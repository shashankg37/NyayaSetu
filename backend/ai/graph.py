"""LangGraph conversational pipeline for NyayaSetu."""
from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, StateGraph  # type: ignore

from backend.ai.drafting import DISCLAIMER, export_draft, render_draft, resolve_doc_type
from backend.ai.language import (
    classify_intent,
    detect_language,
    infer_legal_domain,
    missing_fields,
    normalize_text,
)
from backend.ai.lawyers import match_lawyers
from backend.ai.llm import generate_answer, generate_text_from_any
from backend.ai.research import research
from backend.ai.safety import check_safety
from backend.ai.speech import SpeechTranscriptionError, transcribe
from backend.ai.types import PipelineState
from backend.ai.vision import extract_document
from backend.rag.evidence_gate import evaluate_evidence
from backend.rag.retrieval import retrieve

logger = logging.getLogger(__name__)


def _history_text(history: list[dict[str, Any]]) -> str:
    return " ".join(str(item.get("content") or "") for item in history[-6:])


def input_processor(state: PipelineState) -> dict[str, Any]:
    text = state.get("text", "") or state.get("current_message", "") or ""
    input_type = state.get("input_type", "text")
    document = state.get("document")
    collected = dict(state.get("collected_information") or {})
    history = list(state.get("conversation_history") or [])

    if input_type == "audio" and state.get("audio_bytes"):
        try:
            text = transcribe(state["audio_bytes"])
        except SpeechTranscriptionError as exc:
            return {
                "text": "",
                "normalized_text": "",
                "current_message": "",
                "answer": {
                    "your_right": "Speech transcription failed.",
                    "what_law_says": str(exc),
                    "fallback_used": True,
                    "service_error": True,
                },
                "safety_status": "ok",
                "intent": "unsupported",
                "next_action": "retry_audio",
            }
    elif input_type == "image" and state.get("image_bytes"):
        document = extract_document(state["image_bytes"])
        text = str(document.get("retrieval_query") or document.get("extracted_text") or text)

    pending = state.get("pending_slot")
    if pending and text and len(text.split()) <= 8:
        collected[pending] = text.strip()

    current_issue = state.get("current_issue") or ""
    if not current_issue or len(text.split()) > 4:
        if not pending:
            current_issue = text or current_issue
    normalized = normalize_text(text)
    return {
        "text": text,
        "normalized_text": normalized,
        "current_message": normalized,
        "document": document,
        "uploaded_document": document,
        "conversation_history": history,
        "collected_information": collected,
        "current_issue": current_issue,
        "pending_slot": "" if pending and pending in collected else pending,
    }


def language_detector(state: PipelineState) -> dict[str, Any]:
    return {"language": detect_language(state.get("normalized_text", ""))}


def conversation_state_node(state: PipelineState) -> dict[str, Any]:
    collected = dict(state.get("collected_information") or {})
    issue = state.get("current_issue") or state.get("normalized_text", "")
    domain = state.get("legal_domain") or infer_legal_domain(f"{issue} {_history_text(state.get('conversation_history') or [])}")
    if "karnataka" in (state.get("normalized_text") or "").lower():
        collected["state"] = "Karnataka"
    if "daily wage" in (state.get("normalized_text") or "").lower() or (state.get("normalized_text") or "").lower() in {
        "daily wage",
        "daily-wage",
        "daily wager",
    }:
        collected["employment_type"] = "daily_wage"
    return {
        "collected_information": collected,
        "current_issue": issue,
        "legal_domain": domain,
        "jurisdiction": collected.get("state") or state.get("jurisdiction") or "unknown",
        "beneficiary": collected.get("employment_type") or state.get("beneficiary") or "unknown",
    }


def safety_checker(state: PipelineState) -> dict[str, Any]:
    safety_result = check_safety(state.get("normalized_text", ""))
    status = safety_result.get("status") or ("unsafe" if not safety_result.get("safe", True) else "ok")
    updates: dict[str, Any] = {"safety_status": status}
    if status == "unsafe":
        updates["answer"] = {
            "your_right": f"I cannot help with that request. {safety_result.get('reason', '')}",
            "remedy": "Ask a lawful legal-awareness question, or contact the police or a legal-aid clinic if you are in danger.",
            "next_step": "Rephrase the question or seek emergency help.",
            "fallback_used": True,
        }
        updates["next_action"] = "end"
    if status == "emergency":
        updates["answer"] = {
            "your_right": "If you are in danger, contact local emergency services or the police immediately.",
            "what_you_can_do": [
                "Call emergency services or a trusted person now.",
                "Contact the National Legal Services Authority or local DLSA for urgent legal aid.",
            ],
            "fallback_used": True,
        }
        updates["next_action"] = "emergency"
    return updates


