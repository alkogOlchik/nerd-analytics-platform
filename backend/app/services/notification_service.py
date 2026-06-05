import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import AsyncSessionLocal
from backend.app.models.enums import UserRole
from backend.app.models.notification import Notification
from backend.app.models.ticket import Ticket
from backend.app.schemas.notification import NotificationResponse

logger = logging.getLogger(__name__)

_CHANNEL_TO_EVENT = {"email": "ticket_update", "push": "system"}


def notification_to_response(notification: Notification) -> NotificationResponse:
    event_type = notification.event_type or _CHANNEL_TO_EVENT.get(notification.type, "info")
    title = notification.title or _default_title(notification.type, event_type)
    message = notification.message or _default_message(notification)
    return NotificationResponse(
        id=notification.id,
        type=event_type,
        title=title,
        message=message,
        is_read=notification.is_read,
        created_at=notification.created_at,
        ticket_id=notification.ticket_id,
    )


def _default_title(channel: str, event_type: str) -> str:
    if event_type == "system":
        return "Системное уведомление"
    if channel == "push":
        return "Важное уведомление"
    return "Обновление по тикету"


def _default_message(notification: Notification) -> str:
    short_id = str(notification.ticket_id)[:8]
    if notification.event_type == "system" or notification.type == "push":
        return f"Требуется внимание по тикету {short_id}"
    return f"Есть новости по тикету {short_id}"


async def _create_and_send(
    client_id: str,
    ticket_id: str,
    *,
    channel: str = "email",
    event_type: str = "ticket_update",
    title: str | None = None,
    message: str | None = None,
) -> None:
    async with AsyncSessionLocal() as db:
        notification = Notification(
            client_id=uuid.UUID(client_id),
            ticket_id=uuid.UUID(ticket_id),
            type=channel,
            event_type=event_type,
            title=title,
            message=message,
            status="pending",
            is_read=False,
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)

        logger.info(
            "NOTIFICATION [%s/%s] client=%s ticket=%s id=%s",
            channel,
            event_type,
            client_id,
            ticket_id,
            notification.id,
        )
        notification.status = "sent"
        await db.commit()


async def on_ticket_created(payload: dict) -> None:
    ticket_id = payload["ticket_id"]
    await _create_and_send(
        payload["client_id"],
        ticket_id,
        title="Тикет принят",
        message="Ваше обращение зарегистрировано",
    )


async def on_ticket_closed(payload: dict) -> None:
    ticket_id = payload["ticket_id"]
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Ticket).where(Ticket.id == uuid.UUID(ticket_id)))
        ticket = result.scalar_one_or_none()
        if ticket:
            await _create_and_send(
                str(ticket.client_id),
                ticket_id,
                title="Тикет закрыт",
                message="Обращение отмечено как решённое",
            )


async def on_ticket_breached(payload: dict) -> None:
    ticket_id = payload["ticket_id"]
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Ticket).where(Ticket.id == uuid.UUID(ticket_id)))
        ticket = result.scalar_one_or_none()
        if ticket:
            await _create_and_send(
                str(ticket.client_id),
                ticket_id,
                channel="push",
                event_type="system",
                title="Нарушение SLA",
                message="Срок по тикету превышен",
            )


async def list_notifications(
    db: AsyncSession,
    user_id: uuid.UUID,
    role: UserRole,
    skip: int,
    limit: int,
) -> list[NotificationResponse]:
    query = select(Notification)
    if role == UserRole.client:
        query = query.where(Notification.client_id == user_id)
    query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return [notification_to_response(n) for n in result.scalars().all()]


async def get_notification(
    db: AsyncSession,
    notification_id: uuid.UUID,
    user_id: uuid.UUID,
    role: UserRole,
) -> NotificationResponse:
    result = await db.execute(select(Notification).where(Notification.id == notification_id))
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    if role == UserRole.client and notification.client_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return notification_to_response(notification)


async def update_notification(
    db: AsyncSession,
    notification_id: uuid.UUID,
    user_id: uuid.UUID,
    role: UserRole,
    *,
    is_read: bool | None,
) -> NotificationResponse:
    result = await db.execute(select(Notification).where(Notification.id == notification_id))
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    if role == UserRole.client and notification.client_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if is_read is not None:
        notification.is_read = is_read
    await db.commit()
    await db.refresh(notification)
    return notification_to_response(notification)


async def mark_all_read(
    db: AsyncSession,
    user_id: uuid.UUID,
    role: UserRole,
) -> int:
    stmt = update(Notification).values(is_read=True).where(Notification.is_read.is_(False))
    if role == UserRole.client:
        stmt = stmt.where(Notification.client_id == user_id)
    result = await db.execute(stmt)
    await db.commit()
    return int(result.rowcount or 0)
