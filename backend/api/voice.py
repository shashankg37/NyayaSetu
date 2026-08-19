import base64

from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.ai.graph import run_query_pipeline_with_audio
from backend.ai.tts import SpeechSynthesisError, synthesize
from backend.api.chat import add_message, create_conversation, get_conversation_history, get_conversation_state, update_conversation_state
from backend.api.deps import current_user
from backend.api.files import read_and_validate_upload
from backend.database import get_db
from backend.models.database import Conversation, User

router = APIRouter(tags=["voice"])


class VoiceResponse(BaseModel):
    conversation_id: str
    transcript: str
    reply_text: str
    reply_audio_b64: str | None = None
    next_action: str | None = None
    service_error: bool = False


@router.post("/chat", response_model=VoiceResponse)
def voice_chat(
    file: UploadFile,
    conversation_id: str | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    _, audio_bytes, _ = read_and_validate_upload(file, kind="audio")
    conv_id = conversation_id
    history = []
    state = {}
    if conv_id:
        existing = db.get(Conversation, conv_id)
        if not existing:
            raise HTTPException(404, "Conversation not found")
        history = get_conversation_history(db, conv_id)
        state = get_conversation_state(db, conv_id)
    else:
        conv_id = create_conversation(db, user_id=user.id)

    result = run_query_pipeline_with_audio(audio_bytes, conversation_history=history, conversation_state=state, db_session=db)
    transcript = result.get("query") or result.get("normalized_text") or ""
    if transcript:
        add_message(db, conv_id, "user", transcript, metadata={"input_type": "voice"})
    answer = result.get("answer") or {}
    reply_text = str(answer.get("your_right") or "")
    if reply_text:
        add_message(db, conv_id, "assistant", reply_text, metadata={"intent": result.get("intent")})
    update_conversation_state(db, conv_id, result)

    reply_audio_b64 = None
    service_error = bool(answer.get("service_error"))
    if reply_text and not service_error:
        try:
            audio = synthesize(reply_text, target_language=result.get("language") or "en")
            reply_audio_b64 = base64.b64encode(audio).decode("ascii")
        except SpeechSynthesisError as exc:
            service_error = True
            reply_text = f"{reply_text}\n\n(Voice synthesis failed: {exc})"

    return VoiceResponse(
        conversation_id=conv_id,
        transcript=transcript,
        reply_text=reply_text,
        reply_audio_b64=reply_audio_b64,
        next_action=result.get("next_action"),
        service_error=service_error,
    )
