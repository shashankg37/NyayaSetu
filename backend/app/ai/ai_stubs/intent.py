from __future__ import annotations

from app.ai.ai_stubs.common import tokenize


def classify_intent(text: str) -> str:
    lowered = text.lower()
    draft_markers = {
        "draft",
        "notice",
        "petition",
        "complaint",
        "application",
        "reply",
        "legal notice",
        "agreement",
        "affidavit",
    }
    procedure_markers = {"how to", "procedure", "file", "appeal", "step", "process", "where to"}
    if any(marker in lowered for marker in draft_markers):
        return "document_draft_request"
    if any(marker in lowered for marker in procedure_markers):
        return "procedure_query"
    tokens = set(tokenize(text))
    if {"notice", "draft", "format"} & tokens:
        return "document_draft_request"
    if {"how", "where", "when", "process", "steps"} & tokens:
        return "procedure_query"
    return "rights_query"

