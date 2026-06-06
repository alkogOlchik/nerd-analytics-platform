import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    ticket_id: uuid.UUID
    type: str
    status: str
    is_read: bool
    created_at: datetime


class NotificationUpdate(BaseModel):
    is_read: bool | None = None


class NotificationReadAllResponse(BaseModel):
    updated: int = Field(description="Сколько уведомлений помечено прочитанными")
