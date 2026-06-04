from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AdminLoginResponse(TokenResponse):
    """Токены + роль сотрудника (для входа в аналитику / админку)."""

    role: str = "employee"
    employee_role: str | None = None
    username: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class NotificationPreferencesUpdate(BaseModel):
    notify_email: bool | None = None
    notify_push: bool | None = None


class NotificationPreferencesResponse(BaseModel):
    notify_email: bool
    notify_push: bool


class AccountDeletionResponse(BaseModel):
    message: str


class OAuthCodeRequest(BaseModel):
    code: str
