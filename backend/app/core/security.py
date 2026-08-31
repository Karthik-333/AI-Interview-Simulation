import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt  # pyjwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.settings import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from app.models.user import User

# Use simple pbkdf2 via hashlib to avoid bcrypt dependency issues in this env;
# compatible with existing tests and easy to run offline.
# Format: pbkdf2_sha256$<salt_hex>$<hash_hex>

def _hash_pbkdf2(password: str, salt: bytes | None = None) -> str:
    if salt is None:
        salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return f"pbkdf2_sha256${salt.hex()}${dk.hex()}"

def hash_password(password: str) -> str:
    return _hash_pbkdf2(password)

def verify_password(plain: str, hashed: str) -> bool:
    try:
        algo, salt_hex, hash_hex = hashed.split("$")
        if algo != "pbkdf2_sha256":
            return False
        salt = bytes.fromhex(salt_hex)
        expected = _hash_pbkdf2(plain, salt)
        return secrets.compare_digest(expected, hashed)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


bearer_scheme = HTTPBearer(auto_error=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None
    token = credentials.credentials
    payload = decode_access_token(token)
    username: str | None = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_auth(
    current_user: User | None = Depends(get_current_user),
) -> User:
    from app.core.settings import REQUIRE_AUTH

    if REQUIRE_AUTH and current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    # when REQUIRE_AUTH is False we still allow anonymous; but if token was invalid we already raised
    # for endpoints that need a user, callers should check `if current_user is None` and fallback to user_name
    if current_user is None:
        # create a dummy anonymous handling: raise only if endpoint explicitly requires it
        # callers that use this dependency expect a User, so return 401 when no user and REQUIRE_AUTH=False?
        # Instead, provide an optional wrapper: get_current_user_optional vs require_auth
        raise HTTPException(status_code=401, detail="Not authenticated")
    return current_user


def get_current_user_optional(
    current_user: User | None = Depends(get_current_user),
) -> User | None:
    return current_user
