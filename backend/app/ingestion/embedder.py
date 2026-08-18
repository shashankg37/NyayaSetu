"""Embedding module using multilingual Sentence Transformers.

Uses paraphrase-multilingual-MiniLM-L12-v2 (or configured model) for both
ingestion and query-time embedding.  This is the SINGLE source of truth
for the embedding model — no other module should instantiate its own.
"""
from __future__ import annotations

import logging
import math
from functools import lru_cache

from app.ai.config import SETTINGS

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_model():
    """Load the sentence transformer model (cached singleton)."""
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore

        model = SentenceTransformer(SETTINGS.embedding_model)
        logger.info("Loaded embedding model: %s", SETTINGS.embedding_model)
        return model
    except Exception as e:
        logger.warning("Could not load SentenceTransformer: %s. Using fallback.", e)
        return None


def _simple_embedding(text: str, dimensions: int = 384) -> list[float]:
    """Deterministic hash-based fallback embedding when model is unavailable."""
    vector = [0.0] * dimensions
    tokens = text.lower().split()
    for token in tokens:
        vector[hash(token) % dimensions] += 1.0
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


def embed_text(text: str) -> list[float]:
    """Embed a single text string.

    Returns a normalized vector suitable for cosine similarity.
    """
    model = _load_model()
    if model is not None:
        try:
            vector = model.encode([text], normalize_embeddings=True)[0]
            return vector.tolist() if hasattr(vector, "tolist") else list(vector)
        except Exception as e:
            logger.warning("Embedding failed for text: %s", e)

    return _simple_embedding(text)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed multiple texts as a batch.

    More efficient than calling embed_text() in a loop.
    """
    if not texts:
        return []

    model = _load_model()
    if model is not None:
        try:
            vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
            return [v.tolist() if hasattr(v, "tolist") else list(v) for v in vectors]
        except Exception as e:
            logger.warning("Batch embedding failed: %s", e)

    return [_simple_embedding(text) for text in texts]


def get_embedding_dimension() -> int:
    """Return the vector dimensionality of the current embedding model."""
    model = _load_model()
    if model is not None:
        try:
            dim = model.get_sentence_embedding_dimension()
            return int(dim) if dim else 384
        except Exception:
            pass
    return 384
