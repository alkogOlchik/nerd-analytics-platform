import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.models.enums import UserRole
from backend.app.models.user import Client, Employee
from backend.app.schemas.auth import TokenResponse
from backend.app.schemas.user import ClientRegister

settings = get_settings()
ALGORITHM = "HS256"
_revoked_refresh_tokens: set[str] = set()


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


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
    existing = await db.execute(
        select(Client).where((Client.username == data.username) | (Client.email == data.email))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already exists")

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
