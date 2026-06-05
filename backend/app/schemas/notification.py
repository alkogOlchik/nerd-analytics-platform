import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationResponse(BaseModel):
    """Формат для фронта: type = event_type (ticket_update, system, …)."""

    id: uuid.UUID
    type: str
    title: str
    message: str
    is_read: bool
    created_at: datetime
    ticket_id: uuid.UUID | None = None


class NotificationUpdate(BaseModel):
    is_read: bool | None = None


class NotificationReadAllResponse(BaseModel):
    updated: int = Field(description="Сколько уведомлений помечено прочитанными")
