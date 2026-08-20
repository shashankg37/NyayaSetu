"""Qdrant semantic search and collection helpers.

Interacts directly with the Qdrant client. This is the only vector store.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from backend.config import SETTINGS

# paraphrase-multilingual-MiniLM-L12-v2
DEFAULT_VECTOR_SIZE = 384

logger = logging.getLogger(__name__)


def get_qdrant_client(timeout: int = 10):
    from qdrant_client import QdrantClient  # type: ignore

    return QdrantClient(url=SETTINGS.qdrant_url, timeout=timeout)


def ping_qdrant(timeout: int = 3) -> bool:
    try:
        client = get_qdrant_client(timeout=timeout)
        client.get_collections()
        return True
    except Exception as exc:
        logger.warning("Qdrant is unavailable: %s", exc)
        return False


def collection_exists(collection: str | None = None) -> bool:
    name = collection or SETTINGS.qdrant_collection
    try:
        return bool(get_qdrant_client().collection_exists(name))
    except Exception:
        return False


def ensure_collection(vector_size: int | None = None, recreate: bool = False) -> int:
    """Create the configured collection if missing. Returns the vector size used."""
    from qdrant_client.http import models as rest  # type: ignore

    dim = int(vector_size or DEFAULT_VECTOR_SIZE)
    client = get_qdrant_client(timeout=60)
    collection = SETTINGS.qdrant_collection
    if recreate:
        try:
            client.delete_collection(collection)
        except Exception:
            pass
    if not client.collection_exists(collection):
        client.create_collection(
            collection_name=collection,
            vectors_config=rest.VectorParams(size=dim, distance=rest.Distance.COSINE),
        )
        logger.info("Created Qdrant collection: %s (dim=%d)", collection, dim)
    return dim


def upsert_records(records: list[dict[str, Any]], recreate: bool = False) -> int:
    """Upsert chunk payloads and vectors into the configured collection."""
    from qdrant_client.http import models as rest  # type: ignore

    if not records:
        logger.warning("No records to index into Qdrant")
        return 0
    first_embedding = records[0].get("embedding") or []
    vector_size = len(first_embedding)
    if vector_size == 0:
        logger.error("Records have no embeddings")
        return 0
    ensure_collection(vector_size=vector_size, recreate=recreate)
    client = get_qdrant_client(timeout=60)
    collection = SETTINGS.qdrant_collection
    points = []
    for idx, record in enumerate(records):
        embedding = record.get("embedding") or []
        if not embedding:
            continue
        payload = {k: v for k, v in record.items() if k != "embedding"}
        point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, str(record.get("chunk_id") or idx)))
        points.append(rest.PointStruct(id=point_id, vector=embedding, payload=payload))
    batch_size = 100
    total = 0
    for i in range(0, len(points), batch_size):
        batch = points[i : i + batch_size]
        client.upsert(collection_name=collection, points=batch)
        total += len(batch)
    return total


def search_qdrant(
    query_vector: list[float],
    top_k: int = 10,
    filters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Search Qdrant for semantically similar chunks."""
    try:
        from qdrant_client.http import models as rest  # type: ignore
    except ImportError:
        logger.error("qdrant_client is not installed")
        return []

    try:
        client = get_qdrant_client(timeout=10)
        collection = SETTINGS.qdrant_collection
        if not client.collection_exists(collection):
            logger.warning("Qdrant collection '%s' does not exist", collection)
            return []

        qdrant_filter = None
        if filters:
            conditions = []
            for key, value in filters.items():
                if isinstance(value, list):
                    conditions.append(rest.FieldCondition(key=key, match=rest.MatchAny(any=value)))
                else:
                    conditions.append(rest.FieldCondition(key=key, match=rest.MatchValue(value=value)))
            if conditions:
                qdrant_filter = rest.Filter(must=conditions)

        results = client.search(
            collection_name=collection,
            query_vector=query_vector,
            query_filter=qdrant_filter,
            limit=top_k,
            with_payload=True,
        )
        hits: list[dict[str, Any]] = []
        for res in results:
            if not res.payload:
                continue
            hits.append(
                {
                    "score": float(res.score),
                    "retrieval_source": "qdrant",
                    **res.payload,
                }
            )
        return hits
    except Exception as e:
        logger.warning("Qdrant is unavailable for this request; returning empty dense results (%s)", e)
        return []
