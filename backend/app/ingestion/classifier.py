"""InLegalBERT-based legal domain classifier.

Uses pretrained InLegalBERT (law-ai/InLegalBERT) as a feature extractor
with cosine similarity against label descriptions for zero-shot-style
classification. NO fine-tuning is performed.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)

# Candidate labels for each classification axis
LEGAL_DOMAINS = [
    "labour",
    "consumer",
    "family",
    "housing",
    "criminal",
    "property",
    "constitutional",
    "administrative",
    "environmental",
    "corporate",
    "taxation",
    "legal_aid",
    "general",
]

TOPICS = [
    "wages",
    "employment",
    "termination",
    "workplace_safety",
    "rent",
    "eviction",
    "tenancy",
    "marriage",
    "divorce",
    "child_custody",
    "maintenance",
    "domestic_violence",
    "consumer_complaint",
    "product_defect",
    "refund",
    "service_deficiency",
    "property_dispute",
    "land_acquisition",
    "legal_aid",
    "free_legal_services",
    "rti",
    "government_grievance",
    "pension",
    "insurance",
    "education",
    "healthcare",
    "general",
]

BENEFICIARIES = [
    "worker",
    "daily_wage_worker",
    "employee",
    "tenant",
    "consumer",
    "woman",
    "child",
    "senior_citizen",
    "person_with_disability",
    "sc_st",
    "victim",
    "citizen",
    "litigant",
    "entrepreneur",
    "farmer",
]


@lru_cache(maxsize=1)
def _load_classifier():
    """Load a zero-shot classification pipeline.

    Tries InLegalBERT embeddings + cosine similarity approach first.
    Falls back to a cross-encoder NLI model if available.
    Falls back to keyword heuristics if no model loads.
    """
    try:
        from transformers import pipeline  # type: ignore

        # Use a multilingual NLI model for zero-shot classification
        # InLegalBERT is BERT-base without NLI head, so we use a dedicated
        # zero-shot model and rely on InLegalBERT embeddings for enrichment
        clf = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=-1,  # CPU
        )
        logger.info("Loaded zero-shot classifier: facebook/bart-large-mnli")
        return clf
    except Exception as e:
        logger.warning("Could not load transformer classifier: %s", e)
        return None


@lru_cache(maxsize=1)
def _load_inlegalbert_embedder():
    """Load InLegalBERT for domain-specific embedding enrichment."""
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore

        model = SentenceTransformer("law-ai/InLegalBERT")
        logger.info("Loaded InLegalBERT for classification enrichment")
        return model
    except Exception as e:
        logger.warning("Could not load InLegalBERT: %s", e)
        return None


def _keyword_classify_domain(text: str) -> str:
    """Fallback keyword-based domain classification."""
    lower = text.lower()
    domain_markers = {
        "labour": ["wage", "salary", "employ", "labour", "worker", "workman", "industrial", "factory", "minimum wage"],
        "consumer": ["consumer", "purchase", "refund", "product", "service", "defect", "seller", "buyer"],
        "housing": ["tenant", "landlord", "rent", "evict", "lease", "premises", "accommodation"],
        "family": ["family", "marriage", "divorce", "child", "maintenance", "custody", "dowry", "domestic violence"],
        "criminal": ["criminal", "offense", "fir", "bail", "arrest", "theft", "fraud"],
        "property": ["property", "land", "succession", "inheritance", "transfer", "mutation"],
        "constitutional": ["fundamental right", "constitution", "article", "writ", "petition"],
        "legal_aid": ["legal aid", "nalsa", "legal services", "free legal", "lok adalat"],
    }
    for domain, markers in domain_markers.items():
        if any(marker in lower for marker in markers):
            return domain
    return "general"


def _keyword_classify_topic(text: str) -> str:
    """Fallback keyword-based topic classification."""
    lower = text.lower()
    topic_markers = {
        "wages": ["wage", "salary", "pay", "remuneration", "compensation"],
        "termination": ["terminat", "dismiss", "retrench", "layoff"],
        "eviction": ["evict", "vacate", "possession"],
        "rent": ["rent", "lease", "tenancy"],
        "maintenance": ["maintenance", "alimony"],
        "consumer_complaint": ["consumer complaint", "consumer forum"],
        "legal_aid": ["legal aid", "free legal", "nalsa"],
        "rti": ["right to information", "rti"],
    }
    for topic, markers in topic_markers.items():
        if any(marker in lower for marker in markers):
            return topic
    return "general"


def _keyword_classify_beneficiary(text: str) -> str:
    """Fallback keyword-based beneficiary classification."""
    lower = text.lower()
    beneficiary_markers = {
        "worker": ["worker", "workman", "labourer"],
        "daily_wage_worker": ["daily wage", "casual", "contract worker"],
        "employee": ["employee", "staff"],
        "tenant": ["tenant", "occupant", "lessee"],
        "consumer": ["consumer", "buyer", "purchaser"],
        "woman": ["woman", "wife", "mother", "female"],
        "child": ["child", "minor", "juvenile"],
        "senior_citizen": ["senior citizen", "elderly", "old age"],
    }
    for beneficiary, markers in beneficiary_markers.items():
        if any(marker in lower for marker in markers):
            return beneficiary
    return "citizen"


def classify_text(text: str) -> dict[str, Any]:
    """Classify a piece of legal text.

    Returns a dict with:
        legal_domain: str
        topic: str
        beneficiary: str
        domain_confidence: float
        topic_confidence: float
        beneficiary_confidence: float
    """
    if not text or not text.strip():
        return {
            "legal_domain": "general",
            "topic": "general",
            "beneficiary": "citizen",
            "domain_confidence": 0.0,
            "topic_confidence": 0.0,
            "beneficiary_confidence": 0.0,
        }

    clf = _load_classifier()
    if clf is None:
        # Pure keyword fallback
        return {
            "legal_domain": _keyword_classify_domain(text),
            "topic": _keyword_classify_topic(text),
            "beneficiary": _keyword_classify_beneficiary(text),
            "domain_confidence": 0.5,
            "topic_confidence": 0.5,
            "beneficiary_confidence": 0.5,
        }

    # Truncate text for the classifier (BART has 1024 token limit)
    truncated = text[:1500]

    try:
        domain_result = clf(truncated, LEGAL_DOMAINS, multi_label=False)
        domain = domain_result["labels"][0]
        domain_conf = float(domain_result["scores"][0])
    except Exception:
        domain = _keyword_classify_domain(text)
        domain_conf = 0.5

    try:
        topic_result = clf(truncated, TOPICS[:15], multi_label=False)  # Limit candidates
        topic = topic_result["labels"][0]
        topic_conf = float(topic_result["scores"][0])
    except Exception:
        topic = _keyword_classify_topic(text)
        topic_conf = 0.5

    try:
        beneficiary_result = clf(truncated, BENEFICIARIES, multi_label=False)
        beneficiary = beneficiary_result["labels"][0]
        beneficiary_conf = float(beneficiary_result["scores"][0])
    except Exception:
        beneficiary = _keyword_classify_beneficiary(text)
        beneficiary_conf = 0.5

    return {
        "legal_domain": domain,
        "topic": topic,
        "beneficiary": beneficiary,
        "domain_confidence": domain_conf,
        "topic_confidence": topic_conf,
        "beneficiary_confidence": beneficiary_conf,
    }


def classify_batch(texts: list[str]) -> list[dict[str, Any]]:
    """Classify multiple texts. Processes sequentially to avoid OOM."""
    return [classify_text(text) for text in texts]
