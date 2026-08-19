from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.ai.graph import run_query_pipeline
from backend.api.deps import current_user
from backend.database import get_db
from backend.models.database import Conversation, Message, User

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


def create_conversation(
    db: Session,
    user_id: int | None = None,
    language: str = "en",
    legal_domain: str | None = None,
    initial_state: dict[str, Any] | None = None,
) -> str:
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
    return conv_id


def get_conversation_state(db: Session, conversation_id: str) -> dict[str, Any]:
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    return dict(conv.state_json) if conv else {}


def update_conversation_state(db: Session, conversation_id: str, state: dict[str, Any]) -> None:
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        return
    conv.state_json = state
    conv.updated_at = datetime.utcnow()
    db.commit()


def add_message(db: Session, conversation_id: str, role: str, content: str, metadata: dict[str, Any] | None = None) -> None:
    db.add(
        Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata_json=metadata or {},
        )
    )
    db.commit()


def get_conversation_history(db: Session, conversation_id: str) -> list[dict[str, Any]]:
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
    evidence_status: str | None = None


@router.post("/message", response_model=ChatResponse)
def send_message(request: ChatRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    conv_id = request.conversation_id
    history: list[dict[str, Any]] = []
    state: dict[str, Any] = {}
    if conv_id:
        existing = db.get(Conversation, conv_id)
        if not existing:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
        if existing.user_id not in {None, user.id}:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Conversation does not belong to this user")
        history = get_conversation_history(db, conv_id)
        state = get_conversation_state(db, conv_id)
    else:
        conv_id = create_conversation(db, user_id=user.id)

    add_message(db, conv_id, "user", request.message)
    result = run_query_pipeline(
        request.message,
        input_type="text",
        conversation_history=history,
        conversation_state=state,
        db_session=db,
    )
    ai_reply = result.get("answer") or {}
    add_message(db, conv_id, "assistant", str(ai_reply.get("your_right") or ai_reply), metadata={"intent": result.get("intent")})
    persistable = {k: v for k, v in result.items() if k not in {"chunks", "retrieved_chunks", "reranked_chunks", "document"}}
    persistable["collected_information"] = result.get("collected_information") or {}
    persistable["current_issue"] = result.get("current_issue")
    persistable["pending_slot"] = result.get("pending_slot")
    update_conversation_state(db, conv_id, persistable)
    return ChatResponse(
        conversation_id=conv_id,
        reply=ai_reply,
        next_action=result.get("next_action"),
        evidence_status=result.get("evidence_status"),
    )


@router.get("/{conversation_id}/history")
def get_history(conversation_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    conv = db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    if conv.user_id not in {None, user.id}:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Conversation does not belong to this user")
    return {"conversation_id": conversation_id, "history": get_conversation_history(db, conversation_id)}
