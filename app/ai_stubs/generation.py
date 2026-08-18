from __future__ import annotations

from typing import Any

from app.ai_stubs.common import get_threshold
from app.config import SETTINGS


def _fallback_response(query: str, chunks: list[dict[str, Any]], confidence: float) -> dict[str, Any]:
    return {
        "your_right": (
            "I could not find a strong enough legal match in the grounded corpus to answer confidently."
        ),
        "what_law_says": (
            "This case needs human review. Please contact your nearest District Legal Services Authority "
            "or the NALSA helpline for guided assistance."
        ),
        "what_this_means": (
            "The system is not making a legal claim here because the retrieved evidence is too weak."
        ),
        "what_you_can_do": [
            "Visit or call your local District Legal Services Authority.",
            "Keep any letters, payslips, notices, or messages that support your case.",
            "If this is urgent, ask a lawyer or legal aid clinic to review the facts directly.",
        ],
        "source": [{"act": "NALSA / DLSA routing", "section": "Legal aid support"}],
        "confidence": float(confidence),
        "fallback_used": True,
        "query": query,
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
        "source": [{"act": act, "section": section}],
        "confidence": float(top.get("confidence", 0.0)),
        "fallback_used": False,
        "query": query,
    }


def _build_context(chunks: list[dict[str, Any]]) -> str:
    lines = []
    for idx, chunk in enumerate(chunks[:5], start=1):
        lines.append(
            f"{idx}. Act: {chunk.get('act', '')}\n"
            f"Section: {chunk.get('section', '')}\n"
            f"Topic: {chunk.get('topic', '')}\n"
            f"Text: {chunk.get('simplified_text') or chunk.get('original_text') or ''}"
        )
    return "\n\n".join(lines)


def _gemini_generate(query: str, chunks: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not SETTINGS.gemini_api_key:
        return None
    try:
        from langchain_core.output_parsers import JsonOutputParser  # type: ignore
        from langchain_core.prompts import ChatPromptTemplate  # type: ignore
        from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore
    except Exception:
        return None

    parser = JsonOutputParser()
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a legal assistant for India. Use only the supplied chunks. "
                "Do not invent law. Cite the act and section for every claim. "
                "Return valid JSON only."
            ),
            (
                "human",
                "Question:\n{query}\n\n"
                "Grounded chunks:\n{context}\n\n"
                "Return JSON with keys: your_right, what_law_says, what_this_means, "
                "what_you_can_do, source, confidence, fallback_used.\n"
                "{format_instructions}",
            ),
        ]
    )
    llm = ChatGoogleGenerativeAI(
        model=SETTINGS.gemini_model,
        google_api_key=SETTINGS.gemini_api_key,
        temperature=0,
    )
    chain = prompt | llm | parser
    try:
        response = chain.invoke(
            {
                "query": query,
                "context": _build_context(chunks),
                "format_instructions": parser.get_format_instructions(),
            }
        )
        if isinstance(response, dict):
            return response
    except Exception:
        return None
    return None


def generate_answer(query: str, chunks: list[dict[str, Any]]) -> dict[str, Any]:
    """Takes the top retrieved chunks and either produces a grounded, cited answer,
    or a safe fallback pointing to legal aid."""
    if not chunks:
        return _fallback_response(query, chunks, 0.0)
    top_confidence = float(chunks[0].get("confidence", 0.0))
    if top_confidence < get_threshold():
        return _fallback_response(query, chunks, top_confidence)
    gemini_answer = _gemini_generate(query, chunks)
    if gemini_answer:
        gemini_answer.setdefault("confidence", top_confidence)
        gemini_answer.setdefault("fallback_used", False)
        gemini_answer.setdefault(
            "source",
            [{"act": chunks[0].get("act", "Unknown act"), "section": chunks[0].get("section", "")}],
        )
        gemini_answer.setdefault("query", query)
        return gemini_answer
    return _synthesize_from_chunks(query, chunks)
