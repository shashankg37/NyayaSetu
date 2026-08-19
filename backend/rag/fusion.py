"""Reciprocal Rank Fusion (RRF) for combining multiple retrieval signals."""
from __future__ import annotations

from typing import Any


def rrf_merge(
    results_a: list[dict[str, Any]],
    results_b: list[dict[str, Any]],
    k: int = 60,
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """Merge two result lists using Reciprocal Rank Fusion.

    RRF_score = 1 / (k + rank_a) + 1 / (k + rank_b)

    Args:
        results_a: First ranked list (e.g. Qdrant).
        results_b: Second ranked list (e.g. BM25).
        k: Smoothing constant.
        top_k: Max number of merged results to return.

    Returns:
        A single fused and sorted list of chunks.
    """
    scores: dict[str, float] = {}
    chunks: dict[str, dict[str, Any]] = {}

    def _add_ranks(results: list[dict[str, Any]]) -> None:
        for rank, chunk in enumerate(results, start=1):
            cid = str(chunk.get("chunk_id", ""))
            if not cid:
                continue
            if cid not in chunks:
                chunks[cid] = dict(chunk)
                chunks[cid]["retrieval_sources"] = []
            source = chunk.get("retrieval_source")
            if source and source not in chunks[cid]["retrieval_sources"]:
                chunks[cid]["retrieval_sources"].append(source)
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)

    _add_ranks(results_a)
    _add_ranks(results_b)

    # Sort by RRF score descending
    sorted_cids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

    fused = []
    for cid in sorted_cids[:top_k]:
        record = dict(chunks[cid])
        record["fusion_score"] = scores[cid]
        fused.append(record)

    return fused
