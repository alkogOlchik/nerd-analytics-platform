"""AI-сервис: классификация тикетов/отзывов и чат."""

import asyncio
import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.chat import ChatHistory
from backend.app.models.chat_file import ChatFile
from backend.app.models.enums import ChatRole, ReviewCategory, Sentiment, TicketCategory
from backend.app.models.review import Review
from backend.app.models.ticket import Ticket
from backend.app.schemas.ai import ChatRequest, ChatSessionResponse, EscalationOffer
from backend.app.services import file_parser, s3_service
from backend.app.services.ml_client import ml_client
from backend.app.utils.keywords import join_keywords

_TICKET_CATEGORY_VALUES = ", ".join(t.value for t in TicketCategory)
_REVIEW_CATEGORY_VALUES = ", ".join(t.value for t in ReviewCategory)

_TICKET_CLASSIFY_PROMPT = """Классифицируй обращение в службу поддержки.
Верни ТОЛЬКО валидный JSON без markdown:
{{
  "category": "<одно из: {types}>",
  "keywords": ["слово1", "слово2"],
  "confidence": <число от 0 до 1>
}}

Текст обращения:
{text}"""

_REVIEW_CLASSIFY_PROMPT = """Классифицируй отзыв клиента.
Верни ТОЛЬКО валидный JSON без markdown:
{{
  "category": "<одно из: {types}>",
  "sentiment": "<positive|neutral|negative>",
  "keywords_positive": ["..."],
  "keywords_neutral": ["..."],
  "keywords_negative": ["..."],
  "confidence": <число от 0 до 1>
}}

Текст отзыва:
{text}"""

_OPERATOR_PHRASES = [
    "переведи на оператора",
    "хочу оператора",
    "позови оператора",
    "человека",
    "живого человека",
]


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


def _parse_ticket_category(raw: str | None) -> str | None:
    if not raw:
        return None
    for item in TicketCategory:
        if item.value == raw or item.name == raw:
            return item.value
    return raw


def _parse_review_category(raw: str | None) -> str | None:
    if not raw:
        return None
    for item in ReviewCategory:
        if item.value == raw or item.name == raw:
            return item.value
    return raw


def _parse_sentiment(raw: str | None) -> str | None:
    if not raw:
        return None
    try:
        return Sentiment(raw).value
    except ValueError:
        return raw


def _parse_keywords(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(v) for v in value]
    return []


async def classify_ticket(
    db: AsyncSession,
    ticket_id: uuid.UUID,
    text: str,
    model: str = "gemma4:e2b",
) -> Ticket:
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    prompt = _TICKET_CLASSIFY_PROMPT.format(types=_TICKET_CATEGORY_VALUES, text=text)
    ml_result = await ml_client.query(prompt, model=model)
    parsed = _extract_json(ml_result.answer)

    category = _parse_ticket_category(parsed.get("category"))
    ticket.ai_suggested_category = category
    ticket.final_category = category
    ticket.keywords = join_keywords(_parse_keywords(parsed.get("keywords")))
    ticket.confidence = min(max(float(parsed.get("confidence", 0.5)), 0.0), 1.0)
    ticket.is_admin_changed = False

    await db.commit()
    await db.refresh(ticket)
    return ticket


async def classify_review(
    db: AsyncSession,
    review_id: uuid.UUID,
    text: str,
    model: str = "gemma4:e2b",
) -> Review:
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    prompt = _REVIEW_CLASSIFY_PROMPT.format(types=_REVIEW_CATEGORY_VALUES, text=text)
    ml_result = await ml_client.query(prompt, model=model)
    parsed = _extract_json(ml_result.answer)

    category = _parse_review_category(parsed.get("category"))
    review.ai_suggested_category = category
    review.final_category = category
    review.sentiment = _parse_sentiment(parsed.get("sentiment"))
    review.keywords_positive = join_keywords(_parse_keywords(parsed.get("keywords_positive")))
    review.keywords_neutral = join_keywords(_parse_keywords(parsed.get("keywords_neutral")))
    review.keywords_negative = join_keywords(_parse_keywords(parsed.get("keywords_negative")))
    review.confidence = min(max(float(parsed.get("confidence", 0.5)), 0.0), 1.0)
    review.is_admin_changed = False

    await db.commit()
    await db.refresh(review)
    return review


def _message_for_ml(data: ChatRequest) -> str:
    text = data.message.strip()
    if text:
        return text
    return data.message


