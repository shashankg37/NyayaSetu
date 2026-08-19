from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.ai.graph import run_query_pipeline
from backend.models.database import Conversation, Message

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


def create_conversation(
    db: Session,
    user_id: int | None = None,
    language: str = "en",
    legal_domain: str | None = None,
    initial_state: dict[str, Any] | None = None,
) -> str:
    """Create a new conversation session."""
    conv_id = str(uuid.uuid4())
    conv = Conversation(
        id=conv_id,
        user_id=user_id,
        language=language,
        legal_domain=legal_domain,
        state_json=initial_state or {},
    )
    db.add(conv)
    db.commit()
    logger.info("Created new conversation: %s", conv_id)
    return conv_id


def get_conversation_state(db: Session, conversation_id: str) -> dict[str, Any]:
    """Retrieve the current LangGraph state for a conversation."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        logger.warning("Conversation %s not found", conversation_id)
        return {}
    return dict(conv.state_json)


def update_conversation_state(
    db: Session,
    conversation_id: str,
    state: dict[str, Any],
) -> None:
    """Update the LangGraph state for a conversation."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conv:
        conv.state_json = state
        conv.updated_at = datetime.utcnow()
        db.commit()
        logger.debug("Updated state for conversation: %s", conversation_id)
    else:
        logger.warning("Attempted to update non-existent conversation: %s", conversation_id)


def add_message(
    db: Session,
    conversation_id: str,
    role: str,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Add a message to the conversation history."""
    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        metadata_json=metadata or {},
    )
    db.add(msg)
    db.commit()


def get_conversation_history(db: Session, conversation_id: str) -> list[dict[str, Any]]:
    """Retrieve the full message history for a conversation."""
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    return [
        {
            "role": msg.role,
            "content": msg.content,
            "metadata": msg.metadata_json,
            "timestamp": msg.created_at.isoformat(),
        }
        for msg in messages
    ]


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
