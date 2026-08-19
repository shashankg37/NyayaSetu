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

        model_name = SETTINGS.cross_encoder_model
        model = CrossEncoder(model_name)
        logger.info("Loaded cross-encoder: %s", model_name)
        return model
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
        for c, s in zip(candidates, normalized_scores):
            c["confidence"] = float(s)

        candidates.sort(key=lambda x: x.get("confidence", 0.0), reverse=True)
        return candidates[:top_k]

    except Exception as e:
        logger.error("Reranking failed: %s", e)
        return candidates[:top_k]
