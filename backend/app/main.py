from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.models.user import Client
from backend.app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    UserCreate,
    UserResponse,
)
from backend.app.services.auth_serv import hash_password, verify_password

app = FastAPI(title="Нёрд Аналитика")

@app.post("/register_client", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(Client).filter(Client.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username is used")
    if db.query(Client).filter(Client.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email is used")

    db_user = Client(
        username=user.username,
        email=user.email,
        password_hash=hash_password(user.password),
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

@app.post("/login_client", response_model=LoginResponse)
def login_client(credentials: LoginRequest, db: Session = Depends(get_db)):
    db_user = db.query(Client).filter(Client.username == credentials.username).first()

    if not db_user:
        raise HTTPException(status_code=401, detail="Wrong username")
    if not verify_password(credentials.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Wrong password")
    return LoginResponse(message="success")
