from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.schemas.auth import LoginRequest, LoginResponse
from backend.app.schemas.user import UserCreate, UserResponse
from backend.app.services import auth_service

router = APIRouter(tags=["auth"])


@router.post("/register_client", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    return auth_service.register_client(db, user)


@router.post("/login_client", response_model=LoginResponse)
def login_client(credentials: LoginRequest, db: Session = Depends(get_db)):
    auth_service.login_client(db, credentials.username, credentials.password)
    return LoginResponse(message="success")
