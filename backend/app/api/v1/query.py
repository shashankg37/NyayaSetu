from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.api.v1.deps import current_user
from app.core.config import get_settings
from app.db import get_db
from app.models import InputType, User
from app.schemas.common import LegalAnswer
from app.schemas.features import KyrRequest, QueryRequest
from app.services import query_service
router = APIRouter(tags=['legal queries'])
@router.post('/query', response_model=LegalAnswer)
def query(payload: QueryRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return query_service.answer(db, payload.text, InputType.text, payload.session_id, user.id)
@router.post('/query/voice', response_model=LegalAnswer)
async def voice(file: UploadFile = File(...), session_id: int | None = Form(None), db: Session = Depends(get_db), user: User = Depends(current_user)):
    content = await file.read()
    if len(content) > get_settings().max_upload_bytes: raise HTTPException(413, 'Upload exceeds the configured size limit')
    return query_service.voice_answer(db, content, session_id, user.id)
@router.post('/kyr/browse', response_model=LegalAnswer)
def kyr(payload: KyrRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    text = f'{payload.beneficiary}: {payload.topic}. {payload.situation or ""}'
    return query_service.answer(db, text, InputType.text, payload.session_id, user.id)
