"""Language detection, intent classification, and slot utilities."""
from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import Any

from backend.config import SETTINGS

logger = logging.getLogger(__name__)

TOKEN_RE = re.compile(r"[a-zA-Z0-9]+", re.UNICODE)

INTENT_LABELS = {
    "legal_guidance",
    "legal_research",
    "document_understanding",
    "drafting",
    "lawyer_matching",
    "legal_awareness",
    "unsupported",
    "emergency",
}

DRAFT_TYPES = {
    "rti": ("rti", "right to information"),
    "wage_complaint": ("wage complaint", "salary complaint", "unpaid wages"),
    "consumer_complaint": ("consumer complaint", "consumer forum", "defective"),
    "government_grievance": ("grievance", "cpgrams", "pg portal"),
    "legal_notice": ("legal notice", "send a notice"),
}

REQUIRED_FIELDS = {
    "rti": ["applicant_name", "address", "public_authority", "information_sought"],
    "wage_complaint": ["worker_name", "employer_name", "period_unpaid", "amount", "work_place"],
    "consumer_complaint": ["complainant_name", "opposite_party", "goods_or_service", "grievance", "relief_sought"],
    "government_grievance": ["applicant_name", "department", "grievance", "location"],
    "legal_notice": ["sender_name", "recipient_name", "facts", "demand"],
}


def normalize_text(text: str) -> str:
    return " ".join((text or "").strip().split())


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text or "")]





def detect_language(text: str) -> str:
    return "en"


def detect_draft_type(text: str) -> str | None:
    lowered = text.lower()
    for doc_type, markers in DRAFT_TYPES.items():
        if any(marker in lowered for marker in markers):
            return doc_type
    return None


def classify_intent(text: str) -> str:
    lowered = text.lower()
    if any(marker in lowered for marker in ("kill myself", "suicide", "bomb", "terror", "shoot")):
        return "emergency"
    if any(marker in lowered for marker in ("find a lawyer", "need a lawyer", "legal aid lawyer", "advocate near")):
        return "lawyer_matching"
    if detect_draft_type(lowered):
        return "drafting"
    if any(marker in lowered for marker in ("research", "which section", "compare", "provision", "what does the act")):
        return "legal_research"
    if any(marker in lowered for marker in ("this document", "uploaded", "notice i received", "scan")):
        return "document_understanding"
    if any(marker in lowered for marker in ("how to", "procedure", "file", "steps", "where do i")):
        return "legal_guidance"
    if any(marker in lowered for marker in ("what are my rights", "is it legal", "can my employer", "landlord")):
        return "legal_awareness"
    if any(marker in lowered for marker in ("hack", "fake aadhaar", "evade tax fraudulently")):
        return "unsupported"
    return "legal_guidance"


def infer_legal_domain(text: str) -> str:
    lowered = text.lower()
    mapping = [
        ("labour", ("employer", "wage", "salary", "worker", "labour", "labor")),
        ("consumer", ("consumer", "refund", "defective", "product")),
        ("property", ("landlord", "tenant", "deposit", "rent", "evict")),
        ("women_and_children", ("domestic violence", "dowry", "child")),
        ("disability", ("disability", "pwd", "accessibility")),
        ("senior_citizens", ("senior citizen", "elderly", "parent maintenance")),
        ("government_services", ("rti", "ration", "pension", "aadhaar", "grievance")),
        ("criminal", ("fir", "police", "theft", "assault", "bail")),
        ("legal_aid", ("legal aid", "nalsa", "dlsa")),
    ]
    for domain, markers in mapping:
        if any(marker in lowered for marker in markers):
            return domain
    return "unknown"


def missing_fields(doc_type: str, known_fields: dict[str, Any]) -> list[str]:
    required = REQUIRED_FIELDS.get(doc_type.lower(), ["party_name", "details"])
    return [field for field in required if not str(known_fields.get(field) or "").strip()]


def followup_slots(domain: str, intent: str, collected: dict[str, Any]) -> list[str]:
    slots: list[str] = []
    if domain == "labour" and not collected.get("employment_type"):
        slots.append("employment_type")
    if domain == "property" and not collected.get("state"):
        slots.append("state")
    if intent == "drafting":
        return slots
    return slots


SLOT_QUESTIONS = {
    "employment_type": "Are you a permanent employee or a daily-wage worker?",
    "state": "What state are you in?",
}
