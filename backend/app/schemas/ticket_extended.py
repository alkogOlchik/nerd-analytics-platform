import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from backend.app.models.enums import TicketPriority, TicketProduct, TicketStatus


class GuestTicketCreate(BaseModel):
    product: TicketProduct
    priority: TicketPriority
    message: str = Field(min_length=1)
    guest_email: EmailStr


class GuestTicketResponse(BaseModel):
    ticket_id: uuid.UUID
    guest_token: str
    status: str


class GuestTrackResponse(BaseModel):
    ticket_id: uuid.UUID
    status: str
    status_updated_at: datetime | None
    product: str
    created_at: datetime


class TicketEscalateRequest(BaseModel):
    description: str | None = None
    user_priority: str | None = None


class TicketEscalateResponse(BaseModel):
    ticket_id: uuid.UUID
    ai_suggested_category: str | None
    final_category: str | None
    status: str


class TicketStatusPatch(BaseModel):
    status: TicketStatus
    admin_priority: str | None = None
    responsible_id: uuid.UUID | None = None


class TicketPriorityPatch(BaseModel):
    admin_priority: str


class TicketStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ticket_id: uuid.UUID | None
    status_from: str | None
    status_to: str | None
    changed_by: uuid.UUID | None
    created_at: datetime


class TicketCommentCreate(BaseModel):
    message: str = Field(min_length=1)


class InternalCommentCreate(BaseModel):
    message: str = Field(min_length=1)


class InternalCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ticket_id: uuid.UUID | None
    employee_id: uuid.UUID | None
    message: str
    created_at: datetime


class ChatHistoryMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    chat_id: uuid.UUID
    ticket_id: uuid.UUID | None
    client_id: uuid.UUID
    role: str
    message: str
    resolved_by_ai: bool
    created_at: datetime
