from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.api.deps import admin_user, current_user
from backend.api.security import create_token, decode_token, hash_password, verify_password
from backend.config import get_settings
from backend.database import get_db
from backend.models.database import AuditLog, Role, User
from backend.models.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, RoleUpdateRequest, TokenResponse, UserResponse

router = APIRouter(prefix='/auth', tags=['auth'])

def audit(db: Session, user_id: int | None, action: str, resource_type: str, resource_id: str) -> None:
    db.add(AuditLog(user_id=user_id, action=action, resource_type=resource_type, resource_id=resource_id))

def tokens_for(user: User) -> TokenResponse:
    settings = get_settings()
    return TokenResponse(
        access_token=create_token(str(user.id), "access", timedelta(minutes=settings.access_token_expire_minutes)), 
        refresh_token=create_token(str(user.id), "refresh", timedelta(days=settings.refresh_token_expire_days))
    )

@router.post('/register', response_model=UserResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first(): 
        raise HTTPException(409, "Email is already registered")
    user = User(
        email=payload.email, 
        hashed_password=hash_password(payload.password), 
        role=Role.citizen, 
        preferred_language=payload.preferred_language, 
        consent_given=payload.consent_given
    )
    db.add(user)
    db.flush()
    audit(db, user.id, "register", "user", str(user.id))
    db.commit()
    db.refresh(user)
    return user

@router.post('/login', response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password): 
        raise HTTPException(401, "Incorrect email or password")
    audit(db, user.id, "login", "user", str(user.id))
    db.commit()
    return tokens_for(user)

@router.post('/refresh', response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    user = db.get(User, int(decode_token(payload.refresh_token, "refresh")))
    if not user: 
        raise HTTPException(401, "User not found")
    return tokens_for(user)

@router.put('/users/{user_id}/role', response_model=UserResponse)
def change_role(user_id: int, payload: RoleUpdateRequest, db: Session = Depends(get_db), admin: User = Depends(admin_user)):
    user = db.get(User, user_id)
    if not user: 
        raise HTTPException(404, 'User not found')
    user.role = payload.role
    audit(db, admin.id, 'role_change', 'user', str(user.id))
    db.commit()
    db.refresh(user)
    return user
