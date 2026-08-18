"""LangGraph orchestration pipeline for NyayaSetu."""
from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, StateGraph  # type: ignore

from app.ai.ai_stubs.common import normalize_text
from app.ai.ai_stubs.draft_fields import missing_fields
from app.ai.ai_stubs.generation import generate_answer as legacy_generate_answer
from app.ai.ai_stubs.intent import classify_intent
from app.ai.ai_stubs.speech import transcribe
from app.ai.ai_stubs.vision import extract_document
from app.ai.langid import detect_language
from app.ai.llm import get_provider
from app.ai.safety import check_safety
from app.ai.types import PipelineState
from app.rag.evidence_gate import evaluate_evidence
from app.rag.retriever import retrieve

logger = logging.getLogger(__name__)


def input_processor(state: PipelineState) -> dict[str, Any]:
    """Process raw input, handle multimodality, and normalize text."""
    logger.info("Executing node: input_processor")
    text = state.get("text", "") or state.get("current_message", "") or ""
    input_type = state.get("input_type", "text")
    
    document = None
    
    if input_type == "audio" and state.get("audio_bytes"):
        text = transcribe(state["audio_bytes"])
    elif input_type == "image" and state.get("image_bytes"):
        document = extract_document(state["image_bytes"])
        text = str(document.get("retrieval_query") or document.get("extracted_text") or "")
    elif not text and state.get("document"):
        document = state["document"]
        text = str(document.get("retrieval_query") or document.get("extracted_text") or "")
        
    normalized = normalize_text(text)
    
    return {
        "text": text,
        "normalized_text": normalized,
        "current_message": normalized,
        "document": document,
        "conversation_history": state.get("conversation_history", []),
        "collected_information": state.get("collected_information", {}),
    }


def language_detector(state: PipelineState) -> dict[str, Any]:
    """Detect the language of the input."""
    logger.info("Executing node: language_detector")
    lang = detect_language(state.get("normalized_text", ""))
    return {"language": lang}


def safety_checker(state: PipelineState) -> dict[str, Any]:
    """Check input for safety violations."""
    logger.info("Executing node: safety_checker")
    safety_result = check_safety(state.get("normalized_text", ""))
    status = "unsafe" if not safety_result.get("safe", True) else "ok"
    
    updates: dict[str, Any] = {"safety_status": status}
    
    if status == "unsafe":
        reason = safety_result.get("reason", "Violation of safety policies")
        updates["answer"] = {
            "your_right": f"I cannot process this request. Reason: {reason}",
            "remedy": "Please refrain from harmful queries.",
            "next_step": "End conversation",
            "fallback_used": True,
            "confidence": 0.0,
        }
        updates["next_action"] = "end"
        
    return updates


def intent_classifier(state: PipelineState) -> dict[str, Any]:
    """Classify the user's intent to route the query."""
    logger.info("Executing node: intent_classifier")
    
    text = state.get("normalized_text", "")
    history = state.get("conversation_history", [])
    
    # Simple context inclusion
    if history and len(text.split()) < 5:
        last_msg = history[-1].get("content", "")
        text = f"Previous context: {last_msg}. User follow-up: {text}"
        
    intent = classify_intent(text)
    return {"intent": intent}


def action_router(state: PipelineState) -> str:
    """Conditional edge router based on safety and intent."""
    logger.info("Evaluating router conditional edge")
    
    if state.get("safety_status") == "unsafe":
        return "unsafe"
        
    intent = state.get("intent", "")
    
    if state.get("document") is not None:
        return "vision"
        
    if intent == "document_draft_request":
        return "drafting"
        
    if intent in ["rights_and_procedure", "legal_query"]:
        return "retrieval"
        
    return "general"


def retriever_node(state: PipelineState) -> dict[str, Any]:
    """Retrieve relevant chunks from Qdrant and BM25."""
    logger.info("Executing node: retriever_node")
    query = state.get("normalized_text", "")
    
    chunks = retrieve(query, qdrant_k=20, bm25_k=20, fusion_k=15, final_k=5)
    
    return {
        "chunks": chunks,
        "retrieved_chunks": chunks,
        "reranked_chunks": chunks,
    }


def evidence_gate_node(state: PipelineState) -> dict[str, Any]:
    """Evaluate if retrieved chunks are sufficient."""
    logger.info("Executing node: evidence_gate_node")
    chunks = state.get("chunks", [])
    query = state.get("normalized_text", "")
    
    decision = evaluate_evidence(query, chunks)
    
    return {
        "confidence_score": decision.confidence,
        "evidence_decision": decision.explanation,
        "evidence_sufficient": decision.sufficient,
    }