def intent_classifier(state: PipelineState) -> dict[str, Any]:
    text = state.get("normalized_text", "")
    history = state.get("conversation_history") or []
    if history and len(text.split()) < 6:
        text = f"{_history_text(history)} {text}"
    if state.get("document") is not None:
        return {"intent": "document_understanding"}
    return {"intent": classify_intent(text)}


def action_router(state: PipelineState) -> str:
    if state.get("next_action") == "retry_audio":
        return "unsafe"
    if state.get("safety_status") == "unsafe":
        return "unsafe"
    if state.get("safety_status") == "emergency":
        return "emergency"
    intent = state.get("intent", "")
    if intent == "unsupported":
        return "unsupported"
    if intent == "drafting":
        return "drafting"
    if intent == "lawyer_matching":
        return "lawyers"
    if intent == "legal_research":
        return "research"
    if intent == "document_understanding" or state.get("document") is not None:
        return "vision"
    if intent in {"legal_guidance", "legal_awareness", "rights_query", "procedure_query"}:
        return "retrieval"
    return "retrieval"


def retriever_node(state: PipelineState) -> dict[str, Any]:
    collected = state.get("collected_information") or {}
    query = " ".join(
        part
        for part in [
            state.get("current_issue") or "",
            state.get("normalized_text") or "",
            collected.get("employment_type", ""),
            collected.get("state", ""),
        ]
        if part
    )
    chunks = retrieve(query)
    return {"chunks": chunks, "retrieved_chunks": chunks, "reranked_chunks": chunks}


def vision_node(state: PipelineState) -> dict[str, Any]:
    document = state.get("document")
    if document is None and state.get("image_bytes"):
        document = extract_document(state["image_bytes"])
    query = str((document or {}).get("retrieval_query") or state.get("normalized_text") or "")
    chunks = retrieve(query) if query else []
    return {
        "document": document,
        "uploaded_document": document,
        "chunks": chunks,
        "retrieved_chunks": chunks,
        "reranked_chunks": chunks,
    }


def evidence_gate_node(state: PipelineState) -> dict[str, Any]:
    decision = evaluate_evidence(state.get("normalized_text", ""), state.get("chunks") or [])
    return {
        "confidence_score": decision.confidence,
        "evidence_decision": decision.explanation,
        "evidence_sufficient": decision.sufficient,
        "evidence_status": decision.status,
        "evidence_verdict": decision.verdict,
    }


def evidence_router(state: PipelineState) -> str:
    status = state.get("evidence_status") or ""
    if status == "no_evidence" or not (state.get("chunks") or []):
        return "refuse"
    if status == "insufficient" or not state.get("evidence_sufficient", False):
        return "clarify"
    return "generate"


def clarify_node(state: PipelineState) -> dict[str, Any]:
    return {
        "answer": {
            "your_right": "The available official material only partly supports this question. I cannot give a complete legal answer from this evidence.",
            "what_law_says": state.get("evidence_decision") or "Retrieved evidence is incomplete or below the confidence threshold.",
            "what_this_means": "Please add facts such as the Act, location, dates, or document type, or ask a more specific question.",
            "what_you_can_do": [
                "Rephrase with more facts such as location, document type, or dates.",
                "Contact DLSA / NALSA for legal aid.",
            ],
            "citations": [],
            "source": None,
            "fallback_used": True,
            "disclaimer": "This is legal awareness information, not legal advice.",
        },
        "next_action": "clarify_or_legal_aid",
    }


def refuse_node(state: PipelineState) -> dict[str, Any]:
    return {
        "answer": {
            "your_right": "No relevant official legal evidence was found for this question. I will not invent a legal answer.",
            "what_law_says": state.get("evidence_decision") or "No grounded official source was retrieved.",
            "what_this_means": "The system is not making a legal claim because there is no matching knowledge-base evidence.",
            "what_you_can_do": [
                "Ask a question covered by an ingested official Act, Code, or legal-aid note.",
                "Contact DLSA / NALSA for legal aid.",
            ],
            "citations": [],
            "source": None,
            "fallback_used": True,
            "disclaimer": "This is legal awareness information, not legal advice.",
        },
        "next_action": "no_speculation",
    }


def generator_node(state: PipelineState) -> dict[str, Any]:
    answer = generate_answer(
        state.get("current_issue") or state.get("normalized_text", ""),
        state.get("chunks") or [],
        history=state.get("conversation_history") or [],
        extracted_document=state.get("document"),
    )
    if state.get("document"):
        answer["user_document_extraction"] = state["document"].get("extracted_fields")
        answer["knowledge_base"] = state.get("chunks")
        answer["ai_interpretation"] = answer.get("interpretation") or answer.get("what_this_means")
    return {"answer": answer, "next_action": answer.get("next_action") or "wait"}


