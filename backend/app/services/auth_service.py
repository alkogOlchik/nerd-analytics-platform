import bcrypt
from fastapi import HTTPException
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from backend.app.models.user import Client
from backend.app.schemas.user import UserCreate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    password_bytes = password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def register_client(db: Session, user: UserCreate) -> Client:
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


def login_client(db: Session, username: str, password: str) -> None:
    db_user = db.query(Client).filter(Client.username == username).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Wrong username")
    if not verify_password(password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Wrong password")
