"""Official-knowledge-base legal research (no case-law corpus)."""
from __future__ import annotations

from typing import Any

from backend.ai.llm import citations_from_chunks, generate_json_from_any
from backend.rag.evidence_gate import evaluate_evidence
from backend.rag.retrieval import retrieve


def research(query: str) -> dict[str, Any]:
    chunks = retrieve(query)
    decision = evaluate_evidence(query, chunks)
    citations = citations_from_chunks(chunks)
    if not decision.sufficient:
        return {
            "query": query,
            "sufficient": False,
            "provisions": [],
            "summary": "Sufficient official material was not found in the approved knowledge base.",
            "citations": [],
            "comparison": [],
            "disclaimer": "Research is limited to ingested official sources. No case law is used.",
        }
    prompt = (
        "Compare and summarize only the official provisions below. Do not add case law. "
        "Return JSON with keys: summary, provisions (array of {act, section, point}), "
        "comparison (array of short contrasts).\n\n"
        f"Question: {query}\n\n"
        + "\n\n".join(
            f"{item.get('act') or item.get('document_name')} {item.get('section')}: {item.get('original_text')}"
            for item in chunks[:6]
        )
    )
    generated = generate_json_from_any(prompt) or {}
    return {
        "query": query,
        "sufficient": True,
        "provisions": generated.get("provisions") or [
            {"act": item.get("act") or item.get("document_name"), "section": item.get("section"), "point": item.get("original_text")}
            for item in chunks[:5]
        ],
        "summary": generated.get("summary") or chunks[0].get("original_text"),
        "comparison": generated.get("comparison") or [],
        "citations": citations,
        "disclaimer": "Research is limited to ingested official sources. No case law is used.",
    }
