from __future__ import annotations

from app.ai_stubs.common import tokenize


def classify_intent(text: str) -> str:
    """Returns one of: rights_query, document_draft_request, procedure_query."""
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
    procedure_markers = {
        "how to",
        "procedure",
        "file",
        "appeal",
        "step",
        "process",
        "where do i",
        "where to",
        "what is the procedure",
    }
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

