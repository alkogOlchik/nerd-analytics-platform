"""Эскалация из чата: детект запроса оператора, подсказки продукта/категории, создание тикета."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.chat import ChatHistory
from backend.app.models.enums import (
    ChatRole,
    TicketCategory,
    TicketPriority,
    TicketProduct,
    TicketStatus,
)
from backend.app.models.ticket import Ticket
from backend.app.schemas.ai import EscalationOffer
from backend.app.schemas.ticket_extended import TicketEscalateResponse
from backend.app.services import ai_service
from backend.core.kafka.producer import event_producer

_ADMIN_INTENT_PHRASES = (
    "позовите",
    "позвать",
    "позови",
    "оператор",
    "админ",
    "администратор",
    "человек",
    "живой",
    "специалист",
    "менеджер",
    "не помог",
    "не помогает",
    "не помогли",
    "не реш",
    "переведите",
    "переведи",
    "свяжите с",
    "хочу поговорить",
    "нужен оператор",
    "вызовите",
)

_PRIORITY_LABELS = {
    TicketPriority.low.value: "Низкий",
    TicketPriority.medium.value: "Средний",
    TicketPriority.high.value: "Высокий",
}


def wants_human_agent(message: str, request_human: bool | None = None) -> bool:
    if request_human:
        return True
    text = message.lower().strip()
    return any(phrase in text for phrase in _ADMIN_INTENT_PHRASES)


def build_escalation_options() -> EscalationOffer:
    return EscalationOffer(
        required=True,
        suggested_product=None,
        suggested_category=None,
        confidence=None,
        products=[p.value for p in TicketProduct],
        categories=[c.value for c in TicketCategory],
        priorities=[p.value for p in TicketPriority],
        priority_labels=dict(_PRIORITY_LABELS),
    )


def format_escalation_assistant_message(offer: EscalationOffer, *, has_ticket: bool) -> str:
    if has_ticket:
        return (
            "Передаю обращение специалисту. Выберите приоритет (низкий, средний или высокий) "
            "и подтвердите эскалацию через API тикета или форму в приложении."
        )
    parts = [
        "Похоже, для решения нужен специалист. ",
    ]
    if offer.suggested_product and offer.suggested_category:
        parts.append(
            f"Рекомендуем: продукт «{offer.suggested_product}», "
            f"категория «{offer.suggested_category}». "
        )
    elif offer.suggested_category:
        parts.append(f"Рекомендуемая категория: «{offer.suggested_category}». ")
    parts.append(
        "Выберите продукт, при необходимости уточните категорию, задайте приоритет "
        "(low / medium / high) и подтвердите создание обращения (POST /ai/chat/escalate)."
    )
    return "".join(parts)


async def collect_chat_text(
    db: AsyncSession,
    client_id: uuid.UUID,
    *,
    chat_id: uuid.UUID | None,
    latest_message: str,
    limit: int = 30,
) -> str:
    parts: list[str] = []
    if latest_message.strip():
        parts.append(latest_message)
    if chat_id:
        result = await db.execute(
            select(ChatHistory.message)
            .where(ChatHistory.client_id == client_id, ChatHistory.chat_id == chat_id)
            .order_by(ChatHistory.created_at.desc())
            .limit(limit)
        )
        for (msg,) in result.all():
            if msg and msg not in parts:
                parts.append(msg)
    return "\n".join(reversed(parts))


async def suggest_product_and_category(text: str, model: str = "gemma4:e2b") -> tuple[str | None, str | None, float | None]:
    """Классификация текста диалога без существующего тикета (через ML)."""
    from backend.app.services.ai_service import _TICKET_CATEGORY_VALUES, _extract_json, _parse_ticket_category
    from backend.app.services.ml_client import ml_client

    product_values = ", ".join(p.value for p in TicketProduct)
    prompt = f"""По переписке клиента поддержки определи продукт и категорию обращения.