def drafting_node(state: PipelineState) -> dict[str, Any]:
    collected = dict(state.get("collected_information") or {})
    doc_type = resolve_doc_type(state.get("current_issue") or state.get("normalized_text") or "", collected)
    if not doc_type:
        return {
            "answer": {
                "your_right": "I can help draft an RTI application, wage complaint, consumer complaint, government grievance, or legal notice. Which one do you need?",
                "fallback_used": False,
            },
            "next_action": "collect_doc_type",
            "missing_information": ["doc_type"],
        }
    collected["doc_type"] = doc_type
    missing = missing_fields(doc_type, collected)
    if missing:
        field = missing[0]
        return {
            "collected_information": collected,
            "missing_information": missing,
            "pending_slot": field,
            "answer": {
                "your_right": f"To draft the {doc_type.replace('_', ' ')}, I still need: {field.replace('_', ' ')}.",
                "disclaimer": DISCLAIMER,
                "fallback_used": False,
            },
            "next_action": f"collect_{field}",
        }
    body = render_draft(doc_type, collected)
    pdf_path = str(export_draft(doc_type, collected, "pdf"))
    docx_path = str(export_draft(doc_type, collected, "docx"))
    return {
        "collected_information": collected,
        "missing_information": [],
        "pending_slot": "",
        "answer": {
            "your_right": "A draft has been generated. It is not legally verified.",
            "draft_text": body,
            "pdf_path": pdf_path,
            "docx_path": docx_path,
            "disclaimer": DISCLAIMER,
            "fallback_used": False,
        },
        "next_action": "download_draft",
    }


def research_node(state: PipelineState) -> dict[str, Any]:
    result = research(state.get("current_issue") or state.get("normalized_text") or "")
    return {
        "chunks": result.get("provisions") or [],
        "evidence_sufficient": result.get("sufficient", False),
        "evidence_status": "sufficient" if result.get("sufficient") else "insufficient",
        "answer": {
            "your_right": result.get("summary"),
            "what_law_says": result.get("provisions"),
            "citations": result.get("citations"),
            "disclaimer": result.get("disclaimer"),
            "fallback_used": not result.get("sufficient"),
        },
        "next_action": "review_provisions",
    }


def lawyer_node(state: PipelineState) -> dict[str, Any]:
    db = state.get("db_session")
    if db is None:
        return {
            "answer": {
                "your_right": "Lawyer matching requires an active database session.",
                "fallback_used": True,
            },
            "next_action": "consult_lawyer",
        }
    matches = match_lawyers(
        db,
        {
            "legal_domain": state.get("legal_domain"),
            "jurisdiction": state.get("jurisdiction"),
            "state": (state.get("collected_information") or {}).get("state"),
            "language": state.get("language"),
        },
    )
    return {
        "answer": {
            "your_right": "These lawyer profiles matched your issue from the directory. This is not an endorsement.",
            "matches": matches,
            "fallback_used": False,
        },
        "next_action": "review_lawyer_matches",
    }


def unsupported_node(state: PipelineState) -> dict[str, Any]:
    return {
        "answer": {
            "your_right": "This request is outside Nyaya Setu's legal-awareness scope.",
            "what_you_can_do": ["Ask about rights, procedures, or official remedies under Indian law."],
            "fallback_used": True,
        },
        "next_action": "end",
    }


def general_generator_node(state: PipelineState) -> dict[str, Any]:
    response = generate_text_from_any(
        "You are a legal-awareness assistant for India. The user said: "
        f"{state.get('normalized_text', '')}. Politely explain your scope."
    )
    if not response:
        response = "I am a legal-awareness assistant for Indian official legal sources. Please ask a legal question."
    return {
        "answer": {"your_right": response, "fallback_used": False, "next_action": "wait"},
        "next_action": "wait",
    }


def output_formatter(state: PipelineState) -> dict[str, Any]:
    answer = state.get("answer") or {}
    result: dict[str, Any] = {
        "intent": state.get("intent"),
        "query": state.get("normalized_text", ""),
        "language": state.get("language"),
        "legal_domain": state.get("legal_domain"),
        "beneficiary": state.get("beneficiary"),
        "jurisdiction": state.get("jurisdiction"),
        "current_issue": state.get("current_issue"),
        "collected_information": state.get("collected_information") or {},
        "missing_information": state.get("missing_information") or [],
        "pending_slot": state.get("pending_slot") or "",
        "answer": answer,
        "chunks": state.get("chunks", []),
        "retrieved_chunks": state.get("retrieved_chunks", []),
        "reranked_chunks": state.get("reranked_chunks", []),
        "confidence_score": state.get("confidence_score", 0.0),
        "evidence_status": state.get("evidence_status", "unknown"),
        "evidence_verdict": state.get("evidence_verdict", ""),
        "safety_status": state.get("safety_status", "ok"),
        "next_action": answer.get("next_action") or state.get("next_action"),
        "document": state.get("document"),
    }
    return {"formatted": result, **{k: v for k, v in result.items() if k != "formatted"}}


