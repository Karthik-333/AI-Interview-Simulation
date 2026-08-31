from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user, get_db, require_auth
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth_service import login_for_access_token, register_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
def auth_register(req: RegisterRequest, db: Session = Depends(get_db)):
    user = register_user(db, req.username, req.password, req.email)
    return user


@router.post("/login", response_model=TokenResponse)
def auth_login(req: LoginRequest, db: Session = Depends(get_db)):
    token = login_for_access_token(db, req.username, req.password)
    from app.core.settings import ACCESS_TOKEN_EXPIRE_MINUTES

    return TokenResponse(access_token=token, expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60)


@router.get("/me", response_model=UserResponse)
def auth_me(current_user: User = Depends(require_auth)):
    return current_user


@router.get("/optional-me")
def auth_optional_me(current_user: User | None = Depends(get_current_user)):
    if not current_user:
        return {"authenticated": False}
    return {"authenticated": True, "user": {"id": current_user.id, "username": current_user.username}}
