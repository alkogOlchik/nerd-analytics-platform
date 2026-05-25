import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.enums import TicketStatus, UserRole
from backend.app.models.ticket import Attachment, Ticket
from backend.app.models.user import Employee
from backend.app.schemas.ticket import AttachmentCreate, TicketCreate, TicketUpdate
from backend.core.kafka.producer import event_producer


def _elapsed_minutes_since(start: datetime) -> float:
    now = datetime.now(UTC)
    if start.tzinfo is None:
        start = start.replace(tzinfo=UTC)
    return (now - start).total_seconds() / 60


def _is_sla_breached(ticket: Ticket) -> bool:
    if ticket.status == TicketStatus.closed.value:
        return False
    elapsed = _elapsed_minutes_since(ticket.date)
    if ticket.sla_ttr_min is not None and elapsed > ticket.sla_ttr_min:
        return True
    if ticket.deadline and datetime.now(UTC) > ticket.deadline:
        return True
    return False


async def _check_sla(ticket: Ticket) -> None:
    if _is_sla_breached(ticket):
        await event_producer.publish(
            "ticket.breached",
            {"ticket_id": str(ticket.id), "deadline": ticket.deadline.isoformat()},
        )


async def create_ticket(
    db: AsyncSession,
    client_id: uuid.UUID,
    data: TicketCreate,
) -> Ticket:
    ticket = Ticket(
        client_id=client_id,
        product=data.product.value,
        priority=data.priority.value,
        date=datetime.now(UTC),
        deadline=data.deadline,
        status=TicketStatus.open.value,
        sla_ttfr_min=data.sla_ttfr_min,
        sla_ttr_min=data.sla_ttr_min,
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)

    await event_producer.publish(
        "ticket.created",
        {
            "ticket_id": str(ticket.id),
            "client_id": str(ticket.client_id),
            "product": ticket.product,
        },
    )
    return ticket


async def list_tickets(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    role: UserRole,
    skip: int,
    limit: int,
    status: str | None = None,
    priority: str | None = None,
    product: str | None = None,
    category: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[Ticket]:
    query = select(Ticket)
    if role == UserRole.client:
        query = query.where(Ticket.client_id == user_id)
    if status:
        query = query.where(Ticket.status == status)
    if priority:
        query = query.where(Ticket.priority == priority)
    if product:
        query = query.where(Ticket.product == product)
    if category:
        query = query.where(
            (Ticket.final_category == category) | (Ticket.ai_suggested_category == category)
        )
    if date_from:
        query = query.where(Ticket.date >= date_from)
    if date_to:
        query = query.where(Ticket.date <= date_to)

    query = query.order_by(Ticket.date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    tickets = list(result.scalars().all())
    for ticket in tickets:
        await _check_sla(ticket)
    return tickets


async def get_ticket(
    db: AsyncSession,
    ticket_id: uuid.UUID,
    user_id: uuid.UUID,
    role: UserRole,
) -> Ticket:
    query = (
        select(Ticket)
        .where(Ticket.id == ticket_id)
        .options(selectinload(Ticket.attachments))
    )
    result = await db.execute(query)
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    if role == UserRole.client and ticket.client_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    await _check_sla(ticket)
    return ticket


async def update_ticket(
    db: AsyncSession,
    ticket_id: uuid.UUID,
    data: TicketUpdate,
    user_id: uuid.UUID,
    role: UserRole,
) -> Ticket:
    ticket = await get_ticket(db, ticket_id, user_id, role)
    if role == UserRole.client:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clients cannot update tickets")

    old_status = ticket.status
    if data.status is not None:
        ticket.status = data.status.value
        if data.status == TicketStatus.closed:
            ticket.closed_at = datetime.now(UTC)
    if data.responsible_id is not None:
        emp = await db.get(Employee, data.responsible_id)
        if not emp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
        ticket.responsible_id = data.responsible_id
    if data.priority is not None:
        ticket.priority = data.priority.value
    if data.final_category is not None:
        ticket.final_category = data.final_category
    if data.is_admin_changed is not None:
        ticket.is_admin_changed = data.is_admin_changed
    if data.sla_ttfr_min is not None:
        ticket.sla_ttfr_min = data.sla_ttfr_min
    if data.sla_ttr_min is not None:
        ticket.sla_ttr_min = data.sla_ttr_min

    await _check_sla(ticket)
    await db.commit()
    await db.refresh(ticket)

    if old_status != TicketStatus.closed.value and ticket.status == TicketStatus.closed.value:
        await event_producer.publish(
            "ticket.closed",
            {
                "ticket_id": str(ticket.id),
                "closed_at": ticket.closed_at.isoformat() if ticket.closed_at else None,
            },
        )
    return ticket


async def reopen_ticket(
    db: AsyncSession,
    ticket_id: uuid.UUID,
    user_id: uuid.UUID,
    role: UserRole,
) -> Ticket:
    ticket = await get_ticket(db, ticket_id, user_id, role)
    if ticket.status != TicketStatus.closed.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticket is not closed")

    ticket.status = TicketStatus.reopened.value
    ticket.reopened_count += 1
    ticket.last_reopened_at = datetime.now(UTC)
    ticket.closed_at = None
    await db.commit()
    await db.refresh(ticket)
    return ticket


async def add_attachment(
    db: AsyncSession,
    ticket_id: uuid.UUID,
    user_id: uuid.UUID,
    role: UserRole,
    data: AttachmentCreate,
) -> Attachment:
    ticket = await get_ticket(db, ticket_id, user_id, role)
    attachment = Attachment(
        ticket_id=ticket.id,
        file_url=data.file_url,
        file_type=data.file_type,
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)
    return attachment
