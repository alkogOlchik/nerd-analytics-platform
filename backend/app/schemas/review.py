import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.models.enums import TicketProduct
from backend.app.utils.keywords import split_keywords


class ReviewCreate(BaseModel):
    ticket_id: uuid.UUID | None = None
    product: TicketProduct | None = None
    rating: int = Field(ge=1, le=5)
    comment: str | None = None

    @field_validator("ticket_id", mode="before")
    @classmethod
    def empty_ticket_id_to_none(cls, value: object) -> object:
        if value is None or value == "":
            return None
        return value


class ReviewUpdate(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = None
    product: TicketProduct | None = None
    final_category: str | None = None
    is_admin_changed: bool | None = None


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ticket_id: uuid.UUID | None
    client_id: uuid.UUID
    product: str | None
    rating: int
    comment: str | None
    created_at: datetime
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
    def parse_keywords(cls, value):
        if isinstance(value, str):
            return split_keywords(value)
        return value or []
