from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
