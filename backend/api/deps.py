from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from backend.api.security import get_token, decode_token
from backend.database import get_db
from backend.models.database import Role, User

def user_from_access(db: Session, token: str) -> User:
    user = db.get(User, int(decode_token(token, "access")))
    if not user: raise HTTPException(401, "User not found")
    return user

def current_user(db: Session = Depends(get_db), token: str = Depends(get_token)) -> User: 
    return user_from_access(db, token)

def admin_user(user: User = Depends(current_user)) -> User:
    if user.role != Role.admin: raise HTTPException(403, 'Admin access required')
    return user
