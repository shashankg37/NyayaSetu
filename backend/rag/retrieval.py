"""Main retriever pipeline orchestrating Qdrant, BM25, RRF, and CrossEncoder."""
from __future__ import annotations

import logging
from typing import Any

from backend.rag.ingestion.embedder import embed_text
from backend.rag.bm25_search import search_bm25
from backend.rag.fusion import rrf_merge
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
) -> list[dict[str, Any]]:
    """Retrieve the most relevant legal chunks for a query.

    Pipeline:
    1. Embed query
    2. Search Qdrant (dense)
    3. Search BM25 (sparse/keyword)
    4. Reciprocal Rank Fusion (RRF)
    5. CrossEncoder Reranking

    Args:
        query: The user's query string.
        filters: Optional metadata filters for Qdrant.
        qdrant_k: Num results from Qdrant.
        bm25_k: Num results from BM25.
        fusion_k: Num results to keep after RRF.
        final_k: Num results to return after reranking.

    Returns:
        List of reranked chunk dictionaries.
    """
    logger.info("Retrieving evidence for query: '%s'", query)

    # 1. Embed Query
    query_vector = embed_text(query)

    # 2. Qdrant Semantic Search
    dense_results = search_qdrant(query_vector, top_k=qdrant_k, filters=filters)
    logger.debug("Qdrant returned %d results", len(dense_results))

    # 3. BM25 Keyword Search
    # TODO: BM25 doesn't currently apply metadata filters. We rely on Qdrant
    # for strict filtering and RRF to combine.
    sparse_results = search_bm25(query, top_k=bm25_k)
    logger.debug("BM25 returned %d results", len(sparse_results))

    # 4. RRF Merge
    fused_results = rrf_merge(dense_results, sparse_results, top_k=fusion_k)
    logger.debug("RRF fused into %d results", len(fused_results))

    if not fused_results:
        return []

    # 5. CrossEncoder Rerank
    final_results = rerank(query, fused_results, top_k=final_k)
    logger.info("Returning %d reranked results", len(final_results))

    return final_results
