import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import AsyncSessionLocal
from backend.app.models.enums import UserRole
from backend.app.models.notification import Notification
from backend.app.models.ticket import Ticket

logger = logging.getLogger(__name__)


async def _create_and_send(
    client_id: str,
    ticket_id: str,
    notification_type: str = "email",
) -> None:
    async with AsyncSessionLocal() as db:
        notification = Notification(
            client_id=uuid.UUID(client_id),
            ticket_id=uuid.UUID(ticket_id),
            type=notification_type,
            status="pending",
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)

        logger.info(
            "NOTIFICATION [%s] client=%s ticket=%s id=%s",
            notification_type,
            client_id,
            ticket_id,
            notification.id,
        )
        notification.status = "sent"
        await db.commit()


async def on_ticket_created(payload: dict) -> None:
    await _create_and_send(payload["client_id"], payload["ticket_id"])


async def on_ticket_closed(payload: dict) -> None:
    ticket_id = payload["ticket_id"]
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Ticket).where(Ticket.id == uuid.UUID(ticket_id)))
        ticket = result.scalar_one_or_none()
        if ticket:
            await _create_and_send(str(ticket.client_id), ticket_id)


async def on_ticket_breached(payload: dict) -> None:
    ticket_id = payload["ticket_id"]
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Ticket).where(Ticket.id == uuid.UUID(ticket_id)))
        ticket = result.scalar_one_or_none()
        if ticket:
            await _create_and_send(str(ticket.client_id), ticket_id, "push")


async def list_notifications(
    db: AsyncSession,
    user_id: uuid.UUID,
    role: UserRole,
    skip: int,
    limit: int,
) -> list[Notification]:
    query = select(Notification)
    if role == UserRole.client:
        query = query.where(Notification.client_id == user_id)
    query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_notification(
    db: AsyncSession,
    notification_id: uuid.UUID,
    user_id: uuid.UUID,
    role: UserRole,
) -> Notification:
    result = await db.execute(select(Notification).where(Notification.id == notification_id))
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    if role == UserRole.client and notification.client_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return notification
