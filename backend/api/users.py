from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.deps import current_user
from backend.database import get_db
from backend.models.database import User
from backend.models.schemas.auth import UpdateProfileRequest, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(current_user)):
    return user


@router.put("/me", response_model=UserResponse)
def update_me(payload: UpdateProfileRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.phone is not None:
        user.phone = payload.phone
    if payload.city is not None:
        user.city = payload.city
    if payload.issue_type is not None:
        user.issue_type = payload.issue_type
    if payload.preferred_language is not None:
        user.preferred_language = payload.preferred_language
    if payload.consent_given is not None:
        user.consent_given = payload.consent_given

    db.add(user)
    db.commit()
    db.refresh(user)
    return user
