"""CrossEncoder reranking module."""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from backend.config import SETTINGS

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_cross_encoder():
    """Load the CrossEncoder model (cached singleton)."""
    try:
        from sentence_transformers import CrossEncoder  # type: ignore

        candidates = [SETTINGS.cross_encoder_model, "cross-encoder/ms-marco-MiniLM-L-6-v2"]
        last_error: Exception | None = None
        for model_name in candidates:
            try:
                model = CrossEncoder(model_name)
                logger.info("Loaded cross-encoder: %s", model_name)
                return model
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.warning("Could not load CrossEncoder %s: %s", model_name, exc)
        logger.warning("Could not load any CrossEncoder: %s", last_error)
        return None
    except Exception as e:
        logger.warning("Could not load CrossEncoder: %s", e)
        return None


def rerank(query: str, candidates: list[dict[str, Any]], top_k: int = 5) -> list[dict[str, Any]]:
    """Rerank candidates using a CrossEncoder.

    Args:
        query: The user's query.
        candidates: The list of candidate chunks.
        top_k: Number of top reranked results to return.

    Returns:
        Reranked list of chunks with updated scores.
    """
    if not candidates:
        return []

    model = _load_cross_encoder()
    if model is None:
        # Fallback: just return the top_k as-is
        return candidates[:top_k]

    # Build pairs of (query, candidate_text)
    pairs = []
    for c in candidates:
        text = " ".join(
            part
            for part in [
                c.get("act", ""),
                c.get("section", ""),
                c.get("original_text", ""),
                c.get("simplified_text", ""),
            ]
            if part
        )
        pairs.append((query, text))

    try:
        scores = model.predict(pairs)

        # Apply sigmoid to normalize to 0-1 range
        import math

        normalized_scores = [1.0 / (1.0 + math.exp(-s)) for s in scores]

        # Attach scores and sort
        ranked = [dict(c) for c in candidates]
        for item, score in zip(ranked, normalized_scores):
            item["confidence"] = float(score)
            item["rerank_score"] = float(score)
        ranked.sort(key=lambda x: x.get("confidence", 0.0), reverse=True)
        return ranked[:top_k]

    except Exception as e:
        logger.error("Reranking failed: %s", e)
        return candidates[:top_k]
