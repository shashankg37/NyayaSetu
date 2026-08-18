"""Indexing module for Qdrant and BM25.

Handles creation/recreation of Qdrant collections and BM25 pickle indices.
Uses the Qdrant client directly (not through LangChain wrappers).
"""
from __future__ import annotations

import logging
import re
from typing import Any

from app.ai.config import BM25_PATH, SETTINGS
from app.ai.knowledge_base.store import save_pickle

logger = logging.getLogger(__name__)


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenizer for BM25."""
    return [t.lower() for t in re.findall(r"[a-zA-Z0-9]+", text)]


def index_qdrant(records: list[dict[str, Any]], recreate: bool = False) -> int:
    """Index records into Qdrant.

    Each record must have:
        - 'embedding': list[float]
        - 'chunk_id': str
        - All metadata fields

    Returns the number of points upserted.
    """
    try:
        from qdrant_client import QdrantClient  # type: ignore
        from qdrant_client.http import models as rest  # type: ignore
    except ImportError:
        logger.error("qdrant_client is not installed")
        return 0

    if not records:
        logger.warning("No records to index into Qdrant")
        return 0

    # Determine vector size from first record
    first_embedding = records[0].get("embedding", [])
    vector_size = len(first_embedding)
    if vector_size == 0:
        logger.error("Records have no embeddings")
        return 0

    # Connect to Qdrant
    qdrant_url = SETTINGS.qdrant_url
    client = QdrantClient(url=qdrant_url, timeout=60)
    collection = SETTINGS.qdrant_collection

    # Recreate collection if requested
    if recreate:
        try:
            client.delete_collection(collection)
            logger.info("Deleted existing collection: %s", collection)
        except Exception:
            pass

    # Create collection if it doesn't exist
    if not client.collection_exists(collection):
        client.create_collection(
            collection_name=collection,
            vectors_config=rest.VectorParams(
                size=vector_size,
                distance=rest.Distance.COSINE,
            ),
        )
        logger.info("Created Qdrant collection: %s (dim=%d)", collection, vector_size)

    # Build points
    points = []
    for idx, record in enumerate(records):
        embedding = record.get("embedding", [])
        if not embedding:
            continue

        # Payload is everything except the embedding vector
        payload = {k: v for k, v in record.items() if k != "embedding"}

        points.append(
            rest.PointStruct(
                id=idx,
                vector=embedding,
                payload=payload,
            )
        )

    # Upsert in batches
    batch_size = 100
    total = 0
    for i in range(0, len(points), batch_size):
        batch = points[i : i + batch_size]
        client.upsert(collection_name=collection, points=batch)
        total += len(batch)
        logger.info("Indexed %d / %d points", total, len(points))

    return total


def index_bm25(records: list[dict[str, Any]]) -> int:
    """Build and save a BM25 index from records.

    The index is saved as a pickle file alongside the tokenized corpus
    and chunk_id mapping for retrieval.

    Returns the corpus size.
    """
    try:
        from rank_bm25 import BM25Okapi  # type: ignore
    except ImportError:
        logger.error("rank_bm25 is not installed")
        return 0

    if not records:
        logger.warning("No records to build BM25 index from")
        return 0

    # Build tokenized corpus
    corpus: list[list[str]] = []
    chunk_ids: list[str] = []

    for record in records:
        text = " ".join(
            part
            for part in [
                record.get("original_text", ""),
                record.get("section", ""),
                record.get("topic", ""),
            ]
            if part
        )
        corpus.append(_tokenize(text))
        chunk_ids.append(record.get("chunk_id", ""))

    bm25 = BM25Okapi(corpus)

    # Save as a bundle: (bm25_model, chunk_ids, records)
    save_pickle(
        {"bm25": bm25, "chunk_ids": chunk_ids, "records": records},
        BM25_PATH,
    )
    logger.info("Built BM25 index with %d documents, saved to %s", len(corpus), BM25_PATH)
    return len(corpus)
