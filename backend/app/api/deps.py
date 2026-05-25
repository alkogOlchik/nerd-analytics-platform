import uuid
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.models.enums import UserRole
from backend.app.services import auth_service

security = HTTPBearer()


@dataclass
class CurrentUser:
    id: uuid.UUID
    username: str
    role: UserRole
    email: str | None = None
    full_name: str | None = None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    payload = auth_service.decode_token(credentials.credentials, expected_type="access")
    user_id = uuid.UUID(payload["sub"])
    role = UserRole(payload["role"])
    user = await auth_service.get_user_by_id(db, user_id, role)

    if role == UserRole.client:
        return CurrentUser(
            id=user.id,
            username=user.username,
            role=role,
            email=user.email,
            full_name=user.full_name,
        )
    return CurrentUser(
        id=user.id,
        username=user.username,
        role=role,
        full_name=user.full_name,
    )


async def require_employee(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if current_user.role != UserRole.employee:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Employees only")
    return current_user
