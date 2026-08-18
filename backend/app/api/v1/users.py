from fastapi import APIRouter, Depends
from app.api.v1.deps import current_user
from app.models import User
from app.schemas.auth import UserResponse
router = APIRouter(prefix='/users', tags=['users'])
@router.get('/me', response_model=UserResponse)
def me(user: User = Depends(current_user)): return user
