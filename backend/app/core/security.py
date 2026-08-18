from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from app.core.config import get_settings

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_context.verify(password, hashed_password)


def create_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    payload = {"sub": subject, "type": token_type, "exp": datetime.now(timezone.utc) + expires_delta}
    return jwt.encode(payload, get_settings().secret_key, algorithm="HS256")


def decode_token(token: str, expected_type: str) -> str:
    try:
        payload = jwt.decode(token, get_settings().secret_key, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc
    if payload.get("type") != expected_type or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Invalid token type")
    return payload["sub"]


def get_token(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> str:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return credentials.credentials
