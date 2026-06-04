import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from backend.app.models.enums import Gender, UserRole


class ClientRegister(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    full_name: str | None = None
    age: int | None = Field(default=None, ge=0, le=150)
    gender: Gender | None = None
    city: str | None = None


class ClientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    email: str
    full_name: str | None
    age: int | None
    gender: str | None
    city: str | None
    created_at: datetime


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    full_name: str
    sec_level: int
    status: str
    created_at: datetime


class UserMeResponse(BaseModel):
    id: uuid.UUID
    username: str
    role: UserRole
    employee_role: str | None = Field(
        default=None,
        description="Роль сотрудника: analyst — доступ к /analytics",
    )
    email: str | None = None
    full_name: str | None = None
