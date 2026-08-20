"""Reciprocal Rank Fusion (RRF) for combining multiple retrieval signals."""
from __future__ import annotations

import hashlib
from typing import Any


def _chunk_key(chunk: dict[str, Any]) -> str:
    cid = str(chunk.get("chunk_id") or "").strip()
    if cid:
        return cid
    raw = f"{chunk.get('document_name', '')}|{chunk.get('section', '')}|{chunk.get('page', '')}|{chunk.get('original_text', '')[:240]}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def rrf_merge(
    results_a: list[dict[str, Any]],
    results_b: list[dict[str, Any]],
    k: int = 60,
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """Merge two result lists using Reciprocal Rank Fusion.

    RRF_score = 1 / (k + rank_a) + 1 / (k + rank_b)

    Ties are broken by chunk_id so the ranking is deterministic.
    """
    scores: dict[str, float] = {}
    chunks: dict[str, dict[str, Any]] = {}

    def _add_ranks(results: list[dict[str, Any]]) -> None:
        for rank, chunk in enumerate(results, start=1):
            cid = _chunk_key(chunk)
            if cid not in chunks:
                chunks[cid] = dict(chunk)
                chunks[cid]["chunk_id"] = chunk.get("chunk_id") or cid
                chunks[cid]["retrieval_sources"] = []
            source = chunk.get("retrieval_source")
            if source and source not in chunks[cid]["retrieval_sources"]:
                chunks[cid]["retrieval_sources"].append(source)
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)

    _add_ranks(results_a)
    _add_ranks(results_b)

    sorted_cids = sorted(scores.keys(), key=lambda cid: (-scores[cid], cid))
    fused = []
    for cid in sorted_cids[:top_k]:
        record = dict(chunks[cid])
        record["fusion_score"] = scores[cid]
        fused.append(record)
    return fused
