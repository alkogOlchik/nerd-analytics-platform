import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import httpx
from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.models.enums import EmployeeRole, UserRole
from backend.app.models.user import Client, Employee
from backend.app.schemas.auth import AdminLoginResponse, NotificationPreferencesResponse, TokenResponse
from backend.app.schemas.user import ClientRegister, EmployeeRegister, ProfileUpdate, UserMeResponse

settings = get_settings()
ALGORITHM = "HS256"
_revoked_refresh_tokens: set[str] = set()


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def _create_token(subject: str, role: UserRole, token_type: str, expires_delta: timedelta) -> str:
    expire = datetime.now(UTC) + expires_delta
    payload = {
        "sub": subject,
        "role": role.value,
        "type": token_type,
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_tokens(user_id: uuid.UUID, role: UserRole) -> TokenResponse:
    access = _create_token(
        str(user_id),
        role,
        "access",
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh = _create_token(
        str(user_id),
        role,
        "refresh",
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    return TokenResponse(access_token=access, refresh_token=refresh)


def decode_token(token: str, expected_type: str = "access") -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    if payload.get("type") != expected_type:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    return payload


async def register_client(db: AsyncSession, data: ClientRegister) -> Client:
    by_username = await db.execute(select(Client).where(Client.username == data.username))
    if by_username.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")

    by_email = await db.execute(select(Client).where(Client.email == data.email))
    if by_email.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    client = Client(
        username=data.username,
        email=data.email,
        full_name=data.full_name,
        age=data.age,
        gender=data.gender.value if data.gender else None,
        city=data.city,
        password_hash=hash_password(data.password),
    )
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client


async def login(db: AsyncSession, username: str, password: str) -> TokenResponse:
    result = await db.execute(select(Client).where(Client.username == username))
    client = result.scalar_one_or_none()
    if client and verify_password(password, client.password_hash):
        return create_tokens(client.id, UserRole.client)

    result = await db.execute(select(Employee).where(Employee.username == username))
    employee = result.scalar_one_or_none()
    if employee and employee.status == "active" and verify_password(password, employee.password_hash):
        return create_tokens(employee.id, UserRole.employee)

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


async def register_employee(
    db: AsyncSession,
    data: EmployeeRegister,
    *,
    actor_role: UserRole | None = None,
    actor_employee_role: str | None = None,
) -> Employee:
    employee_count = await db.scalar(select(func.count()).select_from(Employee)) or 0

    existing = await db.execute(select(Employee).where(Employee.username == data.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

    role = EmployeeRole.super_admin.value if employee_count == 0 else data.role.value
    employee = Employee(
        username=data.username,
        full_name=data.full_name,
        password_hash=hash_password(data.password),
        status="active",
        role=role,
        sec_level=1,
    )
    db.add(employee)
    await db.commit()
    await db.refresh(employee)
    return employee


def build_user_me(user: Client | Employee, role: UserRole) -> UserMeResponse:
    if role == UserRole.employee:
        return UserMeResponse(
            id=user.id,
            username=user.username,
            role=role,
            employee_role=getattr(user, "role", None),
            full_name=user.full_name,
        )
    return UserMeResponse(
        id=user.id,
        username=user.username,
        role=role,
        email=user.email,
        full_name=user.full_name,
        age=user.age,
        gender=user.gender,
        city=user.city,
    )


async def update_profile(
    db: AsyncSession,
    user_id: uuid.UUID,
    role: UserRole,
    data: ProfileUpdate,
) -> UserMeResponse:
    user = await get_user_by_id(db, user_id, role)
    if data.full_name is not None:
        user.full_name = data.full_name
    if role == UserRole.client:
        if data.city is not None:
            user.city = data.city
        if data.age is not None:
            user.age = data.age
        if data.gender is not None:
            user.gender = data.gender.value
    await db.commit()
    await db.refresh(user)
    return build_user_me(user, role)


async def change_password(
    db: AsyncSession,
    user_id: uuid.UUID,
    role: UserRole,
    *,
    current_password: str,
    new_password: str,
) -> None:
    user = await get_user_by_id(db, user_id, role)
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid current password",
        )
    user.password_hash = hash_password(new_password)
    await db.commit()


async def login_employee(db: AsyncSession, username: str, password: str) -> AdminLoginResponse:
    """Вход только для таблицы employees (аналитика / операторы)."""
    result = await db.execute(select(Employee).where(Employee.username == username))
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if employee.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Employee account is inactive",
        )
    if not verify_password(password, employee.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    tokens = create_tokens(employee.id, UserRole.employee)
    return AdminLoginResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        role=UserRole.employee.value,
        employee_role=employee.role,
        username=employee.username,
    )


async def refresh_tokens(refresh_token: str) -> TokenResponse:
    if refresh_token in _revoked_refresh_tokens:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
    payload = decode_token(refresh_token, expected_type="refresh")
    user_id = uuid.UUID(payload["sub"])
    role = UserRole(payload["role"])
    return create_tokens(user_id, role)


async def logout(refresh_token: str | None) -> None:
    if refresh_token:
        _revoked_refresh_tokens.add(refresh_token)


async def get_user_by_id(
    db: AsyncSession, user_id: uuid.UUID, role: UserRole
) -> Client | Employee:
    if role == UserRole.client:
        result = await db.execute(select(Client).where(Client.id == user_id))
        user = result.scalar_one_or_none()
    else:
        result = await db.execute(select(Employee).where(Employee.id == user_id))
        user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


async def request_account_deletion(db: AsyncSession, client_id: uuid.UUID) -> str:
    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    client.deletion_requested_at = datetime.now(UTC)
    await db.commit()
    return "Аккаунт будет удалён через 30 дней"


async def update_notification_preferences(
    db: AsyncSession,
    client_id: uuid.UUID,
    *,
    notify_email: bool | None,
    notify_push: bool | None,
) -> NotificationPreferencesResponse:
    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if notify_email is not None:
        client.notify_email = notify_email
    if notify_push is not None:
        client.notify_push = notify_push
    await db.commit()
    await db.refresh(client)
    return NotificationPreferencesResponse(
        notify_email=client.notify_email,
        notify_push=client.notify_push,
    )


async def _exchange_google_code(code: str) -> str:
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Google OAuth not configured")
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.OAUTH_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth token exchange failed")
        access_token = token_resp.json().get("access_token")
        user_resp = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_resp.status_code != 200:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to fetch Google profile")
        return user_resp.json()


async def _exchange_github_code(code: str) -> dict:
    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="GitHub OAuth not configured")
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.OAUTH_REDIRECT_URI,
            },
            headers={"Accept": "application/json"},
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth token exchange failed")
        access_token = token_resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"}
        user_resp = await client.get("https://api.github.com/user", headers=headers)
        if user_resp.status_code != 200:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to fetch GitHub profile")
        profile = user_resp.json()
        if not profile.get("email"):
            emails_resp = await client.get("https://api.github.com/user/emails", headers=headers)
            if emails_resp.status_code == 200:
                emails = emails_resp.json()
                primary = next((e["email"] for e in emails if e.get("primary")), None)
                profile["email"] = primary or (emails[0]["email"] if emails else None)
        return profile


async def oauth_login(db: AsyncSession, provider: str, code: str) -> TokenResponse:
    if provider == "google":
        profile = await _exchange_google_code(code)
        email = profile.get("email")
        username = profile.get("name") or email.split("@")[0]
    elif provider == "github":
        profile = await _exchange_github_code(code)
        email = profile.get("email")
        username = profile.get("login") or email.split("@")[0]
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown OAuth provider")

    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email not available from provider")

    result = await db.execute(select(Client).where(Client.email == email))
    client = result.scalar_one_or_none()
    if not client:
        base_username = username[:50]
        candidate = base_username
        idx = 1
        while True:
            exists = await db.execute(select(Client).where(Client.username == candidate))
            if not exists.scalar_one_or_none():
                break
            candidate = f"{base_username}_{idx}"
            idx += 1
        client = Client(
            username=candidate,
            email=email,
            full_name=profile.get("name"),
            password_hash=str(uuid.uuid4()),
        )
        db.add(client)
        await db.commit()
        await db.refresh(client)
    return create_tokens(client.id, UserRole.client)
