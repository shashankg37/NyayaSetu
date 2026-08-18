from __future__ import annotations

from typing import Any

from app.ai.ai_stubs.common import get_threshold
from app.ai.llm import generate_json


def _fallback_response(query: str, chunks: list[dict[str, Any]], confidence: float) -> dict[str, Any]:
    return {
        "your_right": "I could not find a strong enough legal match in the grounded corpus to answer confidently.",
        "what_law_says": "This case needs human review. Please contact your nearest District Legal Services Authority or the NALSA helpline for guided assistance.",
        "what_this_means": "The system is not making a legal claim here because the retrieved evidence is too weak.",
        "what_you_can_do": [
            "Visit or call your local District Legal Services Authority.",
            "Keep any letters, payslips, notices, or messages that support your case.",
            "If this is urgent, ask a lawyer or legal aid clinic to review the facts directly.",
        ],
        "source": {"act": "NALSA / DLSA routing", "section": "Legal aid support"},
        "confidence": float(confidence),
        "fallback_used": True,
        "query": query,
        "next_action": "legal_aid_or_more_information",
    }


def _synthesize_from_chunks(query: str, chunks: list[dict[str, Any]]) -> dict[str, Any]:
    top = chunks[0]
    act = top.get("act", "Unknown act")
    section = top.get("section", "Unknown section")
    simplified = top.get("simplified_text") or top.get("original_text") or ""
    return {
        "your_right": f"The strongest grounded match points to {act}, {section}.",
        "what_law_says": simplified or "The retrieved chunk describes the relevant legal rule.",
        "what_this_means": "Based on the retrieved material, the issue appears to fall under the cited provision.",
        "what_you_can_do": [
            "Review the cited source in full before taking action.",
            "Keep supporting documents ready in case you need legal aid or a claim filing.",
        ],
        "source": {"act": act, "section": section},
        "confidence": float(top.get("confidence", 0.0)),
        "fallback_used": False,
        "query": query,
        "next_action": "review_cited_source",
    }


def _build_context(chunks: list[dict[str, Any]]) -> str:
    lines = []
    for idx, chunk in enumerate(chunks[:5], start=1):
        lines.append(
            f"{idx}. Act: {chunk.get('act', '')}\nSection: {chunk.get('section', '')}\nTopic: {chunk.get('topic', '')}\nText: {chunk.get('simplified_text') or chunk.get('original_text') or ''}"
        )
    return "\n\n".join(lines)


def _provider_generate(query: str, chunks: list[dict[str, Any]]) -> dict[str, Any] | None:
    prompt = (
        "You are Nyaya Setu, an Indian legal-awareness assistant. Use only the supplied chunks. "
        "Do not invent law. Cite one act and section from the evidence. Return JSON only with keys: "
        "your_right, what_law_says, what_this_means, what_you_can_do, source, confidence, fallback_used.\n\n"
        f"Question:\n{query}\n\nGrounded chunks:\n{_build_context(chunks)}"
    )
    return generate_json(prompt)


def generate_answer(query: str, chunks: list[dict[str, Any]]) -> dict[str, Any]:
    if not chunks:
        return _fallback_response(query, chunks, 0.0)
    top_confidence = float(chunks[0].get("confidence", 0.0))
    if top_confidence < get_threshold():
        return _fallback_response(query, chunks, top_confidence)
    provider_answer = _provider_generate(query, chunks)
    if provider_answer:
        provider_answer.setdefault("confidence", top_confidence)
        provider_answer.setdefault("fallback_used", False)
        source = provider_answer.get("source")
        if isinstance(source, list):
            provider_answer["source"] = source[0] if source else {}
        provider_answer.setdefault("source", {"act": chunks[0].get("act", "Unknown act"), "section": chunks[0].get("section", "")})
        provider_answer.setdefault("query", query)
        return provider_answer
    return _synthesize_from_chunks(query, chunks)
