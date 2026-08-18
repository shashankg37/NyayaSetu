from datetime import timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.ai_stubs.intent import classify_intent
from app.core.config import get_settings
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.models import AuditLog, Role, User
from app.schemas.auth import RegisterRequest, TokenResponse

def audit(db: Session, user_id: int | None, action: str, resource_type: str, resource_id: str) -> None:
    db.add(AuditLog(user_id=user_id, action=action, resource_type=resource_type, resource_id=resource_id))

def tokens_for(user: User) -> TokenResponse:
    settings = get_settings()
    return TokenResponse(access_token=create_token(str(user.id), "access", timedelta(minutes=settings.access_token_expire_minutes)), refresh_token=create_token(str(user.id), "refresh", timedelta(days=settings.refresh_token_expire_days)))

def register(db: Session, payload: RegisterRequest) -> User:
    if db.query(User).filter(User.email == payload.email).first(): raise HTTPException(409, "Email is already registered")
    user = User(email=payload.email, hashed_password=hash_password(payload.password), role=Role.citizen, preferred_language=payload.preferred_language, consent_given=payload.consent_given)
    db.add(user); db.flush(); audit(db, user.id, "register", "user", str(user.id)); db.commit(); db.refresh(user); return user

def login(db: Session, email: str, password: str) -> TokenResponse:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password): raise HTTPException(401, "Incorrect email or password")
    audit(db, user.id, "login", "user", str(user.id)); db.commit(); return tokens_for(user)

def user_from_access(db: Session, token: str) -> User:
    user = db.get(User, int(decode_token(token, "access")))
    if not user: raise HTTPException(401, "User not found")
    return user

def refresh(db: Session, refresh_token: str) -> TokenResponse:
    user = db.get(User, int(decode_token(refresh_token, "refresh")))
    if not user: raise HTTPException(401, "User not found")
    return tokens_for(user)
