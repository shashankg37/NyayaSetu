from __future__ import annotations

from io import BytesIO
from typing import Any
import base64
import mimetypes

from app.ai.ai_stubs.retrieval import retrieve


def _extract_pdf_text(file_bytes: bytes) -> str:
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(BytesIO(file_bytes))
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n".join(pages).strip()
    except Exception:
        return ""


def _extract_ocr_text(file_bytes: bytes) -> str:
    try:
        from PIL import Image  # type: ignore
        import pytesseract  # type: ignore

        image = Image.open(BytesIO(file_bytes))
        return pytesseract.image_to_string(image).strip()
    except Exception:
        return ""


def _gemini_vision(file_bytes: bytes, mime_type: str) -> dict[str, Any] | None:
    try:
        import google.generativeai as genai  # type: ignore
    except Exception:
        return None
    from app.ai.config import SETTINGS

    api_key = getattr(SETTINGS, "gemini_api_key", "")
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(SETTINGS.gemini_model)
    prompt = (
        "Extract structured legal document facts from the image or PDF. "
        "Return JSON with keys: document_type, parties, key_dates, deadline, issuer, extracted_text, "
        "retrieval_query, confidence. Do not invent missing facts."
    )
    try:
        part = {"mime_type": mime_type, "data": base64.b64encode(file_bytes).decode("ascii")}
        response = model.generate_content([prompt, part], generation_config={"response_mime_type": "application/json"})
        if getattr(response, "text", None):
            from app.ai.ai_stubs.common import safe_json_loads

            parsed = safe_json_loads(response.text)
            if isinstance(parsed, dict):
                return parsed
    except Exception:
        return None
    return None


def _heuristic_doc_type(text: str) -> str:
    lowered = text.lower()
    for doc_type, markers in {
        "eviction_notice": ["eviction", "vacate", "possession"],
        "employment_complaint": ["salary", "wages", "employer", "payment"],
        "legal_notice": ["notice", "demand", "breach", "reply within"],
        "rent_dispute": ["rent", "landlord", "tenant", "arrears"],
        "summons": ["summons", "court", "appearance"],
    }.items():
        if any(marker in lowered for marker in markers):
            return doc_type
    return "unknown_document"


def _heuristic_parties(text: str) -> list[str]:
    parties = []
    for marker in ["tenant", "landlord", "employer", "employee", "buyer", "seller", "complainant", "respondent"]:
        if marker in text.lower():
            parties.append(marker)
    return parties


def extract_document(file_bytes: bytes) -> dict[str, Any]:
    """Classifies the document type and extracts key facts: parties, dates, deadlines, clauses."""
    mime_type = "application/octet-stream"
    if file_bytes.startswith(b"%PDF"):
        mime_type = "application/pdf"
    else:
        kind = mimetypes.guess_type("document.png")[0]
        if kind:
            mime_type = kind

    extracted_text = ""
    if mime_type == "application/pdf":
        extracted_text = _extract_pdf_text(file_bytes)
    if not extracted_text:
        extracted_text = _extract_ocr_text(file_bytes)

    gemini_data = _gemini_vision(file_bytes, mime_type)
    if gemini_data:
        retrieval_query = " ".join(
            str(gemini_data.get(key, ""))
            for key in ["document_type", "parties", "key_dates", "deadline", "issuer", "extracted_text"]
        ).strip()
        if not retrieval_query:
            retrieval_query = extracted_text
        gemini_data["retrieval_query"] = retrieval_query
        gemini_data.setdefault("extracted_text", extracted_text)
        gemini_data["retrieved_chunks"] = retrieve(retrieval_query or extracted_text)
        gemini_data.setdefault("confidence", 0.75 if gemini_data.get("retrieved_chunks") else 0.0)
        gemini_data.setdefault("fallback_used", False)
        return gemini_data

    doc_type = _heuristic_doc_type(extracted_text)
    retrieval_query = " ".join(
        part for part in [doc_type, extracted_text[:800]] if part
    ).strip()
    result = {
        "document_type": doc_type,
        "parties": _heuristic_parties(extracted_text),
        "key_dates": [],
        "deadline": "",
        "issuer": "",
        "extracted_text": extracted_text,
        "retrieval_query": retrieval_query,
        "retrieved_chunks": retrieve(retrieval_query) if retrieval_query else [],
        "confidence": 0.35 if extracted_text else 0.0,
        "fallback_used": not bool(extracted_text),
    }
    return result

