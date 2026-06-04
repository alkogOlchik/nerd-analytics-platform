"""AI-сервис: классификация тикетов/отзывов и чат."""

import json
import re
import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.config import get_settings
from backend.app.models.chat import ChatHistory
from backend.app.models.chat_attachment import ChatAttachment
from backend.app.models.enums import ChatRole, ReviewCategory, Sentiment, TicketCategory
from backend.app.models.review import Review
from backend.app.models.ticket import Ticket
from backend.app.schemas.ai import ChatAttachmentInput, ChatRequest, EscalationOffer
from backend.app.services import storage_service
from backend.app.services import escalation_service
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


async def _save_chat_attachments(
    db: AsyncSession,
    *,
    client_id: uuid.UUID,
    user_msg: ChatHistory,
    items: list[ChatAttachmentInput],
) -> list[ChatAttachment]:
    settings = get_settings()
    saved: list[ChatAttachment] = []
    for item in items:
        storage_service.assert_file_url_owned_by_client(settings, client_id, item.file_url)
        row = ChatAttachment(
            chat_history_id=user_msg.id,
            client_id=client_id,
            file_url=item.file_url,
            file_type=item.file_type,
            file_name=item.file_name,
            size_bytes=None,
        )
        db.add(row)
        saved.append(row)
    if saved:
        await db.flush()
        user_msg.attachments.extend(saved)
    return saved


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

    user_text = data.message.strip() or "📎 Вложение"
    ml_text = _message_for_ml(data)

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
    if data.attachments:
        await _save_chat_attachments(
            db,
            client_id=client_id,
            user_msg=user_msg,
            items=data.attachments,
        )

    escalation: EscalationOffer | None = None
    if escalation_service.wants_human_agent(ml_text, data.request_human):
        escalation = await escalation_service.build_escalation_offer(
            db,
            client_id,
            chat_id=chat_id,
            message=ml_text,
            model=data.model,
            ticket=ticket,
        )
        answer = escalation_service.format_escalation_assistant_message(
            escalation, has_ticket=ticket is not None
        )
        ml_response: dict = {
            "answer": answer,
            "model": data.model,
            "escalation": escalation.model_dump(),
        }
    else:
        ml_result = await ml_client.query(ml_text, model=data.model)
        answer = ml_result.answer
        ml_response = ml_result.raw or {"answer": answer, "model": ml_result.model}

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
        .options(selectinload(ChatHistory.attachments))
        .where(ChatHistory.client_id == client_id)
    )
    if chat_id:
        query = query.where(ChatHistory.chat_id == chat_id)
    if ticket_id:
        query = query.where(ChatHistory.ticket_id == ticket_id)
    query = query.order_by(ChatHistory.created_at.asc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())
