from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.ai.vision import extract_document
from app.models import AuditLog, UploadedDocument
from app.services.query_service import session_for
from app.services.storage_service import storage

def upload(db: Session, filename: str, content: bytes, session_id: int | None, user_id: int | None) -> UploadedDocument:
    result = extract_document(content); session = session_for(db, session_id, user_id)
    document = UploadedDocument(session_id=session.id, original_filename=filename, storage_ref=storage.save('uploads', filename, content), doc_type=result['doc_type'], extracted_fields=result['extracted_fields'])
    db.add(document); db.flush(); db.add(AuditLog(user_id=user_id, action='document_upload', resource_type='document', resource_id=str(document.id))); db.commit(); db.refresh(document); return document

def get_document(db: Session, document_id: int) -> UploadedDocument:
    document = db.get(UploadedDocument, document_id)
    if not document: raise HTTPException(404, 'Document not found')
    return document
