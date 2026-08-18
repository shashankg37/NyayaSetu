from __future__ import annotations

from typing import Any

from app.ai.ai_stubs.draft_fields import missing_fields
from app.ai.ai_stubs.generation import generate_answer
from app.ai.ai_stubs.intent import classify_intent
from app.ai.ai_stubs.retrieval import retrieve
from app.ai.ai_stubs.speech import transcribe
from app.ai.ai_stubs.vision import extract_document
from app.ai.ai_stubs.common import normalize_text
from app.ai.types import PipelineState


def input_processor(state: PipelineState) -> PipelineState:
    text = state.get("text", "") or ""
    input_type = state.get("input_type", "text")
    if input_type == "audio" and state.get("audio_bytes"):
        text = transcribe(state["audio_bytes"])
    elif input_type == "image" and state.get("image_bytes"):
        document = extract_document(state["image_bytes"])
        state["document"] = document
        text = str(document.get("retrieval_query") or document.get("extracted_text") or "")
    elif not text and state.get("document"):
        document = state["document"]
        text = str(document.get("retrieval_query") or document.get("extracted_text") or "")
    state["normalized_text"] = normalize_text(text)
    return state


def intent_classifier(state: PipelineState) -> PipelineState:
    state["intent"] = classify_intent(state.get("normalized_text", ""))
    return state


def retriever_node(state: PipelineState) -> PipelineState:
    state["chunks"] = retrieve(state.get("normalized_text", ""))
    return state


def generation_node(state: PipelineState) -> PipelineState:
    state["answer"] = generate_answer(state.get("normalized_text", ""), state.get("chunks", []))
    return state


def output_formatter(state: PipelineState) -> dict[str, Any]:
    answer = state.get("answer") or {}
    document = state.get("document")
    result: dict[str, Any] = {
        "intent": state.get("intent"),
        "query": state.get("normalized_text", ""),
        "answer": answer,
        "chunks": state.get("chunks", []),
    }
    if document is not None:
        result["document"] = document
    return result


def build_graph():
    try:
        from langgraph.graph import END, StateGraph  # type: ignore
    except Exception:
        return None

    graph = StateGraph(PipelineState)
    graph.add_node("input_processor", input_processor)
    graph.add_node("intent_classifier", intent_classifier)
    graph.add_node("retriever", retriever_node)
    graph.add_node("generator", generation_node)
    graph.add_node("output_formatter", output_formatter)

    graph.set_entry_point("input_processor")
    graph.add_edge("input_processor", "intent_classifier")
    graph.add_edge("intent_classifier", "retriever")
    graph.add_edge("retriever", "generator")
    graph.add_edge("generator", "output_formatter")
    graph.add_edge("output_formatter", END)
    return graph.compile()


def run_pipeline(state: PipelineState) -> dict[str, Any]:
    state = input_processor(state)
    state = intent_classifier(state)
    state = retriever_node(state)
    state = generation_node(state)
    return output_formatter(state)


# ============================================================================
# CLEAN ENTRY POINTS FOR BACKEND INTEGRATION
# ============================================================================
# The backend should call only these functions; they wrap the internal pipeline.


def run_query_pipeline(query: str, input_type: str = "text") -> dict[str, Any]:
    """
    Runs the full AI pipeline (intent → retrieve → generate) and returns
    a plain dict matching the standard answer shape.
    
    Args:
        query: The user's question or text input.
        input_type: One of "text", "audio", "image" (default: "text").
    
    Returns:
        A dict with keys: intent, query, answer, chunks, (optionally: document).
    """
    state: PipelineState = {"text": query, "input_type": input_type}
    return run_pipeline(state)


def run_query_pipeline_with_audio(audio_bytes: bytes) -> dict[str, Any]:
    """
    Runs the full AI pipeline starting from audio transcription.
    
    Args:
        audio_bytes: Raw audio bytes to transcribe and process.
    
    Returns:
        A dict with keys: intent, query, answer, chunks.
    """
    state: PipelineState = {"audio_bytes": audio_bytes, "input_type": "audio", "text": ""}
    return run_pipeline(state)


def run_query_pipeline_with_document(file_bytes: bytes) -> dict[str, Any]:
    """
    Runs the full AI pipeline starting from document extraction.
    
    Args:
        file_bytes: Raw file bytes to extract and process.
    
    Returns:
        A dict with keys: intent, query, answer, chunks, document.
    """
    state: PipelineState = {"image_bytes": file_bytes, "input_type": "image", "text": ""}
    return run_pipeline(state)


def get_missing_fields(doc_type: str, known_fields: dict) -> list[str]:
    """
    Returns a list of fields still needed to complete a legal document draft.
    
    Args:
        doc_type: Type of document (e.g., "legal_notice", "wage_complaint").
        known_fields: Dict of fields already provided by the user.
    
    Returns:
        List of field names that are still required.
    """
    return missing_fields(doc_type, known_fields)

