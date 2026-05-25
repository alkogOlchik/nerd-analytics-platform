from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import CurrentUser, get_current_user
from backend.app.db.session import get_db
from backend.app.schemas.auth import LoginRequest, LogoutRequest, RefreshRequest, TokenResponse
from backend.app.schemas.user import ClientRegister, ClientResponse, UserMeResponse
from backend.app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=ClientResponse, status_code=201)
async def register(data: ClientRegister, db: AsyncSession = Depends(get_db)):
    return await auth_service.register_client(db, data)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.login(db, data.username, data.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest):
    return await auth_service.refresh_tokens(data.refresh_token)


@router.post("/logout", status_code=204)
async def logout(data: LogoutRequest):
    await auth_service.logout(data.refresh_token)
    return None


@router.get("/me", response_model=UserMeResponse)
async def me(current_user: CurrentUser = Depends(get_current_user)):
    return UserMeResponse(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        email=current_user.email,
        full_name=current_user.full_name,
    )
