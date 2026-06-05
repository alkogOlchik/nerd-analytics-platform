from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import CurrentUser, get_current_user, get_optional_current_user
from backend.app.db.session import get_db
from backend.app.models.enums import UserRole
from backend.app.schemas.auth import (
    AccountDeletionResponse,
    AdminLoginResponse,
    ChangePasswordRequest,
    LoginRequest,
    LogoutRequest,
    NotificationPreferencesResponse,
    NotificationPreferencesUpdate,
    OAuthCodeRequest,
    RefreshRequest,
    TokenResponse,
)
from backend.app.schemas.user import (
    ClientRegister,
    ClientResponse,
    EmployeeRegister,
    EmployeeResponse,
    ProfileUpdate,
    UserMeResponse,
)
from backend.app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=ClientResponse, status_code=201)
async def register(data: ClientRegister, db: AsyncSession = Depends(get_db)):
    return await auth_service.register_client(db, data)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.login(db, data.username, data.password)


@router.post("/admin/register", response_model=EmployeeResponse, status_code=201)
async def admin_register(
    data: EmployeeRegister,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser | None = Depends(get_optional_current_user),
):
    """
    Регистрация сотрудника (employees).

    Разрешено если: (1) в БД ещё нет сотрудников — bootstrap, (2) токен super_admin,
    (3) в body верный registration_secret (= ADMIN_REGISTRATION_SECRET в .env).
    """
    return await auth_service.register_employee(
        db,
        data,
        actor_role=current_user.role if current_user else None,
        actor_employee_role=current_user.employee_role if current_user else None,
    )


@router.post("/admin/login", response_model=AdminLoginResponse)
async def admin_login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Вход сотрудника (employees). Клиентский аккаунт с тем же username не подойдёт."""
    return await auth_service.login_employee(db, data.username, data.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest):
    return await auth_service.refresh_tokens(data.refresh_token)


@router.post("/logout", status_code=204)
async def logout(data: LogoutRequest):
    await auth_service.logout(data.refresh_token)
    return None


@router.get("/me", response_model=UserMeResponse)
async def me(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    user = await auth_service.get_user_by_id(db, current_user.id, current_user.role)
    return auth_service.build_user_me(user, current_user.role)


@router.patch("/me", response_model=UserMeResponse)
async def update_me(
    data: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return await auth_service.update_profile(db, current_user.id, current_user.role, data)


@router.post("/change-password", status_code=200)
async def change_password(
    data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    await auth_service.change_password(
        db,
        current_user.id,
        current_user.role,
        current_password=data.current_password,
        new_password=data.new_password,
    )
    return {"message": "Password changed"}


@router.delete("/me", response_model=AccountDeletionResponse)
async def delete_me(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    if current_user.role != UserRole.client:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clients only")
    message = await auth_service.request_account_deletion(db, current_user.id)
    return AccountDeletionResponse(message=message)


@router.patch("/me/notifications", response_model=NotificationPreferencesResponse)
async def update_notifications(
    data: NotificationPreferencesUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    if current_user.role != UserRole.client:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clients only")
    return await auth_service.update_notification_preferences(
        db,
        current_user.id,
        notify_email=data.notify_email,
        notify_push=data.notify_push,
    )


@router.post("/oauth/{provider}", response_model=TokenResponse)
async def oauth_login(provider: str, data: OAuthCodeRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.oauth_login(db, provider, data.code)
