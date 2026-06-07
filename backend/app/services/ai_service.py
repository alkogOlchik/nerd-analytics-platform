"""AI-сервис: классификация тикетов/отзывов и чат."""

import json
import re
import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.chat import ChatHistory
from backend.app.models.chat_file import ChatFile
from backend.app.models.enums import ChatRole, ReviewCategory, Sentiment, TicketCategory
from backend.app.models.review import Review
from backend.app.models.ticket import Ticket
from backend.app.schemas.ai import ChatRequest, EscalationOffer
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
    if data.attachments:
        names = ", ".join(a.file_name or a.file_url for a in data.attachments[:3])
        return f"[Вложения: {names}]"
    return data.message


async def chat(
    db: AsyncSession,
    client_id: uuid.UUID,
    data: ChatRequest,
) -> tuple[uuid.UUID, ChatHistory, ChatHistory, dict, EscalationOffer | None]:
    ticket: Ticket | None = None
    if data.ticket_id:
        ticket_result = await db.execute(select(Ticket).where(Ticket.id == data.ticket_id))
        ticket = ticket_result.scalar_one_or_none()
        if not ticket:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
        if ticket.client_id != client_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    chat_id = data.chat_id or uuid.uuid4()
    product = data.product or (ticket.product if ticket else None)
    category = data.category or (ticket.final_category or ticket.ai_suggested_category if ticket else None)

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
        ticket_id=data.ticket_id,
        role=ChatRole.client.value,
        product=product,
        category=category,
        resolved_by_ai=data.resolved_by_ai,
        message=user_text,
    )
    db.add(user_msg)
    await db.flush()

    escalation: EscalationOffer | None = None
    ml_result = await ml_client.query(ml_text, model=data.model)
    answer = ml_result.answer
    ml_response: dict = ml_result.raw or {"answer": answer, "model": ml_result.model}

    assistant_msg = ChatHistory(
        chat_id=chat_id,
        client_id=client_id,
        ticket_id=data.ticket_id,
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

    return chat_id, user_msg, assistant_msg, ml_response, escalation


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
