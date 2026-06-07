import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SlaRuleCreate(BaseModel):
    product_id: uuid.UUID | None = None
    priority: str = Field(..., pattern="^(low|medium|high)$")
    ttfr_limit_minutes: int = Field(..., gt=0)
    ttr_limit_minutes: int = Field(..., gt=0)


class SlaRuleUpdate(BaseModel):
    ttfr_limit_minutes: int | None = Field(None, gt=0)
    ttr_limit_minutes: int | None = Field(None, gt=0)


class SlaRuleResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID | None
    priority: str
    ttfr_limit_minutes: int
    ttr_limit_minutes: int
    created_at: datetime

    model_config = {"from_attributes": True}
