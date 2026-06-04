import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import CurrentUser, get_current_user
from backend.app.db.session import get_db
from backend.app.models.ticket import Ticket
from backend.app.schemas.ai import (
    ChatEscalateRequest,
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
    ClassifyReviewRequest,
    ClassifyTicketRequest,
    EscalationOffer,
    FileUploadResponse,
    ReviewClassificationResponse,
    TicketClassificationResponse,
)
from backend.app.services import storage_service
from backend.app.schemas.ticket import TicketResponse
from backend.app.schemas.ticket_extended import TicketEscalateResponse
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


@router.post("/chat/attachments", response_model=FileUploadResponse, status_code=201)
async def upload_chat_attachment(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Загрузить фото или PDF в S3/MinIO (или локально). Вернувшийся file_url передать в POST /ai/chat."""
    content = await file.read()
    stored = storage_service.upload_bytes(
        client_id=current_user.id,
        filename=file.filename or "file",
        content=content,
        content_type=file.content_type,
    )
    return FileUploadResponse(
        file_url=stored.file_url,
        file_type=stored.file_type,
        file_name=stored.file_name,
        size_bytes=stored.size_bytes,
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    data: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    chat_id, user_msg, assistant_msg, ml_response, escalation = await ai_service.chat(
        db, current_user.id, data
    )
    return ChatResponse(
        chat_id=chat_id,
        user_message=ChatMessageResponse.model_validate(user_msg),
        assistant_message=ChatMessageResponse.model_validate(assistant_msg),
        ml_response=ml_response,
        escalation=escalation,
    )


@router.get("/escalation/options", response_model=EscalationOffer)
async def escalation_options(_: CurrentUser = Depends(get_current_user)):
    """Справочник продуктов, категорий и приоритетов для формы эскалации."""
    from backend.app.services import escalation_service

    return escalation_service.build_escalation_options()


@router.post("/chat/escalate", response_model=TicketEscalateResponse, status_code=201)
async def chat_escalate(
    data: ChatEscalateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Создать тикет из чата после выбора продукта, категории и приоритета."""
    from backend.app.services import escalation_service

    return await escalation_service.confirm_chat_escalation(
        db,
        current_user.id,
        chat_id=data.chat_id,
        product=data.product,
        user_priority=data.user_priority,
        category=data.category,
        description=data.description,
        model=data.model,
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
