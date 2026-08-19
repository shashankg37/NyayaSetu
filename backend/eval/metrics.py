from __future__ import annotations

from typing import Any


def recall_at_k(relevant_ids: set[str], retrieved: list[dict[str, Any]], k: int) -> float:
    if not relevant_ids:
        return 0.0
    got = {str(item.get("chunk_id")) for item in retrieved[:k]}
    return len(relevant_ids & got) / len(relevant_ids)


def precision_at_k(relevant_ids: set[str], retrieved: list[dict[str, Any]], k: int) -> float:
    top = retrieved[:k]
    if not top:
        return 0.0
    hits = sum(1 for item in top if str(item.get("chunk_id")) in relevant_ids)
    return hits / len(top)


def mrr(relevant_ids: set[str], retrieved: list[dict[str, Any]]) -> float:
    for rank, item in enumerate(retrieved, start=1):
        if str(item.get("chunk_id")) in relevant_ids:
            return 1.0 / rank
    return 0.0
