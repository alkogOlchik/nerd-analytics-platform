import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import CurrentUser, get_current_user, require_employee, require_operator
from backend.app.db.session import get_db
from backend.app.models.enums import TicketPriority, TicketProduct, TicketStatus, UserRole
from backend.app.schemas.ticket import (
    AttachmentCreate,
    AttachmentResponse,
    TicketCreate,
    TicketDetailResponse,
    TicketResponse,
    TicketUpdate,
)
from backend.app.schemas.ticket_extended import (
    ChatHistoryMessageResponse,
    GuestTicketCreate,
    GuestTicketResponse,
    GuestTrackResponse,
    InternalCommentCreate,
    InternalCommentResponse,
    TicketCommentCreate,
    TicketEscalateRequest,
    TicketEscalateResponse,
    TicketPriorityPatch,
    TicketStatusHistoryResponse,
    TicketStatusPatch,
)
from backend.app.services import ticket_service

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("/guest", response_model=GuestTicketResponse, status_code=201)
async def create_guest_ticket(data: GuestTicketCreate, db: AsyncSession = Depends(get_db)):
    return await ticket_service.create_guest_ticket(db, data)


@router.get("/track/{token}", response_model=GuestTrackResponse)
async def track_guest_ticket(token: str, db: AsyncSession = Depends(get_db)):
    return await ticket_service.track_guest_ticket(db, token)


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


@router.post("/{ticket_id}/escalate", response_model=TicketEscalateResponse)
async def escalate_ticket(
    ticket_id: uuid.UUID,
    data: TicketEscalateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    if current_user.role != UserRole.client:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clients only")
    return await ticket_service.escalate_ticket(db, ticket_id, current_user.id, data)


@router.patch("/{ticket_id}/status", response_model=TicketResponse)
async def patch_ticket_status(
    ticket_id: uuid.UUID,
    data: TicketStatusPatch,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_operator),
):
    return await ticket_service.patch_ticket_status(db, ticket_id, current_user.id, data)


@router.patch("/{ticket_id}/priority", response_model=TicketResponse)
async def patch_ticket_priority(
    ticket_id: uuid.UUID,
    data: TicketPriorityPatch,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_operator),
):
    return await ticket_service.patch_ticket_priority(db, ticket_id, data)


@router.get("/{ticket_id}/status-history", response_model=list[TicketStatusHistoryResponse])
async def get_status_history(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    await ticket_service.get_ticket(db, ticket_id, current_user.id, current_user.role)
    return await ticket_service.get_status_history(db, ticket_id)


@router.post("/{ticket_id}/comments", response_model=ChatHistoryMessageResponse, status_code=201)
async def add_ticket_comment(
    ticket_id: uuid.UUID,
    data: TicketCommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    if current_user.role != UserRole.client:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clients only")
    return await ticket_service.add_client_comment(db, ticket_id, current_user.id, data)


@router.post(
    "/{ticket_id}/internal-comments",
    response_model=InternalCommentResponse,
    status_code=201,
)
async def add_internal_comment(
    ticket_id: uuid.UUID,
    data: InternalCommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_operator),
):
    return await ticket_service.add_internal_comment(db, ticket_id, current_user.id, data)


@router.get("/{ticket_id}/internal-comments", response_model=list[InternalCommentResponse])
async def list_internal_comments(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_operator),
):
    return await ticket_service.list_internal_comments(db, ticket_id)


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
