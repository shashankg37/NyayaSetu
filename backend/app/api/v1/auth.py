from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.v1.deps import admin_user, current_user
from app.db import get_db
from app.models import Role, User
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, RoleUpdateRequest, TokenResponse, UserResponse
from app.services import auth_service
router = APIRouter(prefix='/auth', tags=['auth'])
@router.post('/register', response_model=UserResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)): return auth_service.register(db, payload)
@router.post('/login', response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)): return auth_service.login(db, payload.email, payload.password)
@router.post('/refresh', response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)): return auth_service.refresh(db, payload.refresh_token)
@router.put('/users/{user_id}/role', response_model=UserResponse)
def change_role(user_id: int, payload: RoleUpdateRequest, db: Session = Depends(get_db), admin: User = Depends(admin_user)):
    user = db.get(User, user_id)
    if not user: from fastapi import HTTPException; raise HTTPException(404, 'User not found')
    user.role = payload.role; auth_service.audit(db, admin.id, 'role_change', 'user', str(user.id)); db.commit(); db.refresh(user); return user
