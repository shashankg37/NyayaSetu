from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.v1.deps import current_user
from app.db import get_db
from app.models import User
from app.schemas.features import TimelineRequest, TimelineResponse
from app.services import timeline_service
router = APIRouter(prefix='/timeline', tags=['timeline'])
@router.post('/build', response_model=TimelineResponse)
def build(payload: TimelineRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = timeline_service.build(db, payload.narrative, payload.session_id, user.id); return {'id': item.id, 'events': item.events}
