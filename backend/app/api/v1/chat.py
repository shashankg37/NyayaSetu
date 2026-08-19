from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.ai.graph import run_query_pipeline
from app.services.conversation_service import (
    create_conversation,
    get_conversation_history,
    add_message,
    update_conversation_state,
    get_conversation_state
)

router = APIRouter()

class ChatRequest(BaseModel):
    conversation_id: str | None = None
    message: str

class ChatResponse(BaseModel):
    conversation_id: str
    reply: dict
    next_action: str | None = None

@router.post("/message", response_model=ChatResponse)
def send_message(request: ChatRequest, db: Session = Depends(get_db)):
    """Send a message to the LangGraph chat pipeline."""
    conv_id = request.conversation_id
    history = []
    
    if conv_id:
        # Load existing history
        history = get_conversation_history(db, conv_id)
        state = get_conversation_state(db, conv_id)
    else:
        # Create new conversation
        conv_id = create_conversation(db)
        state = {}

    # Add user message to DB
    add_message(db, conv_id, "user", request.message)

    # Run LangGraph pipeline
    result = run_query_pipeline(request.message, input_type="text", conversation_history=history)

    # Add AI response to DB
    ai_reply_text = result.get("answer", {}).get("your_right", "")
    if not ai_reply_text:
        ai_reply_text = str(result.get("answer", ""))
        
    add_message(db, conv_id, "ai", ai_reply_text, metadata={"intent": result.get("intent")})

    # Update conversation state
    # We store the latest result in the state for context
    update_conversation_state(db, conv_id, result)

    return ChatResponse(
        conversation_id=conv_id,
        reply=result.get("answer", {}),
        next_action=result.get("next_action")
    )

@router.get("/{conversation_id}/history")
def get_history(conversation_id: str, db: Session = Depends(get_db)):
    """Get the full message history of a conversation."""
    history = get_conversation_history(db, conversation_id)
    if not history:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return {"conversation_id": conversation_id, "history": history}
