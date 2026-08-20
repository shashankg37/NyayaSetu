from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.ai.speech import transcribe, synthesize, SpeechTranscriptionError, SpeechSynthesisError
from backend.api.deps import current_user
from backend.database import get_db
from backend.models.database import User
from backend.api.files import read_and_validate_upload

router = APIRouter(tags=["speech"])


class SynthesizeRequest(BaseModel):
    text: str
    language: str = "en-IN"


def map_pref_language(pref: str | None) -> str:
    if not pref:
        return "en-IN"
    pref = pref.lower().strip()
    if pref == "hi":
        return "hi-IN"
    if pref == "kn":
        return "kn-IN"
    if pref == "en":
        return "en-IN"
    if "-" in pref:
        return pref
    return "en-IN"


@router.post("/transcribe")
def speech_transcribe(
    file: UploadFile,
    language: str | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    try:
        _, audio_bytes, _ = read_and_validate_upload(file, kind="audio")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Resolve transcription language
    tx_lang = language
    if not tx_lang and user.preferred_language:
        tx_lang = map_pref_language(user.preferred_language)
    if not tx_lang:
        tx_lang = "en-IN"

    import logging
    logging.getLogger("backend.api.speech").info(f"STT language: {tx_lang}")

    try:
        text = transcribe(audio_bytes, source_language=tx_lang)
        return {"text": text, "language": tx_lang}
    except SpeechTranscriptionError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/synthesize")
def speech_synthesize(
    request: SynthesizeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    import logging
    logging.getLogger("backend.api.speech").info(f"TTS language: {request.language}")

    try:
        audio_bytes = synthesize(request.text, target_language=request.language)
        return Response(content=audio_bytes, media_type="audio/wav")
    except SpeechSynthesisError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

