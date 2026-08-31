from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.core.settings import ACCESS_TOKEN_EXPIRE_MINUTES
from app.models.user import User


def register_user(db: Session, username: str, password: str, email: str | None = None) -> User:
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    if email and db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    user = User(username=username, hashed_password=hash_password(password), email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def login_for_access_token(db: Session, username: str, password: str) -> str:
    user = authenticate_user(db, username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    return create_access_token(data={"sub": user.username}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
