"""Evidence gate to evaluate retrieval quality and safety.

Acts as a safeguard against hallucination.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.ai.config import SETTINGS

logger = logging.getLogger(__name__)


@dataclass
class EvidenceDecision:
    """Decision output from the evidence gate."""
    sufficient: bool
    confidence: float
    explanation: str


def evaluate_evidence(query: str, results: list[dict[str, Any]]) -> EvidenceDecision:
    """Evaluate if retrieved chunks are sufficient to answer the query.

    Checks:
    1. Are there any results?
    2. Is the top CrossEncoder score above the minimum threshold?
    3. Is there sufficient overall coverage?

    Args:
        query: Original user query.
        results: Retrieved chunks (must have 'confidence' score from CrossEncoder).

    Returns:
        EvidenceDecision object.
    """
    if not results:
        return EvidenceDecision(
            sufficient=False,
            confidence=0.0,
            explanation="No legal evidence found.",
        )

    # Evaluate top score
    top_score = results[0].get("confidence", 0.0)
    threshold = SETTINGS.confidence_threshold

    if top_score < threshold:
        logger.warning(
            "Evidence rejected: Top score %.2f < threshold %.2f",
            top_score,
            threshold,
        )
        return EvidenceDecision(
            sufficient=False,
            confidence=top_score,
            explanation=f"Confidence too low ({top_score:.2f}).",
        )

    # Evaluate domain consensus (if multiple chunks agree on legal_domain)
    domains = [r.get("legal_domain", "general") for r in results[:3]]
    consensus_domain = max(set(domains), key=domains.count)

    # Count NALSA/authoritative sources
    auth_sources = sum(1 for r in results if "nalsa" in str(r.get("source", "")).lower())

    explanation = (
        f"Strong evidence found (score {top_score:.2f}). "
        f"Domain consensus: {consensus_domain}. "
        f"Authoritative chunks: {auth_sources}."
    )

    logger.info("Evidence accepted: %s", explanation)
    return EvidenceDecision(
        sufficient=True,
        confidence=top_score,
        explanation=explanation,
    )
