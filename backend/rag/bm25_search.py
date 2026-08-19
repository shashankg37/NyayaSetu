"""BM25 keyword search module.

Loads the saved BM25 pickle index and performs keyword search.
"""
from __future__ import annotations

import logging
from typing import Any

from backend.config import BM25_PATH
from backend.ai.knowledge_base.store import load_pickle
from backend.rag.ingestion.indexer import _tokenize

logger = logging.getLogger(__name__)


def search_bm25(query: str, top_k: int = 10) -> list[dict[str, Any]]:
    """Search the BM25 index for keyword matches.

    Args:
        query: The raw query string.
        top_k: Number of results to return.

    Returns:
        List of chunks with their BM25 scores.
    """
    if not BM25_PATH.exists():
        logger.warning("BM25 index not found at %s", BM25_PATH)
        return []

    try:
        data = load_pickle(BM25_PATH)
        if not data or not isinstance(data, dict):
            return []

        bm25 = data.get("bm25")
        chunk_ids = data.get("chunk_ids")
        records = data.get("records")

        if not bm25 or not chunk_ids or not records:
            return []

        tokenized_query = _tokenize(query)
        scores = bm25.get_scores(tokenized_query)

        # Get top K indices
        # Numpy argsort is faster but we avoid the dependency if possible
        indexed_scores = [(idx, score) for idx, score in enumerate(scores) if score > 0]
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        top_indices = indexed_scores[:top_k]

        results = []
        for idx, score in top_indices:
            record = dict(records[idx])
            record["score"] = float(score)
            results.append(record)

        return results
    except Exception as e:
        logger.error("BM25 search failed: %s", e)
        return []