Верни ТОЛЬКО JSON без markdown:
{{
  "product": "<одно из: {product_values}>",
  "category": "<одно из: {_TICKET_CATEGORY_VALUES}>",
  "confidence": <0..1>
}}

Переписка:
{text}"""
    ml_result = await ml_client.query(prompt, model=model)
    parsed = _extract_json(ml_result.answer)
    product_raw = parsed.get("product")
    product: str | None = None
    if product_raw:
        for item in TicketProduct:
            if item.value == product_raw or item.name == str(product_raw):
                product = item.value
                break
        if product is None:
            product = str(product_raw)
    category = _parse_ticket_category(parsed.get("category"))
    confidence = parsed.get("confidence")
    try:
        conf = min(max(float(confidence), 0.0), 1.0) if confidence is not None else None
    except (TypeError, ValueError):
        conf = None
    return product, category, conf


async def build_escalation_offer(
    db: AsyncSession,
    client_id: uuid.UUID,
    *,
    chat_id: uuid.UUID | None,
    message: str,
    model: str,
    ticket: Ticket | None,
) -> EscalationOffer:
    offer = build_escalation_options()
    if ticket:
        offer.suggested_product = ticket.product
        offer.suggested_category = ticket.final_category or ticket.ai_suggested_category
        return offer

    text = await collect_chat_text(db, client_id, chat_id=chat_id, latest_message=message)
    product, category, confidence = await suggest_product_and_category(text, model=model)
    offer.suggested_product = product
    offer.suggested_category = category
    offer.confidence = confidence
    return offer


async def confirm_chat_escalation(
    db: AsyncSession,
    client_id: uuid.UUID,
    *,
    chat_id: uuid.UUID,
    product: TicketProduct,
    user_priority: TicketPriority,
    category: str | None,
    description: str | None,
    model: str = "gemma4:e2b",
) -> TicketEscalateResponse:
    hist = await db.execute(
        select(ChatHistory).where(
            ChatHistory.client_id == client_id,
            ChatHistory.chat_id == chat_id,
        )
    )
    messages = list(hist.scalars().all())
    if not messages:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

    existing_ticket_id = next((m.ticket_id for m in messages if m.ticket_id), None)
    if existing_ticket_id:
        from backend.app.schemas.ticket_extended import TicketEscalateRequest
        from backend.app.services import ticket_service

        text = description or await collect_chat_text(
            db, client_id, chat_id=chat_id, latest_message=""
        )
        return await ticket_service.escalate_ticket(
            db,
            existing_ticket_id,
            client_id,
            TicketEscalateRequest(description=text or None, user_priority=user_priority.value),
        )

    now = datetime.now(UTC)
    ticket = Ticket(
        client_id=client_id,
        product=product.value,
        priority=user_priority.value,
        user_priority=user_priority.value,
        date=now,
        deadline=now + timedelta(days=7),
        status=TicketStatus.accepted.value,
        status_updated_at=now,
    )
    if category:
        ticket.ai_suggested_category = category
        ticket.final_category = category
    db.add(ticket)
    await db.flush()

    await db.execute(
        update(ChatHistory)
        .where(ChatHistory.chat_id == chat_id, ChatHistory.client_id == client_id)
        .values(ticket_id=ticket.id, product=product.value)
    )

    classify_text = description or await collect_chat_text(
        db, client_id, chat_id=chat_id, latest_message=""
    )
    if classify_text.strip():
        from backend.app.services import ai_service as ai_svc

        ticket = await ai_svc.classify_ticket(db, ticket.id, classify_text, model=model)
        if category:
            ticket.final_category = category

    await db.commit()
    await db.refresh(ticket)

    await event_producer.publish(
        "ticket.created",
        {"ticket_id": str(ticket.id), "client_id": str(client_id), "from_chat": True},
    )

    return TicketEscalateResponse(
        ticket_id=ticket.id,
        ai_suggested_category=ticket.ai_suggested_category,
        final_category=ticket.final_category,
        status=ticket.status,
    )
