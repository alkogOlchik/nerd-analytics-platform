import uuid
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.models.enums import EmployeeRole, UserRole
from backend.app.models.user import Employee
from backend.app.services import auth_service

security = HTTPBearer()

_ANALYST_ROLES = {
    EmployeeRole.analyst.value,
    EmployeeRole.product_owner.value,
    EmployeeRole.super_admin.value,
}
_OPERATOR_ROLES = {
    EmployeeRole.operator.value,
    EmployeeRole.product_owner.value,
    EmployeeRole.super_admin.value,
}
_OWNER_ROLES = {EmployeeRole.product_owner.value, EmployeeRole.super_admin.value}


@dataclass
class CurrentUser:
    id: uuid.UUID
    username: str
    role: UserRole
    email: str | None = None
    full_name: str | None = None
    employee_role: str | None = None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    payload = auth_service.decode_token(credentials.credentials, expected_type="access")
    user_id = uuid.UUID(payload["sub"])
    role = UserRole(payload["role"])
    user = await auth_service.get_user_by_id(db, user_id, role)

    employee_role: str | None = None
    if role == UserRole.employee:
        employee_role = getattr(user, "role", EmployeeRole.operator.value)

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
        employee_role=employee_role,
    )


async def require_employee(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if current_user.role != UserRole.employee:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Employees only")
    return current_user


def _check_employee_role(current_user: CurrentUser, allowed: set[str]) -> None:
    role = current_user.employee_role or EmployeeRole.operator.value
    if role not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")


async def require_analyst(current_user: CurrentUser = Depends(require_employee)) -> CurrentUser:
    _check_employee_role(current_user, _ANALYST_ROLES)
    return current_user


async def require_operator(current_user: CurrentUser = Depends(require_employee)) -> CurrentUser:
    _check_employee_role(current_user, _OPERATOR_ROLES)
    return current_user


async def require_owner(current_user: CurrentUser = Depends(require_employee)) -> CurrentUser:
    _check_employee_role(current_user, _OWNER_ROLES)
    return current_user


async def require_super_admin(current_user: CurrentUser = Depends(require_employee)) -> CurrentUser:
    if current_user.employee_role != EmployeeRole.super_admin.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super admin only")
    return current_user
