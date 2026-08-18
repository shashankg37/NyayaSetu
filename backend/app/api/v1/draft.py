from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.api.v1.deps import current_user
from app.db import get_db
from app.models import User
from app.schemas.features import DraftAnswerRequest, DraftResponse, DraftStartRequest
from app.services import draft_service
router = APIRouter(prefix='/draft', tags=['drafting'])
@router.post('/start', response_model=DraftResponse, status_code=201)
def start(payload: DraftStartRequest, db: Session = Depends(get_db), user: User = Depends(current_user)): return draft_service.start(db, payload.doc_type, payload.known_fields, payload.session_id, user.id)
@router.post('/{draft_id}/answer', response_model=DraftResponse)
def answer(draft_id: int, payload: DraftAnswerRequest, db: Session = Depends(get_db), user: User = Depends(current_user)): return draft_service.add_answer(db, draft_id, payload.fields)
@router.post('/{draft_id}/generate', response_model=DraftResponse)
def generate(draft_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)): return draft_service.generate(db, draft_id, user.id)
@router.get('/{draft_id}/download')
def download(draft_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    path = draft_service.download(db, draft_id); return FileResponse(path, filename='nyaya_setu_draft.pdf', media_type='application/pdf')
