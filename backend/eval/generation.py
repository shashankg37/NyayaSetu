"""Generation evaluation helpers. Metrics are computed only from observed outputs."""
from __future__ import annotations

from typing import Any


def evaluate_generation(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        return {"n": 0, "note": "No generation records were measured."}
    citation_ok = 0
    grounded = 0
    hallucinations = 0
    complete = 0
    refusals = 0
    for item in records:
        answer = item.get("answer") or {}
        citations = answer.get("citations") or []
        chunks = item.get("chunks") or []
        fallback = bool(answer.get("fallback_used"))
        if fallback:
            refusals += 1
        if citations and all((c.get("act") or c.get("document_name")) for c in citations):
            citation_ok += 1
        chunk_text = " ".join(str(c.get("original_text") or "") for c in chunks).lower()
        law_text = str(answer.get("what_law_says") or "").lower()
        if fallback or (law_text and (not chunks or any(token in chunk_text for token in law_text.split()[:8]))):
            grounded += 1
        else:
            hallucinations += 1
        if answer.get("your_right") and (answer.get("what_you_can_do") or fallback):
            complete += 1
    n = len(records)
    return {
        "n": n,
        "citation_correctness": round(citation_ok / n, 4),
        "evidence_grounding": round(grounded / n, 4),
        "hallucination_rate": round(hallucinations / n, 4),
        "answer_completeness": round(complete / n, 4),
        "refusal_or_fallback_rate": round(refusals / n, 4),
    }
