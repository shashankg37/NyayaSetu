"""Non-authoritative user-document extraction (text/PDF only; no vision model)."""
from __future__ import annotations

import logging
from io import BytesIO
from typing import Any

logger = logging.getLogger(__name__)


def _extract_pdf_text(file_bytes: bytes) -> str:
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except Exception as exc:
        logger.error("PDF extraction failed: %s", exc)
        return ""


def extract_document(file_bytes: bytes) -> dict[str, Any]:
    mime_type = "application/octet-stream"
    if file_bytes.startswith(b"%PDF"):
        mime_type = "application/pdf"
    elif file_bytes.startswith(b"\xff\xd8"):
        mime_type = "image/jpeg"
    elif file_bytes.startswith(b"\x89PNG"):
        mime_type = "image/png"
    elif file_bytes.startswith(b"RIFF"):
        mime_type = "image/webp"

    extracted_text = _extract_pdf_text(file_bytes) if mime_type == "application/pdf" else ""
    vision_error = None
    structured = {
        "document_type": "unknown_document",
        "parties": [],
        "dates": [],
        "authorities": [],
        "sections_mentioned": [],
        "deadlines": [],
        "clauses": [],
        "important_facts": extracted_text[:800] if extracted_text else "",
    }

    retrieval_query = " ".join(
        part
        for part in [
            str(structured.get("document_type") or ""),
            " ".join(structured.get("sections_mentioned") or []),
            str(structured.get("important_facts") or extracted_text[:500]),
        ]
        if part
    ).strip()

    return {
        "doc_type": structured.get("document_type") or "unknown_document",
        "extracted_text": extracted_text,
        "retrieval_query": retrieval_query,
        "extracted_fields": structured,
        "origin": "user_document_extraction",
        "authoritative": False,
        "vision_error": vision_error,
        "fallback_used": structured.get("document_type") == "unknown_document" and not extracted_text,
    }
