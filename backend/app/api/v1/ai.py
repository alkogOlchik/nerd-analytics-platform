import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import CurrentUser, get_current_user
from backend.app.db.session import get_db
from backend.app.models.ticket import Ticket
from backend.app.schemas.ai import (
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
    ClassifyReviewRequest,
    ClassifyTicketRequest,
    ReviewClassificationResponse,
    TicketClassificationResponse,
)
from backend.app.schemas.ticket import TicketResponse
from backend.app.services import ai_service

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/classify/ticket", response_model=TicketResponse)
async def classify_ticket(
    data: ClassifyTicketRequest,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
):
    return await ai_service.classify_ticket(db, data.ticket_id, data.text, model=data.model)


@router.post("/classify/review", response_model=ReviewClassificationResponse)
async def classify_review(
    data: ClassifyReviewRequest,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
):
    review = await ai_service.classify_review(db, data.review_id, data.text, model=data.model)
    return ReviewClassificationResponse.model_validate(review)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    data: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    chat_id, user_msg, assistant_msg, ml_response = await ai_service.chat(db, current_user.id, data)
    return ChatResponse(
        chat_id=chat_id,
        user_message=ChatMessageResponse.model_validate(user_msg),
        assistant_message=ChatMessageResponse.model_validate(assistant_msg),
        ml_response=ml_response,
    )


@router.get("/chat/history", response_model=list[ChatMessageResponse])
async def chat_history(
    chat_id: uuid.UUID | None = None,
    ticket_id: uuid.UUID | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    messages = await ai_service.get_chat_history(
        db,
        current_user.id,
        chat_id=chat_id,
        ticket_id=ticket_id,
        skip=skip,
        limit=limit,
    )
    return [ChatMessageResponse.model_validate(m) for m in messages]


@router.get("/classify/ticket/{ticket_id}", response_model=TicketClassificationResponse)
async def get_ticket_classification(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return TicketClassificationResponse.model_validate(ticket)
