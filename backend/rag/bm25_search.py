"""BM25 keyword search.

Works from the on-disk pickle index or from an in-memory record list.
Independent of Qdrant.
"""
from __future__ import annotations

import logging
from typing import Any

from backend.config import BM25_PATH
from backend.rag.ingestion import _tokenize
from backend.rag.store import load_pickle

logger = logging.getLogger(__name__)


def rank_bm25(query: str, records: list[dict[str, Any]], top_k: int = 10) -> list[dict[str, Any]]:
    """Rank an in-memory list of chunks with BM25. Does not use Qdrant."""
    try:
        from rank_bm25 import BM25Okapi  # type: ignore
    except ImportError:
        logger.error("rank_bm25 is not installed")
        return []
    if not query.strip() or not records:
        return []
    corpus = []
    for record in records:
        text = " ".join(
            part
            for part in [
                record.get("original_text", ""),
                record.get("section", ""),
                record.get("topic", ""),
                record.get("act", ""),
            ]
            if part
        )
        corpus.append(_tokenize(text))
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(_tokenize(query))
    indexed = [(idx, float(score)) for idx, score in enumerate(scores) if score > 0]
    indexed.sort(key=lambda item: (-item[1], str(records[item[0]].get("chunk_id", ""))))
    results = []
    for idx, score in indexed[:top_k]:
        record = dict(records[idx])
        record["score"] = score
        record["retrieval_source"] = "bm25"
        results.append(record)
    return results


def search_bm25(query: str, top_k: int = 10) -> list[dict[str, Any]]:
    """Search the saved BM25 index for keyword matches."""
    if not BM25_PATH.exists():
        logger.warning("BM25 index not found at %s", BM25_PATH)
        return []
    try:
        data = load_pickle(BM25_PATH)
        if not data or not isinstance(data, dict):
            return []
        records = data.get("records") or []
        bm25 = data.get("bm25")
        if bm25 is not None and records:
            scores = bm25.get_scores(_tokenize(query))
            indexed = [(idx, float(score)) for idx, score in enumerate(scores) if score > 0]
            indexed.sort(key=lambda item: (-item[1], str(records[item[0]].get("chunk_id", ""))))
            results = []
            for idx, score in indexed[:top_k]:
                record = dict(records[idx])
                record["score"] = score
                record["retrieval_source"] = "bm25"
                results.append(record)
            return results
        return rank_bm25(query, records, top_k=top_k)
    except Exception as e:
        logger.error("BM25 search failed: %s", e)
        return []
