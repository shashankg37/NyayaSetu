from __future__ import annotations

from typing import Any, TypedDict


class PipelineState(TypedDict, total=False):
    conversation_id: int | str
    user_id: int | str
    language: str
    conversation_history: list[dict[str, Any]]
    current_message: str
    input_type: str
    text: str
    audio_bytes: bytes
    image_bytes: bytes
    normalized_text: str
    intent: str
    beneficiary: str
    legal_domain: str
    jurisdiction: str
    current_issue: str
    collected_information: dict[str, Any]
    missing_information: list[str]
    pending_slot: str
    uploaded_document: dict[str, Any]
    chunks: list[dict[str, Any]]
    retrieved_chunks: list[dict[str, Any]]
    reranked_chunks: list[dict[str, Any]]
    confidence_score: float
    evidence_status: str
    evidence_decision: str
    evidence_sufficient: bool
    safety_status: str
    next_action: str
    answer: dict[str, Any]
    document: dict[str, Any]
    db_session: Any
