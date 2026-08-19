from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from backend.ai.graph import run_query_pipeline_with_document
from backend.api.chat import create_conversation
from backend.api.deps import current_user
from backend.api.files import read_and_validate_upload
from backend.config import get_settings
from backend.database import get_db
from backend.models.database import AuditLog, Session as UserSession, UploadedDocument, User
from backend.models.schemas.features import DocumentResponse
from backend.storage import storage

router = APIRouter(prefix="/documents", tags=["documents"])


def session_for(db: Session, session_id: int | None, user_id: int | None = None) -> UserSession:
    if session_id:
        session = db.get(UserSession, session_id)
        if not session:
            raise ValueError("Session not found")
        return session
    session = UserSession(user_id=user_id)
    db.add(session)
    db.flush()
    return session


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload(
    file: UploadFile,
    session_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    filename, content, _ = read_and_validate_upload(file, kind="document")
    result = run_query_pipeline_with_document(content, db_session=db)
    document_info = result.get("document") or {}
    session = session_for(db, session_id, user.id)
    storage_ref = storage.save("uploads", filename, content)
    document = UploadedDocument(
        session_id=session.id,
        original_filename=filename,
        storage_ref=storage_ref,
        doc_type=document_info.get("doc_type"),
        extracted_fields={
            "extracted_fields": document_info.get("extracted_fields"),
            "answer": result.get("answer"),
            "citations": (result.get("answer") or {}).get("citations"),
        },
    )
    db.add(document)
    db.flush()
    db.add(AuditLog(user_id=user.id, action="document_upload", resource_type="document", resource_id=str(document.id)))
    db.commit()
    db.refresh(document)
    return document


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    document = db.get(UploadedDocument, document_id)
    if not document:
        from fastapi import HTTPException

        raise HTTPException(404, "Document not found")
    return document
