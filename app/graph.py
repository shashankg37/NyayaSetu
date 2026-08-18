from __future__ import annotations

from typing import Any

from app.ai_stubs.draft_fields import missing_fields
from app.ai_stubs.generation import generate_answer
from app.ai_stubs.intent import classify_intent
from app.ai_stubs.retrieval import retrieve
from app.ai_stubs.speech import transcribe
from app.ai_stubs.vision import extract_document
from app.ai_stubs.common import normalize_text
from app.types import PipelineState


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

