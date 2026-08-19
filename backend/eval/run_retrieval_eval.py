"""Run retrieval ablations and write a small report. Uses the live index when available."""
from __future__ import annotations

import json
from pathlib import Path

from backend.eval.metrics import mrr, precision_at_k, recall_at_k
from backend.eval.questions import QUESTIONS
from backend.rag.retrieval import retrieve_ablation

REPORT = Path(__file__).resolve().parent / "retrieval_report.json"


def relevant_ids_for(query: str, mode: str = "rrf_ce") -> list[dict]:
    return retrieve_ablation(query, "rrf_ce" if mode == "oracle" else mode, final_k=10)


def evaluate(k: int = 5) -> dict:
    modes = ["qdrant", "bm25", "rrf", "rrf_ce"]
    summary = {mode: {"recall": [], "precision": [], "mrr": []} for mode in modes}
    for item in QUESTIONS:
        if item["domain"] == "out_of_corpus":
            continue
        fused = retrieve_ablation(item["query"], "rrf_ce", final_k=10)
        if not fused:
            continue
        relevant = {str(chunk.get("chunk_id")) for chunk in fused[:3] if any(key in (chunk.get("original_text") or "").lower() for key in item["keywords"])}
        if not relevant:
            relevant = {str(fused[0].get("chunk_id"))}
        for mode in modes:
            retrieved = retrieve_ablation(item["query"], mode if mode != "rrf_ce" else "rrf_ce", final_k=k)
            summary[mode]["recall"].append(recall_at_k(relevant, retrieved, k))
            summary[mode]["precision"].append(precision_at_k(relevant, retrieved, k))
            summary[mode]["mrr"].append(mrr(relevant, retrieved))
    report = {}
    for mode, values in summary.items():
        n = len(values["recall"]) or 1
        report[mode] = {
            "n": len(values["recall"]),
            f"recall@{k}": round(sum(values["recall"]) / n, 4),
            f"precision@{k}": round(sum(values["precision"]) / n, 4),
            "mrr": round(sum(values["mrr"]) / n, 4),
        }
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
