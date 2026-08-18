from __future__ import annotations

from pathlib import Path

from app.ai_stubs.draft_fields import missing_fields
from app.ai_stubs.generation import generate_answer
from app.ai_stubs.intent import classify_intent
from app.ai_stubs.retrieval import retrieve


def test_intent_classifier_routes_draft_requests() -> None:
    assert classify_intent("Please draft a legal notice for unpaid rent") == "document_draft_request"


def test_missing_fields_uses_template_registry() -> None:
    fields = missing_fields(
        "employment_complaint",
        {"employee_name": "Asha", "amount_due": "20000"},
    )
    assert "employer_name" in fields
    assert "salary_due_period" in fields
    assert "employee_name" not in fields


def test_retrieve_returns_relevant_wage_chunk() -> None:
    results = retrieve("my employer has not paid me for two months")
    assert results
    assert any("Payment of Wages Act" in chunk.get("act", "") for chunk in results)


def test_generate_answer_falls_back_on_low_confidence() -> None:
    result = generate_answer("random unrelated question", [{"confidence": 0.1}])
    assert result["fallback_used"] is True
    assert result["confidence"] == 0.1


def test_generate_answer_synthesizes_from_chunk() -> None:
    result = generate_answer(
        "my employer has not paid me",
        [
            {
                "act": "Payment of Wages Act, 1936",
                "section": "Section 15",
                "simplified_text": "A worker may ask the proper authority to recover unpaid wages.",
                "confidence": 0.9,
            }
        ],
    )
    assert result["fallback_used"] is False
    assert "Payment of Wages Act" in result["your_right"]

