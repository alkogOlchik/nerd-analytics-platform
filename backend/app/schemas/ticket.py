import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.models.enums import TicketPriority, TicketProduct, TicketStatus
from backend.app.utils.keywords import split_keywords


class TicketCreate(BaseModel):
    product: TicketProduct
    priority: TicketPriority = TicketPriority.medium
    deadline: datetime
    sla_ttfr_min: int | None = Field(default=None, ge=1, description="SLA: минут до первого ответа")
    sla_ttr_min: int | None = Field(default=None, ge=1, description="SLA: минут до полного решения")


class TicketUpdate(BaseModel):
    status: TicketStatus | None = None
    responsible_id: uuid.UUID | None = None
    priority: TicketPriority | None = None
    final_category: str | None = None
    is_admin_changed: bool | None = None
    sla_ttfr_min: int | None = Field(default=None, ge=1)
    sla_ttr_min: int | None = Field(default=None, ge=1)


class AttachmentCreate(BaseModel):
    file_url: str = Field(min_length=1, max_length=1024)
    file_type: str | None = Field(default=None, max_length=64)


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    file_url: str
    file_type: str | None
    created_at: datetime


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    responsible_id: uuid.UUID | None
    title: str | None = None
    product: str | None = None
    status: str
    priority: str
    user_priority: str | None = None
    admin_priority: str | None = None
    guest_email: str | None = None
    status_updated_at: datetime | None = None
    date: datetime
    deadline: datetime
    closed_at: datetime | None
    reopened_count: int
    last_reopened_at: datetime | None
    ai_suggested_category: str | None
    final_category: str | None
    is_admin_changed: bool
    keywords: list[str] = []
    confidence: float | None
    sla_ttfr_min: int | None
    sla_ttr_min: int | None

    @field_validator("keywords", mode="before")
    @classmethod
    def parse_keywords(cls, value):
        if isinstance(value, str):
            return split_keywords(value)
        return value or []


class TicketDetailResponse(TicketResponse):
    attachments: list[AttachmentResponse] = []
