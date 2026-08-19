"""Main retriever pipeline orchestrating Qdrant, BM25, RRF, and CrossEncoder."""
from __future__ import annotations

import logging
from typing import Any

from backend.rag.bm25_search import search_bm25
from backend.rag.fusion import rrf_merge
from backend.rag.ingestion import embed_text
from backend.rag.qdrant_store import search_qdrant
from backend.rag.reranker import rerank

logger = logging.getLogger(__name__)


def retrieve(
    query: str,
    filters: dict[str, Any] | None = None,
    qdrant_k: int = 20,
    bm25_k: int = 20,
    fusion_k: int = 15,
    final_k: int = 5,
    rerank_candidates: bool = True,
) -> list[dict[str, Any]]:
    """Retrieve the most relevant legal chunks for a query."""
    logger.info("Retrieving evidence for query: '%s'", query)

    query_vector = embed_text(query)
    dense_results = search_qdrant(query_vector, top_k=qdrant_k, filters=filters)
    for item in dense_results:
        item["retrieval_source"] = "qdrant"
    sparse_results = search_bm25(query, top_k=bm25_k)
    fused_results = rrf_merge(dense_results, sparse_results, top_k=fusion_k)

    if not fused_results:
        return []
    if not rerank_candidates:
        return fused_results[:final_k]
    return rerank(query, fused_results, top_k=final_k)


def retrieve_ablation(
    query: str,
    mode: str,
    qdrant_k: int = 20,
    bm25_k: int = 20,
    fusion_k: int = 15,
    final_k: int = 5,
) -> list[dict[str, Any]]:
    """Run a named retrieval variant for evaluation."""
    query_vector = embed_text(query)
    dense = search_qdrant(query_vector, top_k=qdrant_k)
    for item in dense:
        item["retrieval_source"] = "qdrant"
    sparse = search_bm25(query, top_k=bm25_k)
    if mode == "qdrant":
        return dense[:final_k]
    if mode == "bm25":
        return sparse[:final_k]
    fused = rrf_merge(dense, sparse, top_k=fusion_k)
    if mode == "rrf":
        return fused[:final_k]
    return rerank(query, fused, top_k=final_k)
