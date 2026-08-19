"""Evidence gate to evaluate retrieval quality before generation."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from backend.config import SETTINGS

logger = logging.getLogger(__name__)

AUTHORITY_MARKERS = (
    "india code",
    "egazette",
    "gazette",
    "nalsa",
    "slsa",
    "dlsa",
    "ministry of law",
    "government of india",
    "act",
    "rules",
    "regulation",
    "official",
)


@dataclass
class EvidenceDecision:
    sufficient: bool
    confidence: float
    explanation: str
    authority_hits: int = 0
    agreement_hits: int = 0
    coverage: float = 0.0
    signals: dict[str, Any] = field(default_factory=dict)


def _is_authoritative(chunk: dict[str, Any]) -> bool:
    haystack = " ".join(
        str(chunk.get(key) or "")
        for key in ("source", "source_url", "document_name", "act", "section")
    ).lower()
    return any(marker in haystack for marker in AUTHORITY_MARKERS)


def evaluate_evidence(query: str, results: list[dict[str, Any]]) -> EvidenceDecision:
    """Evaluate whether retrieved chunks are sufficient to answer the query."""
    del query
    if not results:
        return EvidenceDecision(
            sufficient=False,
            confidence=0.0,
            explanation="No legal evidence found in the official knowledge base.",
        )

    top_score = float(results[0].get("confidence") or results[0].get("fusion_score") or 0.0)
    threshold = float(SETTINGS.confidence_threshold)
    authority_hits = sum(1 for item in results if _is_authoritative(item))
    agreement_hits = sum(
        1
        for item in results
        if "qdrant" in str(item.get("retrieval_sources", item.get("retrieval_source", "")))
        and "bm25" in str(item.get("retrieval_sources", item.get("retrieval_source", "")))
    )
    if agreement_hits == 0:
        agreement_hits = sum(1 for item in results if item.get("fusion_score") and item.get("retrieval_source") != "qdrant")
        sources = [str(item.get("retrieval_source", "")) for item in results]
        if "qdrant" in sources and "bm25" in sources:
            agreement_hits = max(agreement_hits, 1)

    coverage = min(1.0, (sum(float(item.get("confidence") or 0.0) for item in results) / max(len(results), 1)))
    min_chunks = int(SETTINGS.evidence_min_chunks)
    min_authority = int(SETTINGS.evidence_min_authority)
    min_agreement = int(SETTINGS.evidence_min_agreement)
    min_coverage = float(SETTINGS.evidence_coverage_min)

    sufficient = (
        len(results) >= min_chunks
        and top_score >= threshold
        and authority_hits >= min_authority
        and (agreement_hits >= min_agreement or top_score >= max(threshold, 0.7))
        and coverage >= min_coverage
    )
    explanation = (
        f"chunks={len(results)}; cross_encoder={top_score:.3f}; "
        f"authority={authority_hits}; agreement={agreement_hits}; coverage={coverage:.3f}"
    )
    if not sufficient:
        logger.warning("Evidence rejected: %s", explanation)
        return EvidenceDecision(
            sufficient=False,
            confidence=top_score,
            explanation=f"Insufficient authoritative evidence ({explanation}).",
            authority_hits=authority_hits,
            agreement_hits=agreement_hits,
            coverage=coverage,
            signals={"threshold": threshold},
        )

    logger.info("Evidence accepted: %s", explanation)
    return EvidenceDecision(
        sufficient=True,
        confidence=top_score,
        explanation=explanation,
        authority_hits=authority_hits,
        agreement_hits=agreement_hits,
        coverage=coverage,
        signals={"threshold": threshold},
    )
