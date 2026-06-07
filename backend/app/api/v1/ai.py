import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import CurrentUser, get_current_user
from backend.app.db.session import get_db
from backend.app.models.chat_file import ChatFile
from backend.app.models.ticket import Ticket
from backend.app.schemas.ai import (
    ChatEscalateRequest,
    ChatFileResponse,
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
from backend.app.schemas.ticket import TicketResponse
from backend.app.schemas.ticket_extended import TicketEscalateResponse
from backend.app.services import ai_service, s3_service

_SUPPORTED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
    "text/markdown",
    "text/x-rst",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "text/csv",
    "application/octet-stream",
}

_EXT_TO_CONTENT_TYPE: dict[str, str] = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".doc": "application/msword",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".rst": "text/x-rst",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls": "application/vnd.ms-excel",
    ".csv": "text/csv",
}

_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

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
    chat_id, ticket_id, ticket_title, ai_needs_escalation, user_msg, assistant_msg, ml_response, escalation = await ai_service.chat(
        db, current_user.id, data
    )
    return ChatResponse(
        chat_id=chat_id,
        ticket_id=ticket_id,
        ticket_title=ticket_title,
        ai_needs_escalation=ai_needs_escalation,
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


@router.post("/files", response_model=list[ChatFileResponse], status_code=status.HTTP_201_CREATED)
async def upload_files(
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    results: list[ChatFile] = []
    for upload in files:
        filename = upload.filename or "file"
        ext = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""
        content_type = upload.content_type or "application/octet-stream"
        if content_type == "application/octet-stream" and ext in _EXT_TO_CONTENT_TYPE:
            content_type = _EXT_TO_CONTENT_TYPE[ext]
        if content_type not in _SUPPORTED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type: {content_type}",
            )
        data = await upload.read()
        if len(data) > _MAX_FILE_SIZE:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large (max 50 MB)")
        s3_key = await s3_service.upload_file(current_user.id, filename, data, content_type)
        cf = ChatFile(
            client_id=current_user.id,
            s3_key=s3_key,
            filename=filename,
            content_type=content_type,
            size_bytes=len(data),
        )
        db.add(cf)
        results.append(cf)
    await db.commit()
    for cf in results:
        await db.refresh(cf)
    return [ChatFileResponse.model_validate(cf) for cf in results]


@router.get("/files/{file_id}", response_model=ChatFileResponse)
async def get_file(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    cf = await db.get(ChatFile, file_id)
    if cf is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    if cf.client_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return ChatFileResponse.model_validate(cf)


@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    cf = await db.get(ChatFile, file_id)
    if cf is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    if cf.client_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    await s3_service.delete_file(cf.s3_key)
    await db.delete(cf)
    await db.commit()
