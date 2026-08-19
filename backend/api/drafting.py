from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.ai.drafting import DISCLAIMER, export_draft, required_for
from backend.ai.language import missing_fields
from backend.api.deps import current_user
from backend.database import get_db
from backend.models.database import DraftStatus, DraftedDocument, Session as UserSession, User
from backend.models.schemas.features import DraftAnswerRequest, DraftResponse, DraftStartRequest

router = APIRouter(prefix="/drafting", tags=["drafting"])


def _session(db: Session, session_id: int | None, user_id: int) -> UserSession:
    if session_id:
        session = db.get(UserSession, session_id)
        if not session:
            raise HTTPException(404, "Session not found")
        return session
    session = UserSession(user_id=user_id)
    db.add(session)
    db.flush()
    return session


def _response(draft: DraftedDocument) -> DraftResponse:
    missing = missing_fields(draft.doc_type, draft.collected_fields or {})
    return DraftResponse(
        id=draft.id,
        doc_type=draft.doc_type,
        draft_status=draft.draft_status,
        collected_fields=draft.collected_fields or {},
        missing_fields=missing,
        disclaimer=DISCLAIMER,
        final_file_ref=draft.final_file_ref,
    )


@router.post("/start", response_model=DraftResponse, status_code=201)
def start(payload: DraftStartRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if payload.doc_type not in {"rti", "wage_complaint", "consumer_complaint", "government_grievance", "legal_notice"}:
        raise HTTPException(400, "Unsupported draft type")
    session = _session(db, payload.session_id, user.id)
    draft = DraftedDocument(
        session_id=session.id,
        doc_type=payload.doc_type,
        collected_fields=payload.known_fields,
        draft_status=DraftStatus.ready.value if not missing_fields(payload.doc_type, payload.known_fields) else DraftStatus.collecting.value,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return _response(draft)


@router.post("/{draft_id}/answer", response_model=DraftResponse)
def answer(draft_id: int, payload: DraftAnswerRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    draft = db.get(DraftedDocument, draft_id)
    if not draft:
        raise HTTPException(404, "Draft not found")
    fields = dict(draft.collected_fields or {})
    fields.update(payload.fields)
    draft.collected_fields = fields
    draft.draft_status = DraftStatus.ready.value if not missing_fields(draft.doc_type, fields) else DraftStatus.collecting.value
    db.commit()
    db.refresh(draft)
    return _response(draft)


@router.post("/{draft_id}/generate", response_model=DraftResponse)
def generate(draft_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    draft = db.get(DraftedDocument, draft_id)
    if not draft:
        raise HTTPException(404, "Draft not found")
    missing = missing_fields(draft.doc_type, draft.collected_fields or {})
    if missing:
        raise HTTPException(400, f"Missing required fields: {', '.join(missing)}")
    pdf_path = export_draft(draft.doc_type, draft.collected_fields, "pdf")
    export_draft(draft.doc_type, draft.collected_fields, "docx")
    draft.final_file_ref = str(pdf_path)
    draft.draft_status = DraftStatus.generated.value
    db.commit()
    db.refresh(draft)
    return _response(draft)


@router.get("/{draft_id}/download")
def download(draft_id: int, fmt: str = "pdf", db: Session = Depends(get_db), user: User = Depends(current_user)):
    draft = db.get(DraftedDocument, draft_id)
    if not draft or not draft.final_file_ref:
        raise HTTPException(404, "Generated draft not found")
    path = draft.final_file_ref
    if fmt == "docx":
        path = path.replace(".pdf", ".docx")
    media = "application/pdf" if fmt == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return FileResponse(path, filename=f"nyaya_setu_draft.{fmt}", media_type=media)
