import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.chat import ChatHistory
from backend.app.models.enums import ALLOWED_TICKET_STATUSES, ChatRole, TicketStatus, UserRole
from backend.app.models.internal_comment import InternalComment
from backend.app.models.ticket import Attachment, Ticket
from backend.app.models.ticket_status_history import TicketStatusHistory
from backend.app.models.user import Client, Employee
from backend.app.schemas.ticket import AttachmentCreate, TicketCreate, TicketUpdate
from backend.app.schemas.ticket_extended import (
    GuestTicketCreate,
    GuestTrackResponse,
    GuestTicketResponse,
    InternalCommentCreate,
    TicketCommentCreate,
    TicketEscalateRequest,
    TicketEscalateResponse,
    TicketPriorityPatch,
    TicketStatusPatch,
)
from backend.app.services import ai_service
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


async def _get_or_create_guest_client(db: AsyncSession, email: str) -> Client:
    result = await db.execute(select(Client).where(Client.email == email))
    client = result.scalar_one_or_none()
    if client:
        return client
    local = email.split("@")[0][:40]
    client = Client(
        username=f"guest_{local}_{uuid.uuid4().hex[:8]}",
        email=email,
        password_hash=str(uuid.uuid4()),
    )
    db.add(client)
    await db.flush()
    return client


