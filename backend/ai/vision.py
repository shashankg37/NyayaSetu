"""Non-authoritative user-document extraction through the primary Qwen model."""
from __future__ import annotations

import logging
from io import BytesIO
from typing import Any

from backend.ai.llm import generate_json_from_image

logger = logging.getLogger(__name__)


def _extract_pdf_text(file_bytes: bytes) -> str:
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except Exception as exc:
        logger.error("PDF extraction failed: %s", exc)
        return ""


def _detect_mime(file_bytes: bytes) -> str:
    mime_type = "application/octet-stream"
    if file_bytes.startswith(b"%PDF"):
        mime_type = "application/pdf"
    elif file_bytes.startswith(b"\xff\xd8"):
        mime_type = "image/jpeg"
    elif file_bytes.startswith(b"\x89PNG"):
        mime_type = "image/png"
    elif file_bytes.startswith(b"RIFF"):
        mime_type = "image/webp"
    return mime_type


def _structured_query(structured: dict[str, Any], extracted_text: str) -> str:
    return " ".join(
        part
        for part in [
            str(structured.get("document_type") or ""),
            " ".join(str(item) for item in structured.get("sections_mentioned") or []),
            " ".join(str(item) for item in structured.get("deadlines") or []),
            str(structured.get("important_facts") or extracted_text[:500]),
        ]
        if part
    ).strip()


def _normalize_structured(data: dict[str, Any] | None, extracted_text: str) -> dict[str, Any]:
    payload = data or {}
    return {
        "document_type": payload.get("document_type") or "unknown_document",
        "parties": payload.get("parties") or [],
        "dates": payload.get("dates") or payload.get("key_dates") or [],
        "authorities": payload.get("authorities") or ([payload.get("issuer")] if payload.get("issuer") else []),
        "sections_mentioned": payload.get("sections_mentioned") or payload.get("cited_provisions") or [],
        "deadlines": payload.get("deadlines") or ([payload.get("deadline")] if payload.get("deadline") else []),
        "clauses": payload.get("clauses") or payload.get("important_clauses") or [],
        "important_facts": payload.get("important_facts") or payload.get("summary") or extracted_text[:800],
    }


def _qwen_understand_document(file_bytes: bytes, mime_type: str, extracted_text: str) -> dict[str, Any] | None:
    prompt = (
        "You are extracting facts from a user-uploaded legal document for Nyaya Setu. "
        "Use the image/PDF only to understand the user's document. This is not authoritative law. "
        "Return JSON with keys: document_type, parties, dates, authorities, sections_mentioned, "
        "deadlines, clauses, important_facts, retrieval_query. Do not answer the legal question."
    )
    result = generate_json_from_image(prompt, file_bytes, mime_type)
    if result:
        return result
    if extracted_text:
        return {
            "document_type": "text_document",
            "important_facts": extracted_text[:1000],
            "retrieval_query": extracted_text[:1000],
        }
    return None


def extract_document(file_bytes: bytes) -> dict[str, Any]:
    mime_type = _detect_mime(file_bytes)

    extracted_text = _extract_pdf_text(file_bytes) if mime_type == "application/pdf" else ""
    provider_payload = _qwen_understand_document(file_bytes, mime_type, extracted_text)
    structured = _normalize_structured(provider_payload, extracted_text)
    retrieval_query = str((provider_payload or {}).get("retrieval_query") or _structured_query(structured, extracted_text))

    return {
        "doc_type": structured.get("document_type") or "unknown_document",
        "extracted_text": extracted_text,
        "retrieval_query": retrieval_query,
        "extracted_fields": structured,
        "origin": "user_document_extraction",
        "authoritative": False,
        "vision_error": None if provider_payload else "Qwen multimodal provider unavailable or returned no structured fields.",
        "fallback_used": provider_payload is None,
    }
