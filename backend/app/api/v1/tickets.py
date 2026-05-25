import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import CurrentUser, get_current_user
from backend.app.db.session import get_db
from backend.app.models.enums import TicketPriority, TicketProduct, TicketStatus
from backend.app.schemas.ticket import (
    AttachmentCreate,
    AttachmentResponse,
    TicketCreate,
    TicketDetailResponse,
    TicketResponse,
    TicketUpdate,
)
from backend.app.services import ticket_service

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketResponse, status_code=201)
async def create_ticket(
    data: TicketCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return await ticket_service.create_ticket(db, current_user.id, data)


@router.get("", response_model=list[TicketResponse])
async def list_tickets(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: TicketStatus | None = None,
    priority: TicketPriority | None = None,
    product: TicketProduct | None = None,
    category: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return await ticket_service.list_tickets(
        db,
        user_id=current_user.id,
        role=current_user.role,
        skip=skip,
        limit=limit,
        status=status.value if status else None,
        priority=priority.value if priority else None,
        product=product.value if product else None,
        category=category,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/{ticket_id}", response_model=TicketDetailResponse)
async def get_ticket(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return await ticket_service.get_ticket(db, ticket_id, current_user.id, current_user.role)


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: uuid.UUID,
    data: TicketUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return await ticket_service.update_ticket(
        db, ticket_id, data, current_user.id, current_user.role
    )


@router.post("/{ticket_id}/reopen", response_model=TicketResponse)
async def reopen_ticket(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return await ticket_service.reopen_ticket(db, ticket_id, current_user.id, current_user.role)


@router.post("/{ticket_id}/attachments", response_model=AttachmentResponse, status_code=201)
async def add_attachment(
    ticket_id: uuid.UUID,
    data: AttachmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return await ticket_service.add_attachment(
        db, ticket_id, current_user.id, current_user.role, data
    )