async def create_ticket(
    db: AsyncSession,
    client_id: uuid.UUID,
    data: TicketCreate,
) -> Ticket:
    now = datetime.now(UTC)
    ticket = Ticket(
        client_id=client_id,
        product=data.product.value,
        priority=data.priority.value,
        user_priority=data.priority.value,
        date=now,
        deadline=data.deadline,
        status=TicketStatus.accepted.value,
        status_updated_at=now,
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


async def create_guest_ticket(db: AsyncSession, data: GuestTicketCreate) -> GuestTicketResponse:
    client = await _get_or_create_guest_client(db, data.guest_email)
    guest_token = str(uuid.uuid4())
    now = datetime.now(UTC)
    ticket = Ticket(
        client_id=client.id,
        product=data.product.value,
        priority=data.priority.value,
        user_priority=data.priority.value,
        guest_email=data.guest_email,
        guest_token=guest_token,
        date=now,
        deadline=now + timedelta(days=7),
        status=TicketStatus.accepted.value,
        status_updated_at=now,
    )
    db.add(ticket)
    await db.flush()

    chat_id = uuid.uuid4()
    db.add(
        ChatHistory(
            chat_id=chat_id,
            ticket_id=ticket.id,
            client_id=client.id,
            role=ChatRole.client.value,
            product=data.product.value,
            resolved_by_ai=False,
            message=data.message,
        )
    )
    await db.commit()
    await db.refresh(ticket)

    await event_producer.publish(
        "ticket.created",
        {
            "ticket_id": str(ticket.id),
            "client_id": str(ticket.client_id),
            "product": ticket.product,
            "guest": True,
        },
    )
    return GuestTicketResponse(
        ticket_id=ticket.id,
        guest_token=guest_token,
        status=ticket.status,
    )


async def track_guest_ticket(db: AsyncSession, token: str) -> GuestTrackResponse:
    result = await db.execute(select(Ticket).where(Ticket.guest_token == token))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return GuestTrackResponse(
        ticket_id=ticket.id,
        status=ticket.status,
        status_updated_at=ticket.status_updated_at,
        product=ticket.product,
        created_at=ticket.date,
    )


async def escalate_ticket(
    db: AsyncSession,
    ticket_id: uuid.UUID,
    client_id: uuid.UUID,
    data: TicketEscalateRequest,
) -> TicketEscalateResponse:
    ticket = await get_ticket(db, ticket_id, client_id, UserRole.client)
    now = datetime.now(UTC)
    if data.user_priority:
        ticket.user_priority = data.user_priority
    ticket.status = TicketStatus.accepted.value
    ticket.status_updated_at = now

    classify_text = data.description or ""
    if data.description:
        chat_id = uuid.uuid4()
        existing = await db.execute(
            select(ChatHistory.chat_id).where(ChatHistory.ticket_id == ticket.id).limit(1)
        )
        row = existing.first()
        if row:
            chat_id = row[0]
        db.add(
            ChatHistory(
                chat_id=chat_id,
                ticket_id=ticket.id,
                client_id=client_id,
                role=ChatRole.client.value,
                product=ticket.product,
                resolved_by_ai=False,
                message=data.description,
            )
        )
    else:
        msg_result = await db.execute(
            select(ChatHistory.message)
            .where(ChatHistory.ticket_id == ticket.id, ChatHistory.role == ChatRole.client.value)
            .order_by(ChatHistory.created_at.desc())
            .limit(1)
        )
        row = msg_result.first()
        if row:
            classify_text = row[0]

    await db.flush()
    if classify_text:
        ticket = await ai_service.classify_ticket(db, ticket.id, classify_text)

    await event_producer.publish(
        "ticket.created",
        {"ticket_id": str(ticket.id), "escalated": True},
    )
    return TicketEscalateResponse(
        ticket_id=ticket.id,
        ai_suggested_category=ticket.ai_suggested_category,
        final_category=ticket.final_category,
        status=ticket.status,
    )


async def patch_ticket_status(
    db: AsyncSession,
    ticket_id: uuid.UUID,
    employee_id: uuid.UUID,
    data: TicketStatusPatch,
) -> Ticket:
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    new_status = data.status.value
    if new_status not in ALLOWED_TICKET_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")

    old_status = ticket.status
    db.add(
        TicketStatusHistory(
            ticket_id=ticket.id,
            status_from=old_status,
            status_to=new_status,
            changed_by=employee_id,
        )
    )
    ticket.status = new_status
    ticket.status_updated_at = datetime.now(UTC)
    if new_status == TicketStatus.closed.value:
        ticket.closed_at = datetime.now(UTC)
    if data.admin_priority:
        ticket.admin_priority = data.admin_priority
    if data.responsible_id:
        emp = await db.get(Employee, data.responsible_id)
        if not emp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
        ticket.responsible_id = data.responsible_id

    await _check_sla(ticket)
    await db.commit()
    await db.refresh(ticket)

    if new_status == TicketStatus.closed.value:
        await event_producer.publish(
            "ticket.closed",
            {
                "ticket_id": str(ticket.id),
                "closed_at": ticket.closed_at.isoformat() if ticket.closed_at else None,
            },
        )
    return ticket


async def patch_ticket_priority(
    db: AsyncSession,
    ticket_id: uuid.UUID,
    data: TicketPriorityPatch,
) -> Ticket:
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    ticket.admin_priority = data.admin_priority
    await db.commit()
    await db.refresh(ticket)
    return ticket


async def get_status_history(db: AsyncSession, ticket_id: uuid.UUID) -> list[TicketStatusHistory]:
    result = await db.execute(
        select(TicketStatusHistory)
        .where(TicketStatusHistory.ticket_id == ticket_id)
        .order_by(TicketStatusHistory.created_at.asc())
    )
    return list(result.scalars().all())


async def add_client_comment(
    db: AsyncSession,
    ticket_id: uuid.UUID,
    client_id: uuid.UUID,
    data: TicketCommentCreate,
) -> ChatHistory:
    ticket = await get_ticket(db, ticket_id, client_id, UserRole.client)
    existing = await db.execute(
        select(ChatHistory.chat_id).where(ChatHistory.ticket_id == ticket.id).limit(1)
    )
    row = existing.first()
    chat_id = row[0] if row else uuid.uuid4()
    message = ChatHistory(
        chat_id=chat_id,
        ticket_id=ticket.id,
        client_id=client_id,
        role=ChatRole.client.value,
        product=ticket.product,
        resolved_by_ai=False,
        message=data.message,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def add_internal_comment(
    db: AsyncSession,
    ticket_id: uuid.UUID,
    employee_id: uuid.UUID,
    data: InternalCommentCreate,
) -> InternalComment:
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    comment = InternalComment(
        ticket_id=ticket_id,
        employee_id=employee_id,
        message=data.message,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment


async def list_internal_comments(db: AsyncSession, ticket_id: uuid.UUID) -> list[InternalComment]:
    result = await db.execute(
        select(InternalComment)
        .where(InternalComment.ticket_id == ticket_id)
        .order_by(InternalComment.created_at.asc())
    )
    return list(result.scalars().all())


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
        ticket.status_updated_at = datetime.now(UTC)
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

    ticket.status = TicketStatus.accepted.value
    ticket.reopened_count += 1
    ticket.last_reopened_at = datetime.now(UTC)
    ticket.closed_at = None
    ticket.status_updated_at = datetime.now(UTC)
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


async def client_resolve_ticket(
    db: AsyncSession,
    ticket_id: uuid.UUID,
    client_id: uuid.UUID,
) -> Ticket:
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    if ticket.client_id != client_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    old_status = ticket.status
    ticket.status = TicketStatus.fixed.value
    ticket.status_updated_at = datetime.now(UTC)
    db.add(TicketStatusHistory(
        ticket_id=ticket.id,
        status_from=old_status,
        status_to=ticket.status,
        changed_by=client_id,
    ))
    await db.commit()
    await db.refresh(ticket)
    return ticket


async def client_escalate_ticket(
    db: AsyncSession,
    ticket_id: uuid.UUID,
    client_id: uuid.UUID,
) -> Ticket:
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    if ticket.client_id != client_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    old_status = ticket.status
    ticket.status = TicketStatus.needs_info.value
    ticket.status_updated_at = datetime.now(UTC)
    db.add(TicketStatusHistory(
        ticket_id=ticket.id,
        status_from=old_status,
        status_to=ticket.status,
        changed_by=client_id,
    ))
    await db.commit()
    await db.refresh(ticket)
    return ticket
