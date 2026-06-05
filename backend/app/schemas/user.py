import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from backend.app.models.enums import EmployeeRole, Gender, UserRole


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


class EmployeeRegister(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    role: EmployeeRole = EmployeeRole.analyst
    registration_secret: str | None = Field(
        default=None,
        description="Обязателен, если в .env задан ADMIN_REGISTRATION_SECRET",
    )


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    full_name: str
    role: str
    sec_level: int
    status: str
    created_at: datetime


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=128)
    age: int | None = Field(default=None, ge=0, le=150)
    gender: Gender | None = None


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
    age: int | None = None
    gender: str | None = None
    city: str | None = None