async def chat(
    db: AsyncSession,
    client_id: uuid.UUID,
    data: ChatRequest,
) -> tuple[uuid.UUID, uuid.UUID | None, str | None, str | None, ChatHistory, ChatHistory, dict, EscalationOffer | None]:
    is_first_message = data.chat_id is None
    ticket: Ticket | None = None

    if is_first_message:
        now = datetime.now(tz=timezone.utc)
        deadline = now + timedelta(days=7)
        ticket = Ticket(
            client_id=client_id,
            product=data.product,
            title="Новое обращение",
            status="in_progress",
            priority="medium",
            date=now,
            deadline=deadline,
        )
        db.add(ticket)
        await db.flush()
        effective_ticket_id: uuid.UUID | None = ticket.id
    else:
        if data.ticket_id:
            t_result = await db.execute(select(Ticket).where(Ticket.id == data.ticket_id))
            ticket = t_result.scalar_one_or_none()
            if ticket and ticket.client_id != client_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        else:
            hist_ticket_id = (await db.execute(
                select(ChatHistory.ticket_id)
                .where(
                    ChatHistory.chat_id == data.chat_id,
                    ChatHistory.client_id == client_id,
                    ChatHistory.ticket_id.is_not(None),
                )
                .limit(1)
            )).scalar_one_or_none()
            if hist_ticket_id:
                t_result = await db.execute(select(Ticket).where(Ticket.id == hist_ticket_id))
                ticket = t_result.scalar_one_or_none()
        effective_ticket_id = ticket.id if ticket else data.ticket_id

    chat_id = data.chat_id or uuid.uuid4()
    product = data.product or (ticket.product if ticket else None)
    category = data.category or (ticket.final_category or ticket.ai_suggested_category if ticket else None)

    # Detect operator request
    user_text_lower = (data.message or "").lower()
    wants_operator = bool(data.request_human) or any(p in user_text_lower for p in _OPERATOR_PHRASES)
    if wants_operator and ticket and ticket.status != "closed":
        ticket.status = "waiting_for_operator"

    # Build file context
    context_parts: list[str] = []
    if data.file_ids:
        for file_id in data.file_ids:
            cf = await db.get(ChatFile, file_id)
            if cf is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"File {file_id} not found")
            if cf.client_id != client_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
            raw = await s3_service.download_file(cf.s3_key)
            try:
                text = file_parser.parse_to_text(raw, cf.filename)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
            context_parts.append(f"=== {cf.filename} ===\n{text}")

    _HISTORY_FILE_CHARS = 3_000
    stored_parts: list[str] = []
    for part in context_parts:
        stored_parts.append(part[:_HISTORY_FILE_CHARS] + ("…" if len(part) > _HISTORY_FILE_CHARS else ""))
    raw_text = data.message.strip()
    user_text = "\n\n".join(stored_parts + ([raw_text] if raw_text else [])).strip() or "📎 Вложение"

    # Load history for existing chats
    history_parts: list[str] = []
    if data.chat_id:
        history_rows = (
            await db.execute(
                select(ChatHistory)
                .where(ChatHistory.chat_id == data.chat_id)
                .order_by(ChatHistory.created_at.asc())
                .limit(20)
            )
        ).scalars().all()
        for row in history_rows:
            role_label = "Пользователь" if row.role == ChatRole.client.value else "Ассистент"
            history_parts.append(f"{role_label}: {row.message}")

    current_query = "\n\n".join(context_parts + [data.message]) if context_parts else _message_for_ml(data)

    prefix_parts: list[str] = []
    if product:
        prefix_parts.append(f"Продукт: {product}")
    if category:
        prefix_parts.append(f"Категория: {category}")
    prefix = ("\n".join(prefix_parts) + "\n\n") if prefix_parts else ""

    if history_parts:
        ml_text = prefix + "История диалога:\n" + "\n".join(history_parts) + "\n\nТекущий вопрос:\n" + current_query
    else:
        ml_text = prefix + current_query

    user_msg = ChatHistory(
        chat_id=chat_id,
        client_id=client_id,
        ticket_id=effective_ticket_id,
        role=ChatRole.client.value,
        product=product,
        category=category,
        resolved_by_ai=data.resolved_by_ai,
        message=user_text,
    )
    db.add(user_msg)
    await db.flush()

    escalation: EscalationOffer | None = None

    if is_first_message and data.message.strip():
        title_prompt = (
            f"Придумай краткое название для обращения (5-7 слов, только текст, без кавычек): "
            f"{data.message.strip()[:500]}"
        )
        ml_result, title_result = await asyncio.gather(
            ml_client.query(ml_text, model=data.model),
            ml_client.query(title_prompt, model=data.model),
        )
        if ticket and title_result.answer.strip():
            ticket.title = title_result.answer.strip()[:100]
    else:
        ml_result = await ml_client.query(ml_text, model=data.model)

    answer = ml_result.answer
    ml_response: dict = ml_result.raw or {"answer": answer, "model": ml_result.model}

    if (
        ml_result.raw
        and ml_result.raw.get("escalate_to_operator")
        and ticket
        and ticket.status not in ("closed", "waiting_for_operator")
    ):
        ticket.status = "waiting_for_operator"

    assistant_msg = ChatHistory(
        chat_id=chat_id,
        client_id=client_id,
        ticket_id=effective_ticket_id,
        role=ChatRole.ai.value,
        product=product or (escalation.suggested_product if escalation else None),
        category=category or (escalation.suggested_category if escalation else None),
        resolved_by_ai=False if escalation else data.resolved_by_ai,
        message=answer,
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(user_msg)
    await db.refresh(assistant_msg)

    ticket_status = ticket.status if ticket else None
    ticket_title = ticket.title if ticket else None

    return chat_id, effective_ticket_id, ticket_status, ticket_title, user_msg, assistant_msg, ml_response, escalation


async def get_chat_sessions(
    db: AsyncSession,
    client_id: uuid.UUID,
) -> list[ChatSessionResponse]:
    session_rows = (await db.execute(
        select(
            ChatHistory.chat_id,
            func.min(ChatHistory.created_at).label("created_at"),
            func.max(ChatHistory.created_at).label("updated_at"),
        )
        .where(ChatHistory.client_id == client_id)
        .group_by(ChatHistory.chat_id)
        .order_by(func.max(ChatHistory.created_at).desc())
    )).all()

    if not session_rows:
        return []

    chat_ids = [row.chat_id for row in session_rows]

    # One ticket_id per chat (first occurrence)
    ticket_id_rows = (await db.execute(
        select(ChatHistory.chat_id, ChatHistory.ticket_id)
        .where(
            ChatHistory.client_id == client_id,
            ChatHistory.ticket_id.is_not(None),
            ChatHistory.chat_id.in_(chat_ids),
        )
    )).all()

    ticket_by_chat: dict[uuid.UUID, uuid.UUID] = {}
    for row in ticket_id_rows:
        if row.chat_id not in ticket_by_chat:
            ticket_by_chat[row.chat_id] = row.ticket_id

    tickets_map: dict[uuid.UUID, Ticket] = {}
    ticket_ids = list(ticket_by_chat.values())
    if ticket_ids:
        tickets = (await db.execute(
            select(Ticket).where(Ticket.id.in_(ticket_ids))
        )).scalars().all()
        tickets_map = {t.id: t for t in tickets}

    # Last assistant message per chat via window function
    rn_col = func.row_number().over(
        partition_by=ChatHistory.chat_id,
        order_by=ChatHistory.created_at.desc(),
    ).label("rn")
    inner = (
        select(ChatHistory.chat_id, ChatHistory.message, rn_col)
        .where(
            ChatHistory.client_id == client_id,
            ChatHistory.role == ChatRole.ai.value,
            ChatHistory.chat_id.in_(chat_ids),
        )
    ).subquery()
    last_msg_rows = (await db.execute(
        select(inner.c.chat_id, inner.c.message).where(inner.c.rn == 1)
    )).all()
    last_msg_by_chat: dict[uuid.UUID, str] = {row.chat_id: row.message for row in last_msg_rows}

    sessions: list[ChatSessionResponse] = []
    for row in session_rows:
        cid = row.chat_id
        ticket_id = ticket_by_chat.get(cid)
        ticket = tickets_map.get(ticket_id) if ticket_id else None
        sessions.append(ChatSessionResponse(
            id=cid,
            title=(ticket.title if ticket and ticket.title else None) or "Новое обращение",
            ticket_id=ticket_id,
            ticket_status=ticket.status if ticket else None,
            created_at=row.created_at,
            updated_at=row.updated_at,
            last_message=last_msg_by_chat.get(cid),
        ))

    return sessions


async def resolve_chat(
    db: AsyncSession,
    client_id: uuid.UUID,
    chat_id: uuid.UUID,
) -> tuple[uuid.UUID, str]:
    ticket_id_val = (await db.execute(
        select(ChatHistory.ticket_id)
        .where(
            ChatHistory.chat_id == chat_id,
            ChatHistory.client_id == client_id,
            ChatHistory.ticket_id.is_not(None),
        )
        .limit(1)
    )).scalar_one_or_none()

    if not ticket_id_val:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat or ticket not found")

    ticket = (await db.execute(select(Ticket).where(Ticket.id == ticket_id_val))).scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    if ticket.client_id != client_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    ticket.status = "closed"
    ticket.closed_at = datetime.now(tz=timezone.utc)
    await db.commit()
    return ticket.id, ticket.status


async def request_operator_chat(
    db: AsyncSession,
    client_id: uuid.UUID,
    chat_id: uuid.UUID,
) -> tuple[uuid.UUID, str]:
    ticket_id_val = (await db.execute(
        select(ChatHistory.ticket_id)
        .where(
            ChatHistory.chat_id == chat_id,
            ChatHistory.client_id == client_id,
            ChatHistory.ticket_id.is_not(None),
        )
        .limit(1)
    )).scalar_one_or_none()

    if not ticket_id_val:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat or ticket not found")

    ticket = (await db.execute(select(Ticket).where(Ticket.id == ticket_id_val))).scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    if ticket.client_id != client_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    ticket.status = "waiting_for_operator"
    await db.commit()
    return ticket.id, ticket.status


async def get_chat_history(
    db: AsyncSession,
    client_id: uuid.UUID,
    *,
    chat_id: uuid.UUID | None = None,
    ticket_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[ChatHistory]:
    query = (
        select(ChatHistory)
        .where(ChatHistory.client_id == client_id)
    )
    if chat_id:
        query = query.where(ChatHistory.chat_id == chat_id)
    if ticket_id:
        query = query.where(ChatHistory.ticket_id == ticket_id)
    query = query.order_by(ChatHistory.created_at.asc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())
