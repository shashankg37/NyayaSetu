"""CrossEncoder reranking module."""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from backend.config import SETTINGS

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_cross_encoder():
    """Load the configured CrossEncoder model (cached singleton)."""
    try:
        from sentence_transformers import CrossEncoder  # type: ignore

        model_name = SETTINGS.cross_encoder_model
        model = CrossEncoder(model_name)
        logger.info("Loaded cross-encoder: %s", model_name)
        return model
    except Exception as e:
        logger.warning("Could not load CrossEncoder %s: %s", SETTINGS.cross_encoder_model, e)
        return None


def rerank(query: str, candidates: list[dict[str, Any]], top_k: int = 5) -> list[dict[str, Any]]:
    """Rerank RRF candidates using the configured CrossEncoder."""
    if not candidates:
        return []

    model = _load_cross_encoder()
    if model is None:
        ranked = [dict(item) for item in candidates[:top_k]]
        for item in ranked:
            item.setdefault("confidence", float(item.get("fusion_score") or item.get("score") or 0.0))
            item.setdefault("rerank_score", item["confidence"])
        return ranked

    pairs = []
    for candidate in candidates:
        text = " ".join(
            part
            for part in [
                candidate.get("act", ""),
                candidate.get("section", ""),
                candidate.get("original_text", ""),
                candidate.get("simplified_text", ""),
            ]
            if part
        )
        pairs.append((query, text))

    try:
        scores = model.predict(pairs)
        import math

        normalized_scores = [1.0 / (1.0 + math.exp(-float(score))) for score in scores]
        ranked = [dict(candidate) for candidate in candidates]
        for item, score in zip(ranked, normalized_scores):
            item["confidence"] = float(score)
            item["rerank_score"] = float(score)
        ranked.sort(key=lambda item: (-float(item.get("confidence", 0.0)), str(item.get("chunk_id", ""))))
        return ranked[:top_k]
    except Exception as e:
        logger.error("Reranking failed: %s", e)
        return candidates[:top_k]