def generator_node(state: PipelineState) -> dict[str, Any]:
    """Generate final answer using retrieved evidence."""
    logger.info("Executing node: generator_node")
    
    # Check if evidence was sufficient
    sufficient = state.get("evidence_sufficient", True)
    
    if not sufficient:
        logger.info("Evidence insufficient, generating fallback response.")
        return {
            "answer": {
                "your_right": "I could not find sufficient verified legal evidence to answer your query securely.",
                "remedy": "Please consider consulting a legal aid service or lawyer.",
                "next_step": "Seek professional legal advice.",
                "fallback_used": True,
                "confidence": state.get("confidence_score", 0.0),
                "next_action": "consult_lawyer",
            },
            "next_action": "consult_lawyer",
        }
        
    # Temporary fallback to legacy generator until Phase 4 prompt is fully integrated
    answer = legacy_generate_answer(state.get("normalized_text", ""), state.get("chunks", []))
    
    return {
        "answer": answer,
        "next_action": answer.get("next_action", ""),
    }


def general_generator_node(state: PipelineState) -> dict[str, Any]:
    """Generate a response for non-legal queries."""
    logger.info("Executing node: general_generator_node")
    
    provider = get_provider()
    prompt = f"The user asked: '{state.get('normalized_text', '')}'. Respond politely that you are a legal awareness assistant and can only help with legal issues in India."
    
    response = provider.generate(prompt)
    
    return {
        "answer": {
            "your_right": response or "I am a legal awareness assistant and can only help with legal matters.",
            "remedy": "",
            "next_step": "Ask a legal question",
            "fallback_used": False,
            "confidence": 1.0,
            "next_action": "wait",
        },
        "next_action": "wait",
    }


def output_formatter(state: PipelineState) -> dict[str, Any]:
    """Format the final output."""
    logger.info("Executing node: output_formatter")
    answer = state.get("answer") or {}
    document = state.get("document")
    
    result: dict[str, Any] = {
        "intent": state.get("intent"),
        "query": state.get("normalized_text", ""),
        "answer": answer,
        "chunks": state.get("chunks", []),
        "confidence_score": state.get("confidence_score", 0.0),
        "safety_status": state.get("safety_status", "ok"),
        "next_action": answer.get("next_action") or state.get("next_action"),
    }
    
    if document is not None:
        result["document"] = document
        
    return result


def build_graph():
    """Build and compile the LangGraph StateGraph."""
    graph = StateGraph(PipelineState)
    
    graph.add_node("input_processor", input_processor)
    graph.add_node("language_detector", language_detector)
    graph.add_node("safety_checker", safety_checker)
    graph.add_node("intent_classifier", intent_classifier)
    graph.add_node("retriever", retriever_node)
    graph.add_node("evidence_gate", evidence_gate_node)
    graph.add_node("generator", generator_node)
    graph.add_node("general_generator", general_generator_node)
    graph.add_node("output_formatter", output_formatter)

    graph.set_entry_point("input_processor")
    graph.add_edge("input_processor", "language_detector")
    graph.add_edge("language_detector", "safety_checker")
    graph.add_edge("safety_checker", "intent_classifier")
    
    graph.add_conditional_edges(
        "intent_classifier",
        action_router,
        {
            "unsafe": "output_formatter",
            "vision": "retriever",  # Route to retrieval for now
            "drafting": "general_generator",  # Stub for now
            "retrieval": "retriever",
            "general": "general_generator",
        }
    )
    
    graph.add_edge("retriever", "evidence_gate")
    graph.add_edge("evidence_gate", "generator")
    graph.add_edge("generator", "output_formatter")
    graph.add_edge("general_generator", "output_formatter")
    graph.add_edge("output_formatter", END)
    
    return graph.compile()


# Build the graph singleton
_compiled_graph = build_graph()


def run_pipeline(state: PipelineState) -> dict[str, Any]:
    """Execute the compiled graph with the given state."""
    logger.info("Starting graph execution")
    final_state = _compiled_graph.invoke(state)
    logger.info("Graph execution completed")
    
    # We return the output directly from the formatter node which should be in the state
    return output_formatter(final_state)


# ============================================================================
# ENTRY POINTS FOR BACKEND INTEGRATION
# ============================================================================

def run_query_pipeline(query: str, input_type: str = "text", conversation_history: list[dict] = None) -> dict[str, Any]:
    state: PipelineState = {
        "text": query, 
        "input_type": input_type,
        "conversation_history": conversation_history or []
    }
    return run_pipeline(state)


def run_query_pipeline_with_audio(audio_bytes: bytes, conversation_history: list[dict] = None) -> dict[str, Any]:
    state: PipelineState = {
        "audio_bytes": audio_bytes, 
        "input_type": "audio", 
        "text": "",
        "conversation_history": conversation_history or []
    }
    return run_pipeline(state)


def run_query_pipeline_with_document(file_bytes: bytes, conversation_history: list[dict] = None) -> dict[str, Any]:
    state: PipelineState = {
        "image_bytes": file_bytes, 
        "input_type": "image", 
        "text": "",
        "conversation_history": conversation_history or []
    }
    return run_pipeline(state)


def get_missing_fields(doc_type: str, known_fields: dict) -> list[str]:
    return missing_fields(doc_type, known_fields)