def build_graph():
    graph = StateGraph(PipelineState)
    graph.add_node("input_processor", input_processor)
    graph.add_node("language_detector", language_detector)
    graph.add_node("conversation_state", conversation_state_node)
    graph.add_node("safety_checker", safety_checker)
    graph.add_node("intent_classifier", intent_classifier)
    graph.add_node("retriever", retriever_node)
    graph.add_node("vision", vision_node)
    graph.add_node("evidence_gate", evidence_gate_node)
    graph.add_node("generator", generator_node)
    graph.add_node("clarify", clarify_node)
    graph.add_node("refuse", refuse_node)
    graph.add_node("drafting", drafting_node)
    graph.add_node("research", research_node)
    graph.add_node("lawyers", lawyer_node)
    graph.add_node("unsupported", unsupported_node)
    graph.add_node("general_generator", general_generator_node)
    graph.add_node("output_formatter", output_formatter)

    graph.set_entry_point("input_processor")
    graph.add_edge("input_processor", "language_detector")
    graph.add_edge("language_detector", "conversation_state")
    graph.add_edge("conversation_state", "safety_checker")
    graph.add_edge("safety_checker", "intent_classifier")
    graph.add_conditional_edges(
        "intent_classifier",
        action_router,
        {
            "unsafe": "output_formatter",
            "emergency": "output_formatter",
            "unsupported": "unsupported",
            "vision": "vision",
            "drafting": "drafting",
            "research": "research",
            "lawyers": "lawyers",
            "retrieval": "retriever",
            "general": "general_generator",
        },
    )
    graph.add_edge("retriever", "evidence_gate")
    graph.add_edge("vision", "evidence_gate")
    graph.add_conditional_edges(
        "evidence_gate",
        evidence_router,
        {
            "generate": "generator",
            "clarify": "clarify",
            "refuse": "refuse",
        },
    )
    graph.add_edge("generator", "output_formatter")
    graph.add_edge("clarify", "output_formatter")
    graph.add_edge("refuse", "output_formatter")
    graph.add_edge("drafting", "output_formatter")
    graph.add_edge("research", "output_formatter")
    graph.add_edge("lawyers", "output_formatter")
    graph.add_edge("unsupported", "output_formatter")
    graph.add_edge("general_generator", "output_formatter")
    graph.add_edge("output_formatter", END)
    return graph.compile()


_compiled_graph = None


def compiled_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


def run_pipeline(state: PipelineState) -> dict[str, Any]:
    final_state = compiled_graph().invoke(state)
    return final_state.get("formatted") or output_formatter(final_state)


def run_query_pipeline(
    query: str,
    input_type: str = "text",
    conversation_history: list[dict] | None = None,
    conversation_state: dict[str, Any] | None = None,
    db_session: Any = None,
) -> dict[str, Any]:
    prior = conversation_state or {}
    state: PipelineState = {
        "text": query,
        "input_type": input_type,
        "conversation_history": conversation_history or [],
        "collected_information": dict(prior.get("collected_information") or {}),
        "current_issue": prior.get("current_issue") or "",
        "pending_slot": prior.get("pending_slot") or "",
        "legal_domain": prior.get("legal_domain") or "",
        "jurisdiction": prior.get("jurisdiction") or "",
        "db_session": db_session,
    }
    return run_pipeline(state)


def run_query_pipeline_with_audio(
    audio_bytes: bytes,
    conversation_history: list[dict] | None = None,
    conversation_state: dict[str, Any] | None = None,
    db_session: Any = None,
) -> dict[str, Any]:
    prior = conversation_state or {}
    return run_pipeline(
        {
            "audio_bytes": audio_bytes,
            "input_type": "audio",
            "text": "",
            "conversation_history": conversation_history or [],
            "collected_information": dict(prior.get("collected_information") or {}),
            "current_issue": prior.get("current_issue") or "",
            "pending_slot": prior.get("pending_slot") or "",
            "db_session": db_session,
        }
    )


def run_query_pipeline_with_document(
    file_bytes: bytes,
    conversation_history: list[dict] | None = None,
    conversation_state: dict[str, Any] | None = None,
    db_session: Any = None,
) -> dict[str, Any]:
    prior = conversation_state or {}
    return run_pipeline(
        {
            "image_bytes": file_bytes,
            "input_type": "image",
            "text": "",
            "conversation_history": conversation_history or [],
            "collected_information": dict(prior.get("collected_information") or {}),
            "current_issue": prior.get("current_issue") or "",
            "db_session": db_session,
        }
    )


def get_missing_fields(doc_type: str, known_fields: dict) -> list[str]:
    return missing_fields(doc_type, known_fields)
