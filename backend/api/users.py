from fastapi import APIRouter, Depends
from backend.api.v1.deps import current_user
from backend.models.database import User
from backend.models.schemas.auth import UserResponse
router = APIRouter(prefix='/users', tags=['users'])
@router.get('/me', response_model=UserResponse)
def me(user: User = Depends(current_user)): return user
