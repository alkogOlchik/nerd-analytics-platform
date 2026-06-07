import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(..., max_length=128)
    description: str | None = None
    logo_url: str | None = None
    is_active: bool = True


class ProductUpdate(BaseModel):
    name: str | None = Field(None, max_length=128)
    description: str | None = None
    logo_url: str | None = None
    is_active: bool | None = None


class ProductResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    logo_url: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
