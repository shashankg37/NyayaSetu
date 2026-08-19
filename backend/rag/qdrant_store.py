"""Qdrant semantic search wrapper.

Interacts directly with Qdrant client to perform vector search.
"""
from __future__ import annotations

import logging
from typing import Any

from backend.config import SETTINGS

logger = logging.getLogger(__name__)


def search_qdrant(
    query_vector: list[float],
    top_k: int = 10,
    filters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Search Qdrant for semantically similar chunks.

    Args:
        query_vector: The embedded query vector.
        top_k: Number of results to return.
        filters: Optional payload filters (e.g. {"legal_domain": "labour"}).

    Returns:
        List of chunks with their scores.
    """
    try:
        from qdrant_client import QdrantClient  # type: ignore
        from qdrant_client.http import models as rest  # type: ignore
    except ImportError:
        logger.error("qdrant_client is not installed")
        return []

    client = QdrantClient(url=SETTINGS.qdrant_url, timeout=10)
    collection = SETTINGS.qdrant_collection

    if not client.collection_exists(collection):
        logger.warning("Qdrant collection '%s' does not exist", collection)
        return []

    # Build filter conditions
    qdrant_filter = None
    if filters:
        conditions = []
        for key, value in filters.items():
            if isinstance(value, list):
                conditions.append(
                    rest.FieldCondition(
                        key=key,
                        match=rest.MatchAny(any=value),
                    )
                )
            else:
                conditions.append(
                    rest.FieldCondition(
                        key=key,
                        match=rest.MatchValue(value=value),
                    )
                )
        if conditions:
            qdrant_filter = rest.Filter(must=conditions)

    try:
        results = client.search(
            collection_name=collection,
            query_vector=query_vector,
            query_filter=qdrant_filter,
            limit=top_k,
            with_payload=True,
        )

        return [
            {
                "score": float(res.score),
                **res.payload,
            }
            for res in results
            if res.payload
        ]
    except Exception as e:
        logger.error("Qdrant search failed: %s", e)
        return []
