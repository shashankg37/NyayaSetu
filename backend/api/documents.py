from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from backend.api.deps import current_user
from backend.config import get_settings
from backend.database import get_db
from backend.models.database import User, AuditLog, UploadedDocument, Session as UserSession
from backend.models.schemas.features import DocumentResponse
from backend.ai.vision import extract_document
from backend.storage import storage

router = APIRouter(prefix='/documents', tags=['documents'])

def session_for(db: Session, session_id: int | None, user_id: int | None = None) -> UserSession:
    if session_id:
        session = db.get(UserSession, session_id)
        if not session: raise ValueError("Session not found")
        return session
    session = UserSession(user_id=user_id); db.add(session); db.flush(); return session

@router.post('/upload', response_model=DocumentResponse, status_code=201)
async def upload(file: UploadFile = File(...), session_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(current_user)):
    content = await file.read()
    if not file.filename: raise HTTPException(400, 'Filename is required')
    if len(content) > get_settings().max_upload_bytes: raise HTTPException(413, 'Upload exceeds the configured size limit')
    
    result = extract_document(content)
    session = session_for(db, session_id, user.id)
    storage_ref = storage.save('uploads', file.filename, content)
    
    document = UploadedDocument(
        session_id=session.id, 
        original_filename=file.filename, 
        storage_ref=storage_ref, 
        doc_type=result['doc_type'], 
        extracted_fields=result['extracted_fields']
    )
    
    db.add(document)
    db.flush()
    db.add(AuditLog(user_id=user.id, action='document_upload', resource_type='document', resource_id=str(document.id)))
    db.commit()
    db.refresh(document)
    return document

@router.get('/{document_id}', response_model=DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    document = db.get(UploadedDocument, document_id)
    if not document: raise HTTPException(404, 'Document not found')
    return document
