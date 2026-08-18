from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.security import get_token
from app.db import get_db
from app.models import Role, User
from app.services.auth_service import user_from_access

def current_user(db: Session = Depends(get_db), token: str = Depends(get_token)) -> User: return user_from_access(db, token)
def admin_user(user: User = Depends(current_user)) -> User:
    if user.role != Role.admin: raise HTTPException(403, 'Admin access required')
    return user
