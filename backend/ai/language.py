"""Language detection, intent classification, and text utilities for NyayaSetu."""
from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import Any

from backend.config import SETTINGS

logger = logging.getLogger(__name__)

TOKEN_RE = re.compile(r"[a-zA-Z0-9]+", re.UNICODE)


def normalize_text(text: str) -> str:
    """Normalize text by stripping and reducing whitespace."""
    return " ".join(text.strip().split())


def tokenize(text: str) -> list[str]:
    """Tokenize text into alphanumeric lowercase words."""
    return [token.lower() for token in TOKEN_RE.findall(text)]


@lru_cache(maxsize=1)
def _load_fasttext_model():
    """Load the FastText language ID model."""
    import fasttext  # type: ignore

    try:
        model = fasttext.load_model(str(SETTINGS.fasttext_langid_model))
        logger.info("Loaded FastText model from %s", SETTINGS.fasttext_langid_model)
        return model
    except Exception as e:
        logger.warning("Failed to load FastText model: %s", e)
        return None


def detect_language(text: str) -> str:
    """Detect the language code of the given text (e.g., 'en', 'hi', 'ta').

    Falls back to 'en' if detection fails or model is unavailable.
    """
    if not text or not text.strip():
        return "en"

    model = _load_fasttext_model()
    if not model:
        return "en"

    try:
        # FastText expects single line text
        clean_text = text.replace("\n", " ").strip()
        predictions = model.predict(clean_text, k=1)
        label = predictions[0][0]
        # Label format is '__label__en'
        lang_code = label.replace("__label__", "")
        return lang_code
    except Exception as e:
        logger.warning("Language detection failed: %s", e)
        return "en"


def classify_intent(text: str) -> str:
    """Classify the user's intent from text."""
    lowered = text.lower()
    draft_markers = {
        "draft", "notice", "petition", "complaint", 
        "application", "reply", "legal notice", "agreement", "affidavit",
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


def missing_fields(doc_type: str, known_fields: dict[str, Any]) -> list[str]:
    """Return a list of missing fields required to draft doc_type."""
    doc_type = doc_type.lower()
    required: list[str] = []
    if "notice" in doc_type:
        required = ["sender_name", "recipient_name", "date_of_incident", "demand"]
    elif "complaint" in doc_type or "fir" in doc_type:
        required = ["complainant_name", "accused_name", "incident_details", "date_of_incident", "police_station"]
    elif "petition" in doc_type:
        required = ["petitioner_name", "respondent_name", "court_name", "grounds"]
    elif "agreement" in doc_type or "contract" in doc_type:
        required = ["party_one", "party_two", "terms", "date_of_execution"]
    else:
        required = ["party_name", "details"]

    missing = [field for field in required if not known_fields.get(field)]
    return missing
