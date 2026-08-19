import base64
from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.api.v1.deps import get_db
from backend.ai.graph import run_query_pipeline_with_audio
from backend.ai.tts import synthesize
from app.services.conversation_service import (
    create_conversation,
    get_conversation_history,
    add_message,
    update_conversation_state
)

router = APIRouter()

class VoiceResponse(BaseModel):
    conversation_id: str
    transcript: str
    reply_text: str
    reply_audio_b64: str | None = None
    next_action: str | None = None

@router.post("/chat", response_model=VoiceResponse)
def voice_chat(
    file: UploadFile,
    conversation_id: str | None = Form(None),
    db: Session = Depends(get_db)
):
    """Process a voice message, returning text and synthesized audio response."""
    if not file.filename.endswith(('.wav', '.mp3', '.ogg', '.m4a')):
        raise HTTPException(status_code=400, detail="Unsupported audio format")
        
    audio_bytes = file.file.read()
    
    conv_id = conversation_id
    history = []
    
    if conv_id:
        history = get_conversation_history(db, conv_id)
    else:
        conv_id = create_conversation(db)

    # Run LangGraph pipeline starting from STT
    result = run_query_pipeline_with_audio(audio_bytes, conversation_history=history)
    
    transcript = result.get("query", "")
    
    if transcript:
        add_message(db, conv_id, "user", transcript, metadata={"input_type": "voice"})
        
    ai_reply_dict = result.get("answer", {})
    ai_reply_text = ai_reply_dict.get("your_right", "")
    if not ai_reply_text:
        ai_reply_text = str(ai_reply_dict)
        
    if ai_reply_text:
        add_message(db, conv_id, "ai", ai_reply_text, metadata={"intent": result.get("intent")})
        
    update_conversation_state(db, conv_id, result)
    
    # Synthesize audio response
    # We need to pass the target language. By default, synthesize uses 'en'
    # We could detect it from the transcript or user preferences.
    audio_response_bytes = synthesize(ai_reply_text, target_language="en")
    
    reply_audio_b64 = None
    if audio_response_bytes:
        reply_audio_b64 = base64.b64encode(audio_response_bytes).decode('ascii')
        
    return VoiceResponse(
        conversation_id=conv_id,
        transcript=transcript,
        reply_text=ai_reply_text,
        reply_audio_b64=reply_audio_b64,
        next_action=result.get("next_action")
    )
