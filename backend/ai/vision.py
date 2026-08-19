"""Multimodal document extraction pipeline using Qwen Vision.

Extracts text from PDFs/images, parses structured facts, and formats
them for hybrid retrieval.
"""
from __future__ import annotations

import base64
import logging
from io import BytesIO
from typing import Any

import requests

from backend.ai.llm import safe_json_loads
from backend.config import SETTINGS
from backend.rag.retrieval import retrieve

logger = logging.getLogger(__name__)


def _extract_pdf_text(file_bytes: bytes) -> str:
    """Extract text from PDF using pypdf."""
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except ImportError:
        logger.warning("pypdf not installed")
        return ""
    except Exception as e:
        logger.error("PDF extraction failed: %s", e)
        return ""


def _extract_ocr_text(file_bytes: bytes) -> str:
    """Extract text from images using pytesseract."""
    try:
        from PIL import Image  # type: ignore
        import pytesseract  # type: ignore

        image = Image.open(BytesIO(file_bytes))
        return pytesseract.image_to_string(image).strip()
    except ImportError:
        logger.warning("PIL or pytesseract not installed")
        return ""
    except Exception as e:
        logger.error("OCR extraction failed: %s", e)
        return ""


def _qwen_vision_extract(file_bytes: bytes, mime_type: str) -> dict[str, Any] | None:
    """Extract structured facts using Qwen Vision model via HF Inference API."""
    if not SETTINGS.hf_api_key:
        logger.warning("HF API key missing for vision extraction")
        return None
        
    url = f"{SETTINGS.hf_api_url.rstrip('/')}/{SETTINGS.vision_model}"
    headers = {
        "Authorization": f"Bearer {SETTINGS.hf_api_key}",
        "Content-Type": "application/json"
    }
    
    prompt = (
        "Analyze this legal document image/PDF and extract the following information as a JSON object: "
        "document_type (e.g., Notice, Contract, Summons), "
        "parties (list of people or entities involved), "
        "key_dates (list of important dates mentioned), "
        "deadline (any deadline specified), "
        "issuer (who issued the document), "
        "relevant_facts (brief summary of what the document says), "
        "cited_provisions (any laws or sections mentioned). "
        "Do not invent facts. Return ONLY valid JSON."
    )
    
    payload = {
        "inputs": {
            "text": prompt,
            "image": base64.b64encode(file_bytes).decode("ascii"),
            "mime_type": mime_type,
        },
        "parameters": {
            "max_new_tokens": 1000,
            "temperature": 0.1
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        
        text = ""
        if isinstance(data, list) and data:
            text = str(data[0].get("generated_text") or data[0].get("text") or "")
        elif isinstance(data, dict):
            text = str(data.get("generated_text") or data.get("text") or "")
            
        if text:
            parsed = safe_json_loads(text)
            if isinstance(parsed, dict):
                return parsed
                
    except Exception as e:
        logger.error("Qwen Vision extraction failed: %s", e)
        
    return None


def _heuristic_doc_type(text: str) -> str:
    """Fallback doc type detection."""
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
    """Fallback party detection."""
    parties = []
    for marker in ["tenant", "landlord", "employer", "employee", "buyer", "seller", "complainant", "respondent"]:
        if marker in text.lower():
            parties.append(marker)
    return parties


def extract_document(file_bytes: bytes) -> dict[str, Any]:
    """Main pipeline for document extraction.
    
    1. Extract raw text via PyPDF or OCR
    2. Extract structured fields via Qwen Vision
    3. Generate retrieval query based on facts
    4. Pass to hybrid RAG
    """
    logger.info("Starting document extraction")
    
    # Detect mime type
    mime_type = "application/octet-stream"
    if file_bytes.startswith(b"%PDF"):
        mime_type = "application/pdf"
    elif file_bytes.startswith(b"\xFF\xD8"):
        mime_type = "image/jpeg"
    elif file_bytes.startswith(b"\x89PNG"):
        mime_type = "image/png"

    # Step 1: Raw text extraction
    extracted_text = _extract_pdf_text(file_bytes) if mime_type == "application/pdf" else ""
    if not extracted_text:
        extracted_text = _extract_ocr_text(file_bytes)

    # Step 2: Vision model extraction
    structured_data = None
    if SETTINGS.vision_provider == "hf":
        structured_data = _qwen_vision_extract(file_bytes, mime_type)
        
    # If vision model failed, use heuristics
    if not structured_data:
        logger.info("Vision model failed, using heuristics")
        doc_type = _heuristic_doc_type(extracted_text)
        structured_data = {
            "document_type": doc_type,
            "parties": _heuristic_parties(extracted_text),
            "key_dates": [],
            "deadline": "",
            "issuer": "",
            "relevant_facts": extracted_text[:500],
            "cited_provisions": []
        }

    # Step 3: Generate retrieval query
    retrieval_parts = []
    if structured_data.get("document_type"):
        retrieval_parts.append(str(structured_data["document_type"]))
    if structured_data.get("relevant_facts"):
        retrieval_parts.append(str(structured_data["relevant_facts"]))
    elif extracted_text:
        retrieval_parts.append(extracted_text[:500])
        
    retrieval_query = " ".join(retrieval_parts).strip()

    # Form final response object
    result = {
        "doc_type": structured_data.get("document_type", "unknown_document"),
        "extracted_text": extracted_text,
        "retrieval_query": retrieval_query,
        "extracted_fields": {
            "parties": structured_data.get("parties", []),
            "key_dates": structured_data.get("key_dates", []),
            "deadline": structured_data.get("deadline", ""),
            "issuer": structured_data.get("issuer", ""),
            "cited_provisions": structured_data.get("cited_provisions", []),
            "summary": structured_data.get("relevant_facts", extracted_text[:500]),
        },
        "fallback_used": not bool(extracted_text) and not structured_data.get("relevant_facts"),
    }
    
    # Step 4: Retrieve evidence based on document contents
    if retrieval_query:
        logger.info("Retrieving evidence for document query: %s", retrieval_query[:50])
        result["retrieved_chunks"] = retrieve(retrieval_query)
        result["confidence"] = 0.8 if result["retrieved_chunks"] else 0.4
    else:
        result["retrieved_chunks"] = []
        result["confidence"] = 0.0
        
    return result
