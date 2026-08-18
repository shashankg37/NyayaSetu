from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.api.v1.deps import current_user
from app.core.config import get_settings
from app.db import get_db
from app.models import User
from app.schemas.features import DocumentResponse
from app.services import document_service
router = APIRouter(prefix='/documents', tags=['documents'])
@router.post('/upload', response_model=DocumentResponse, status_code=201)
async def upload(file: UploadFile = File(...), session_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(current_user)):
    content = await file.read()
    if not file.filename: raise HTTPException(400, 'Filename is required')
    if len(content) > get_settings().max_upload_bytes: raise HTTPException(413, 'Upload exceeds the configured size limit')
    return document_service.upload(db, file.filename, content, session_id, user.id)
@router.get('/{document_id}', response_model=DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return document_service.get_document(db, document_id)
