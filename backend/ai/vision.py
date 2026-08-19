"""Qwen-VL document understanding with a non-authoritative extraction boundary."""
from __future__ import annotations

import base64
import logging
from io import BytesIO
from typing import Any

import requests

from backend.ai.llm import safe_json_loads
from backend.config import SETTINGS

logger = logging.getLogger(__name__)


def _extract_pdf_text(file_bytes: bytes) -> str:
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except Exception as exc:
        logger.error("PDF extraction failed: %s", exc)
        return ""


def _qwen_vision_extract(file_bytes: bytes, mime_type: str) -> dict[str, Any] | None:
    if not SETTINGS.hf_api_key:
        logger.warning("HF API key missing for vision extraction")
        return None
    prompt = (
        "Analyze this legal document image or scanned page. Extract JSON with keys: "
        "document_type, parties, dates, authorities, sections_mentioned, deadlines, "
        "clauses, important_facts. Do not invent missing fields; use empty lists or null. "
        "This extraction is not legal authority."
    )
    b64 = base64.b64encode(file_bytes).decode("ascii")
    try:
        from huggingface_hub import InferenceClient  # type: ignore

        client = InferenceClient(token=SETTINGS.hf_api_key)
        completion = client.chat.completions.create(
            model=SETTINGS.vision_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}},
                    ],
                }
            ],
            max_tokens=1000,
            temperature=0.1,
        )
        text = completion.choices[0].message.content or ""
        parsed = safe_json_loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception as exc:
        logger.info("HF vision client failed, trying HTTP: %s", exc)

    url = f"{SETTINGS.hf_api_url.rstrip('/')}/{SETTINGS.vision_model}"
    payload = {
        "inputs": {"text": prompt, "image": b64, "mime_type": mime_type},
        "parameters": {"max_new_tokens": 1000, "temperature": 0.1},
    }
    try:
        response = requests.post(
            url,
            headers={"Authorization": f"Bearer {SETTINGS.hf_api_key}"},
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        text = ""
        if isinstance(data, list) and data:
            text = str(data[0].get("generated_text") or data[0].get("text") or "")
        elif isinstance(data, dict):
            text = str(data.get("generated_text") or data.get("text") or "")
        parsed = safe_json_loads(text)
        return parsed if isinstance(parsed, dict) else None
    except Exception as exc:
        logger.error("Qwen-VL extraction failed: %s", exc)
        return None


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
    structured = None
    vision_error = None
    if SETTINGS.vision_provider == "hf":
        try:
            structured = _qwen_vision_extract(file_bytes, mime_type)
        except Exception as exc:  # noqa: BLE001
            vision_error = str(exc)
            logger.error("Qwen-VL path failed: %s", exc)

    if not structured:
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
