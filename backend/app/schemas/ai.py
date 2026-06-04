import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.models.enums import ChatRole
from backend.app.utils.keywords import split_keywords


class ClassifyTicketRequest(BaseModel):
    ticket_id: uuid.UUID
    text: str = Field(min_length=1)
    model: str = "gemma4:e2b"


class ClassifyReviewRequest(BaseModel):
    review_id: uuid.UUID
    text: str = Field(min_length=1)
    model: str = "gemma4:e2b"


class ChatFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    content_type: str
    size_bytes: int
    created_at: datetime


class ChatRequest(BaseModel):
    """Первое сообщение: только message (+ model). chat_id создаётся в ответе."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "message": "Привет! Ответь одним словом: ок",
                    "model": "gemma4:e2b",
                }
            ]
        }
    )

    message: str = Field(min_length=1)
    model: str = "gemma4:e2b"
    chat_id: uuid.UUID | None = Field(
        default=None,
        description="Только для 2+ сообщения — uuid из прошлого ответа. Первый раз не указывать.",
    )
    ticket_id: uuid.UUID | None = Field(
        default=None,
        description="Опционально: привязка к тикету. Первый раз не указывать.",
    )
    file_ids: list[uuid.UUID] | None = None
    product: str | None = None
    category: str | None = None
    resolved_by_ai: bool = False

    @field_validator("ticket_id", "chat_id", mode="before")
    @classmethod
    def empty_uuid_to_none(cls, value: object) -> object:
        if value is None or value == "":
            return None
        return value


class TicketClassificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ai_suggested_category: str | None
    final_category: str | None
    is_admin_changed: bool
    keywords: list[str] = []
    confidence: float | None

    @field_validator("keywords", mode="before")
    @classmethod
    def parse_keywords(cls, value):
        if isinstance(value, str):
            return split_keywords(value)
        return value or []


class ReviewClassificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ai_suggested_category: str | None
    final_category: str | None
    is_admin_changed: bool
    sentiment: str | None
    keywords_positive: list[str] = []
    keywords_neutral: list[str] = []
    keywords_negative: list[str] = []
    confidence: float | None

    @field_validator("keywords_positive", "keywords_neutral", "keywords_negative", mode="before")
    @classmethod
    def parse_keyword_fields(cls, value):
        if isinstance(value, str):
            return split_keywords(value)
        return value or []


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    chat_id: uuid.UUID
    ticket_id: uuid.UUID | None
    role: ChatRole
    product: str | None
    category: str | None
    resolved_by_ai: bool
    message: str
    created_at: datetime


class ChatResponse(BaseModel):
    chat_id: uuid.UUID
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse
    ml_response: dict
