"""Nyaya Setu — internal AI & multimodal test console.

DEVELOPMENT / TESTING ONLY. Not a production frontend.
Calls existing backend modules; does not mock AI responses.
"""
from __future__ import annotations

import json
import sys
import traceback
import uuid
from collections import Counter
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import streamlit as st

st.set_page_config(
    page_title="Nyaya Setu AI Test Console",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

SECRET_FIELD_NAMES = {
    "hf_api_key",
    "gemini_api_key",
    "sarvam_api_key",
    "secret_key",
    "password",
    "token",
    "api_key",
    "access_token",
    "authorization",
}

TEST_CASES = {
    "TEST 1 — Wages": {
        "question": "My employer has not paid my wages on the due date. What are my rights?",
        "module": "Chat",
    },
    "TEST 2 — Wage deduction": {
        "question": "My employer deducted money from my wages. Is that allowed?",
        "module": "Chat",
    },
    "TEST 3 — General": {
        "question": "What is an employment contract?",
        "module": "Chat",
    },
    "TEST 4 — Unsupported / no hallucination": {
        "question": "What is the law regarding a completely unrelated topic that is not present in the knowledge base?",
        "module": "Chat",
    },
    "TEST 5 — Evidence (due date)": {
        "question": "Are wages required to be paid on the due date?",
        "evidence_text": "The employer shall pay or cause to be paid wages to the employees on the due date.",
        "module": "Evidence Gate",
    },
    "TEST 6 — Weak evidence": {
        "question": "Can I claim damages for a hypothetical issue with no statute in the knowledge base?",
        "evidence_text": "Someone once said wages might be paid sometime.",
        "weak": True,
        "module": "Evidence Gate",
    },
    "TEST 7 — Multimodal": {
        "question": "What are the important dates and sections mentioned in this document?",
        "module": "Multimodal",
    },
    "TEST 8 — Voice": {
        "question": "My employer has not paid my salary for two months. What can I do?",
        "module": "Voice",
    },
    "TEST 9 — Conversation memory": {
        "question": "My employer has not paid my salary.",
        "followup": "This has been happening for two months.",
        "module": "Chat",
    },
}

CHAT_EXAMPLES = [
    "What are my rights if my employer has not paid my wages?",
    "Can an employer deduct wages without informing the employee?",
    "I want to understand my legal rights in simple language.",
]

DRAFT_TYPE_OPTIONS = {
    "Complaint (wage)": "wage_complaint",
    "Complaint (consumer)": "consumer_complaint",
    "Legal notice": "legal_notice",
    "Application (RTI)": "rti",
    "Grievance": "government_grievance",
}

PIPELINE_STEPS = [
    "INPUT",
    "LANGUAGE",
    "CONVERSATION STATE",
    "SAFETY",
    "INTENT",
    "RETRIEVAL",
    "EVIDENCE GATE",
    "ROUTER",
    "GENERATION",
    "FINAL ANSWER",
]


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            if str(key).lower() in SECRET_FIELD_NAMES or "password" in str(key).lower() or str(key).lower().endswith("_key"):
                out[key] = "***REDACTED***" if item else ""
            else:
                out[key] = _redact(item)
        return out
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, bytes):
        return f"<bytes:{len(value)}>"
    return value


def _jsonable(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items() if k != "db_session"}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, bytes):
        return f"<bytes:{len(value)}>"
    if isinstance(value, Path):
        return str(value)
    return str(value)


def raw_json(value: Any) -> str:
    return json.dumps(_redact(_jsonable(value)), indent=2, ensure_ascii=False, default=str)


def fail_box(reason: str, action: str, module: str | None = None) -> None:
    st.error("TEST FAILED")
    st.markdown(f"**Reason:** {reason}")
    if module:
        st.markdown(f"**Module:** `{module}`")
    st.markdown(f"**Recommended action:** {action}")


def show_exception(exc: BaseException, module: str) -> None:
    fail_box(str(exc) or type(exc).__name__, _recommend(exc, module), module)
    st.markdown(f"**Exception type:** `{type(exc).__name__}`")
    st.markdown(f"**Error message:** {exc}")
    st.markdown(f"**Relevant module:** `{module}`")
    if st.session_state.get("show_traceback"):
        st.code("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)), language="text")
    else:
        st.caption("Enable **Show technical traceback** in the sidebar for a full stack trace.")


def _recommend(exc: BaseException, module: str) -> str:
    text = f"{type(exc).__name__}: {exc}".lower()
    if "hf" in text or "huggingface" in text or "401" in text or "403" in text:
        return "Confirm HF authentication in environment settings (do not paste secrets here) and retry."
    if "qdrant" in text:
        return "Start Qdrant at the configured URL, or use BM25-only retrieval while Qdrant is down."
    if "sarvam" in text or "stt" in text or "tts" in text or "speech" in text:
        return "Check Sarvam configuration and audio/text input; retry STT/TTS independently."
    if "empty" in text or "invalid audio" in text:
        return "Upload a supported non-empty audio file (wav/mp3/ogg/m4a)."
    if "pickle" in text or "bm25" in text:
        return "Rebuild the BM25 index with the ingestion script, then retry."
    if "database" in text or "sql" in text:
        return "Verify DATABASE_URL and that the database is reachable. Chat can still run in-session without persistence."
    if module.startswith("backend.ai.llm"):
        return "Check LLM provider/model configuration and network access to the inference endpoint."
    if module.startswith("backend.ai.vision"):
        return "Confirm the vision/LLM multimodal path, file type, and that the file is not empty."
    return f"Inspect `{module}` output in RAW OUTPUT, fix the failing dependency, and rerun this test."


def run_safe(label: str, module: str, fn: Callable[[], Any]) -> tuple[bool, Any]:
    try:
        result = fn()
        if result is None:
            fail_box(
                f"{label} returned None (no silent success).",
                _recommend(RuntimeError(f"{label} returned None"), module),
                module,
            )
            return False, None
        return True, result
    except Exception as exc:  # noqa: BLE001 — console must surface every backend failure
        show_exception(exc, module)
        return False, None


def chunk_score(chunk: dict[str, Any]) -> float:
    for key in ("confidence", "rerank_score", "fusion_score", "score"):
        value = chunk.get(key)
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
    return 0.0


def chunk_source(chunk: dict[str, Any]) -> str:
    sources = chunk.get("retrieval_sources")
    if isinstance(sources, list) and sources:
        return ", ".join(str(item) for item in sources)
    return str(chunk.get("retrieval_source") or "unknown")


def render_answer(answer: dict[str, Any] | None) -> None:
    if not answer:
        fail_box("Backend returned no answer payload.", "Inspect the pipeline RAW OUTPUT and LLM/evidence status.", "backend.ai.graph")
        return
    st.markdown("##### Your Right")
    st.write(answer.get("your_right") or "—")
    st.markdown("##### What the Law Says")
    st.write(answer.get("what_law_says") or "—")
    st.markdown("##### What This Means")
    st.write(answer.get("what_this_means") or "—")
    st.markdown("##### What You Can Do")
    can_do = answer.get("what_you_can_do")
    if isinstance(can_do, list):
        for item in can_do:
            st.markdown(f"- {item}")
    elif can_do:
        st.write(can_do)
    else:
        st.write("—")
    st.markdown("##### Sources")
    citations = answer.get("citations") or answer.get("source")
    if citations:
        st.json(_jsonable(citations))
    else:
        st.write("—")
    if answer.get("draft_text"):
        st.markdown("##### Generated draft")
        st.text_area("draft_text", value=str(answer["draft_text"]), height=240, label_visibility="collapsed")
    st.markdown("##### Evidence Status")
    st.write(answer.get("evidence_status") or st.session_state.get("_last_evidence_status") or "—")
    st.markdown("##### Disclaimer")
    st.info(answer.get("disclaimer") or "This is legal awareness information, not legal advice.")
    if answer.get("fallback_used"):
        st.warning("Fallback used by the backend (not a mock).")
    if answer.get("service_error"):
        st.error("Backend reported a service error.")


def raw_expander(title: str, payload: Any) -> None:
    with st.expander(title, expanded=False):
        st.code(raw_json(payload), language="json")


def status_pill(label: str, state: str, detail: str = "") -> None:
    color = {"connected": "#16a34a", "available": "#16a34a", "failed": "#dc2626", "fallback": "#d97706"}.get(state, "#6b7280")
    caption = {"connected": "Connected", "available": "Available", "failed": "Failed", "fallback": "Fallback"}.get(state, state)
    extra = f" — {detail}" if detail else ""
    st.markdown(
        f"<div style='padding:8px 12px;border:1px solid #e5e7eb;border-radius:8px;margin-bottom:8px;'>"
        f"<span style='color:{color};font-size:18px'>●</span> "
        f"<b>{label}</b>: {caption}{extra}</div>",
        unsafe_allow_html=True,
    )


@st.cache_resource
def load_settings_cached():
    from backend.config import get_settings

    return get_settings()


@st.cache_resource
def warmup_embedding_model():
    from backend.rag.ingestion import _load_model

    return _load_model()


@st.cache_resource
def warmup_cross_encoder():
    from backend.rag.reranker import _load_cross_encoder

    return _load_cross_encoder()


@st.cache_data(ttl=20)
def probe_qdrant() -> dict[str, Any]:
    from backend.config import SETTINGS
    from backend.rag.qdrant_store import collection_exists, ping_qdrant

    try:
        ok = ping_qdrant()
        exists = collection_exists() if ok else False
        return {
            "ok": ok,
            "collection_exists": exists,
            "collection": SETTINGS.qdrant_collection,
            "url_configured": bool(SETTINGS.qdrant_url),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


@st.cache_data(ttl=20)
def probe_database() -> dict[str, Any]:
    from sqlalchemy import text

    from backend.config import SETTINGS
    from backend.database import engine

    scheme = (SETTINGS.database_url or "").split("://", 1)[0]
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"ok": True, "scheme": scheme}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "scheme": scheme, "error": f"{type(exc).__name__}: {exc}"}


def ensure_session() -> None:
    st.session_state.setdefault("show_traceback", False)
    st.session_state.setdefault("conversation_id", str(uuid.uuid4()))
    st.session_state.setdefault("chat_history", [])
    st.session_state.setdefault("pipeline_state", {})
    st.session_state.setdefault("chat_turns", [])
    st.session_state.setdefault("last_retrieval", [])
    st.session_state.setdefault("prefill_question", TEST_CASES["TEST 1 — Wages"]["question"])
    st.session_state.setdefault("prefill_evidence", "")


def apply_test_case() -> None:
    case = TEST_CASES.get(st.session_state.get("selected_test_case") or "", {})
    if case.get("question"):
        st.session_state.prefill_question = case["question"]
        st.session_state.chat_question_box = case["question"]
        st.session_state.rag_query = case["question"] if "TEST 4" not in (st.session_state.get("selected_test_case") or "") else "payment of wages due date"
        st.session_state.langgraph_question = case["question"]
        st.session_state.multimodal_question = case.get("question", "")
        st.session_state.evidence_question = case["question"]
        st.session_state.tts_text = case["question"]
    if case.get("evidence_text"):
        st.session_state.prefill_evidence = case["evidence_text"]
        st.session_state.manual_evidence = case["evidence_text"]
    if case.get("weak"):
        st.session_state.manual_evidence = case.get("evidence_text") or "weak unofficial note"
    if case.get("followup"):
        st.session_state.followup_hint = case["followup"]


def render_header() -> None:
    st.markdown(
        """
        <div style="margin-bottom:8px">
          <div style="font-size:13px;letter-spacing:0.12em;color:#4b5563;">DEVELOPMENT / TESTING ONLY</div>
          <h1 style="margin:0;font-size:2rem;">NYAYA SETU</h1>
          <div style="font-size:1.15rem;font-weight:600;">AI &amp; MULTIMODAL TEST CONSOLE</div>
          <p style="color:#4b5563;margin-top:4px;">Validate the complete legal AI pipeline before frontend integration.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    try:
        settings = load_settings_cached()
        settings_ok = True
        settings_error = ""
    except Exception as exc:  # noqa: BLE001
        settings = None
        settings_ok = False
        settings_error = f"{type(exc).__name__}: {exc}"

    qdrant = probe_qdrant() if settings_ok else {"ok": False}
    db = probe_database() if settings_ok else {"ok": False}

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        status_pill("Backend Status", "connected" if settings_ok else "failed", "" if settings_ok else settings_error[:80])
    with c2:
        status_pill("AI Provider", "available" if settings_ok and getattr(settings, "llm_provider", None) else "failed", getattr(settings, "llm_provider", "unconfigured") if settings else "")
    with c3:
        status_pill("Model", "available" if settings_ok else "failed", getattr(settings, "llm_model", "") if settings else "")
    with c4:
        status_pill("Database", "connected" if db.get("ok") else "failed", db.get("scheme", ""))
    with c5:
        status_pill("Qdrant", "connected" if qdrant.get("ok") else "failed", qdrant.get("collection", "") if qdrant.get("ok") else "")
    with c6:
        embed = getattr(settings, "embedding_model", "") if settings else ""
        short = embed.split("/")[-1] if embed else ""
        status_pill("Embedding Model", "available" if settings_ok and embed else "failed", short)


def persist_chat(user_text: str, result: dict[str, Any]) -> None:
    answer = result.get("answer") or {}
    assistant_text = str(answer.get("your_right") or answer)
    st.session_state.chat_history.append({"role": "user", "content": user_text})
    st.session_state.chat_history.append({"role": "assistant", "content": assistant_text})
    st.session_state.chat_turns.append({"user": user_text, "result": result, "at": datetime.utcnow().isoformat()})
    persistable = {k: v for k, v in result.items() if k not in {"chunks", "retrieved_chunks", "reranked_chunks", "document"}}
    persistable["collected_information"] = result.get("collected_information") or {}
    persistable["current_issue"] = result.get("current_issue")
    persistable["pending_slot"] = result.get("pending_slot")
    st.session_state.pipeline_state = persistable
    st.session_state._last_evidence_status = result.get("evidence_status")


def page_chat() -> None:
    from backend.ai.graph import run_query_pipeline

    st.subheader("AI LEGAL ASSISTANT")
    left, right = st.columns([3, 1])
    with left:
        if "chat_question_box" not in st.session_state:
            st.session_state.chat_question_box = st.session_state.get("prefill_question") or CHAT_EXAMPLES[0]

        def _apply_example() -> None:
            choice = st.session_state.get("chat_example")
            if choice and choice != "(custom)":
                st.session_state.chat_question_box = choice

        st.selectbox("Example test questions", ["(custom)"] + CHAT_EXAMPLES, key="chat_example", on_change=_apply_example)
        question = st.text_area("Text question", height=100, key="chat_question_box")
    with right:
        st.text_input("Conversation ID", value=st.session_state.conversation_id, disabled=True)
        if st.button("Reset conversation"):
            st.session_state.conversation_id = str(uuid.uuid4())
            st.session_state.chat_history = []
            st.session_state.pipeline_state = {}
            st.session_state.chat_turns = []
            st.rerun()
        st.caption("Conversation state is kept in this Streamlit session and passed into `run_query_pipeline` (same contract as the API).")

    if st.session_state.get("followup_hint"):
        st.info(f"TEST 9 follow-up after first send: {st.session_state.followup_hint}")

    send = st.button("Send", type="primary")
    if send:
        text = (question or "").strip()
        if not text:
            fail_box("Empty query.", "Enter a legal question before sending.", "backend.ai.graph.run_query_pipeline")
        else:
            ok, result = run_safe(
                "Chat pipeline",
                "backend.ai.graph.run_query_pipeline",
                lambda: run_query_pipeline(
                    text,
                    input_type="text",
                    conversation_history=list(st.session_state.chat_history),
                    conversation_state=dict(st.session_state.pipeline_state),
                ),
            )
            if ok and result:
                persist_chat(text, result)

    for turn in st.session_state.chat_turns:
        st.markdown("**USER**")
        st.write(turn["user"])
        st.markdown("**NYAYA SETU**")
        result = turn["result"]
        st.caption(
            f"Evidence: {result.get('evidence_status') or 'n/a'} · "
            f"Intent: {result.get('intent') or 'n/a'} · "
            f"Next: {result.get('next_action') or 'n/a'}"
        )
        render_answer(result.get("answer"))
        raw_expander("RAW RESPONSE", result)

    if st.session_state.chat_history:
        with st.expander("Conversation memory (passed to the next request)"):
            st.json(_jsonable(st.session_state.chat_history))
            st.json(_jsonable(st.session_state.pipeline_state))


def display_chunks(chunks: list[dict[str, Any]]) -> None:
    if not chunks:
        fail_box("No retrieval results.", "Try another query, ingest sources, or check BM25/Qdrant diagnostics.", "backend.rag.retrieval")
        return
    scores = [chunk_score(item) for item in chunks]
    sources = Counter(chunk_source(item) for item in chunks)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Number of results", len(chunks))
    m2.metric("Highest score", f"{max(scores):.4f}" if scores else "0")
    m3.metric("Average score", f"{(sum(scores) / len(scores)):.4f}" if scores else "0")
    m4.write("**Source distribution**")
    m4.write(dict(sources))
    for rank, chunk in enumerate(chunks, start=1):
        with st.container(border=True):
            st.markdown(f"**Rank {rank}** · `{chunk.get('chunk_id') or '—'}`")
            c1, c2, c3 = st.columns(3)
            c1.write(f"Score: `{chunk_score(chunk):.4f}`")
            c2.write(f"Retrieval source: `{chunk_source(chunk)}`")
            c3.write(f"Document: {chunk.get('document_name') or chunk.get('source') or '—'}")
            st.write(f"Act: {chunk.get('act') or '—'} · Section: {chunk.get('section') or '—'}")
            st.write(chunk.get("original_text") or chunk.get("simplified_text") or "")


def page_rag() -> None:
    from backend.rag.bm25_search import rank_bm25, search_bm25
    from backend.rag.ingestion import embed_text
    from backend.rag.qdrant_store import search_qdrant
    from backend.rag.retrieval import retrieve, retrieve_ablation
    from backend.config import BM25_PATH
    from backend.rag.store import load_pickle

    tab_ret, tab_bm25 = st.tabs(["Hybrid / Qdrant / BM25 retrieval", "BM25 independent test"])
    with tab_ret:
        st.subheader("RAG TEST")
        query = st.text_input("Query", value=st.session_state.get("rag_query", "payment of wages due date"))
        top_k = st.slider("Top K", 1, 20, 5)
        method = st.radio("Retrieval method", ["Hybrid", "Qdrant", "BM25"], horizontal=True)
        rerank = st.checkbox("Rerank hybrid results (CrossEncoder)", value=True)
        if st.button("RUN RETRIEVAL", type="primary"):
            if not (query or "").strip():
                fail_box("Empty query.", "Enter a retrieval query.", "backend.rag.retrieval")
            else:
                def _run():
                    q = query.strip()
                    if method == "BM25":
                        return search_bm25(q, top_k=top_k)
                    if method == "Qdrant":
                        vector = embed_text(q)
                        return search_qdrant(vector, top_k=top_k)
                    if rerank:
                        return retrieve(q, final_k=top_k)
                    return retrieve_ablation(q, mode="rrf", final_k=top_k)

                ok, chunks = run_safe("Retrieval", "backend.rag.retrieval", _run)
                if ok:
                    st.session_state.last_retrieval = chunks or []
                    display_chunks(chunks or [])
                    raw_expander("RAW RESULTS", chunks)
        elif st.session_state.last_retrieval:
            st.caption("Last retrieval still in session (rerun to refresh).")
            display_chunks(st.session_state.last_retrieval)
            raw_expander("RAW RESULTS", st.session_state.last_retrieval)

    with tab_bm25:
        st.subheader("BM25 TEST")
        st.caption("Uses `rank_bm25` / `search_bm25`. This path does not call Qdrant.")
        qdrant = probe_qdrant()
        status_pill("Qdrant (not required)", "connected" if qdrant.get("ok") else "failed", "BM25 must still work if this is Failed")
        query = st.text_input("BM25 query", value="payment of wages due date", key="bm25_query")
        top_k = st.slider("Top K", 1, 20, 5, key="bm25_k")
        if st.button("RUN BM25", type="primary"):
            if not (query or "").strip():
                fail_box("Empty query.", "Enter a BM25 query.", "backend.rag.bm25_search")
            else:
                def _bm25():
                    indexed = search_bm25(query.strip(), top_k=top_k)
                    ranked = []
                    if BM25_PATH.exists():
                        data = load_pickle(BM25_PATH)
                        records = (data or {}).get("records") or []
                        ranked = rank_bm25(query.strip(), records, top_k=top_k)
                    return {"search_bm25": indexed, "rank_bm25": ranked, "index_path": str(BM25_PATH), "index_exists": BM25_PATH.exists()}

                ok, payload = run_safe("BM25", "backend.rag.bm25_search", _bm25)
                if ok and payload:
                    indexed = payload.get("search_bm25") or []
                    ranked = payload.get("rank_bm25") or []
                    independent_ok = payload.get("index_exists") and (indexed is not None) and (ranked is not None)
                    passed = bool(independent_ok and (indexed or ranked or payload.get("index_exists")))
                    if passed and (indexed or ranked):
                        st.success("BM25 independent retrieval: PASS")
                    elif passed and not indexed and not ranked:
                        st.warning("BM25 independent retrieval: PASS (index loaded, 0 hits for this query)")
                    else:
                        st.error("BM25 independent retrieval: FAIL")
                        fail_box(
                            "BM25 index missing or search failed.",
                            f"Create `{payload.get('index_path')}` via the ingestion script.",
                            "backend.rag.bm25_search",
                        )
                    rows = ranked or indexed
                    for chunk in rows:
                        with st.container(border=True):
                            st.write(f"**Chunk ID:** `{chunk.get('chunk_id')}` · **Score:** `{chunk_score(chunk):.4f}`")
                            st.write(f"Act: {chunk.get('act') or '—'} · Section: {chunk.get('section') or '—'}")
                            st.write(chunk.get("original_text") or "")
                    raw_expander("RAW OUTPUT", payload)


def _chunks_from_manual_text(text: str, weak: bool) -> list[dict[str, Any]]:
    body = (text or "").strip()
    if not body:
        return []
    if weak:
        return [
            {
                "chunk_id": "weak-1",
                "original_text": body,
                "confidence": 0.05,
                "rerank_score": 0.05,
                "source": "unofficial blog note",
                "document_name": "unverified note",
                "act": "",
                "section": "",
                "retrieval_source": "manual",
            }
        ]
    return [
        {
            "chunk_id": "manual-1",
            "original_text": body,
            "confidence": 0.82,
            "rerank_score": 0.82,
            "source": "Code on Wages official gazette",
            "document_name": "Code on Wages, 2019",
            "act": "Code on Wages, 2019",
            "section": "17",
            "retrieval_sources": ["qdrant", "bm25"],
        }
    ]


def page_evidence() -> None:
    from backend.ai.graph import evidence_gate_node, evidence_router
    from backend.rag.evidence_gate import evaluate_evidence
    from backend.rag.retrieval import retrieve

    st.subheader("EVIDENCE GATE")
    question = st.text_area(
        "Normalized question",
        value=st.session_state.get("evidence_question", st.session_state.get("prefill_question", "Are wages required to be paid on the due date?")),
        height=80,
    )
    mode = st.radio("Evidence source", ["A. Use actual retrieval results", "B. Manually enter test evidence"], horizontal=True)
    run_eval = False
    chunks: list[dict[str, Any]] = list(st.session_state.get("last_retrieval") or [])
    if mode.startswith("A"):
        st.caption(f"Cached retrieval chunks in session: {len(chunks)}")
        run_eval = st.button("Retrieve then evaluate", type="primary")
        if run_eval:
            if not (question or "").strip():
                fail_box("Empty query.", "Enter a normalized question.", "backend.rag.evidence_gate")
                return
            ok, chunks = run_safe("Retrieval for evidence gate", "backend.rag.retrieval.retrieve", lambda: retrieve(question.strip()))
            if not ok:
                return
            st.session_state.last_retrieval = chunks or []
    else:
        weak = st.checkbox("Use intentionally weak evidence (TEST 6)", value="TEST 6" in (st.session_state.get("selected_test_case") or ""))
        manual = st.text_area(
            "Manual evidence text",
            value=st.session_state.get("manual_evidence", st.session_state.get("prefill_evidence", "The employer shall pay or cause to be paid wages to the employees on the due date.")),
            height=120,
        )
        custom_json = st.text_area("Optional JSON chunks (overrides text)", value="", height=100)
        run_eval = st.button("Evaluate with evidence_gate_node + evidence_router", type="primary")
        if run_eval:
            if custom_json.strip():
                try:
                    parsed = json.loads(custom_json)
                    chunks = parsed if isinstance(parsed, list) else [parsed]
                except json.JSONDecodeError as exc:
                    show_exception(exc, "manual JSON")
                    return
            else:
                chunks = _chunks_from_manual_text(manual, weak)

    if run_eval:
        if not (question or "").strip():
            fail_box("Empty query.", "Enter a normalized question.", "backend.rag.evidence_gate")
            return
        decision_ok, decision = run_safe(
            "evaluate_evidence",
            "backend.rag.evidence_gate.evaluate_evidence",
            lambda: evaluate_evidence(question.strip(), chunks),
        )
        if not decision_ok:
            return
        node_ok, node_out = run_safe(
            "evidence_gate_node",
            "backend.ai.graph.evidence_gate_node",
            lambda: evidence_gate_node({"normalized_text": question.strip(), "chunks": chunks}),
        )
        if not node_ok:
            return
        route = evidence_router(node_out)
        route_label = {"refuse": "REFUSE", "clarify": "CLARIFY", "generate": "GENERATE"}.get(route, str(route).upper())
        color = {"REFUSE": "red", "CLARIFY": "orange", "GENERATE": "green"}.get(route_label, "gray")
        st.markdown(f"### Final routing decision: :{color}[{route_label}]")
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("confidence", f"{decision.confidence:.3f}")
        d2.metric("sufficient", str(decision.sufficient))
        d3.metric("status", decision.status)
        d4.metric("verdict", decision.verdict)
        st.write(f"**explanation:** {decision.explanation}")
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("cross_encoder score", f"{decision.confidence:.3f}")
        s2.metric("authority", decision.authority_hits)
        s3.metric("agreement", decision.agreement_hits)
        s4.metric("coverage", f"{decision.coverage:.3f}")
        if decision.sufficient:
            st.success("TEST STATUS: evidence accepted by the real gate")
        elif decision.status == "no_evidence":
            st.error("TEST STATUS: no_evidence → should REFUSE")
        else:
            st.warning("TEST STATUS: insufficient → should CLARIFY")
        raw_expander("RAW OUTPUT", {"decision": decision, "evidence_gate_node": node_out, "evidence_router": route, "chunks": chunks})


def _record_stage(stages: list[dict[str, Any]], name: str, fn: Callable[[], Any], module: str) -> Any:
    try:
        output = fn()
        stages.append({"name": name, "status": "ok", "output": output, "module": module})
        return output
    except Exception as exc:  # noqa: BLE001
        stages.append(
            {
                "name": name,
                "status": "failed",
                "output": None,
                "module": module,
                "exception_type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }
        )
        raise


def page_langgraph() -> None:
    from backend.ai.graph import (
        action_router,
        conversation_state_node,
        drafting_node,
        evidence_gate_node,
        evidence_router,
        generator_node,
        clarify_node,
        refuse_node,
        input_processor,
        intent_classifier,
        language_detector,
        lawyer_node,
        output_formatter,
        research_node,
        retriever_node,
        run_pipeline,
        safety_checker,
        unsupported_node,
        vision_node,
        general_generator_node,
    )
    from backend.ai.types import PipelineState
    from backend.ai.vision import extract_document

    st.subheader("LANGGRAPH PIPELINE")
    question = st.text_area("Question", value=st.session_state.get("langgraph_question", st.session_state.get("prefill_question", "")), height=80)
    history_raw = st.text_area("Optional conversation history (JSON list of {role, content})", value="[]", height=80)
    uploaded = st.file_uploader("Optional uploaded document", type=["png", "jpg", "jpeg", "webp", "pdf"])
    col_a, col_b = st.columns(2)
    step = col_a.button("Step through nodes", type="primary")
    compiled = col_b.button("Run compiled graph (`run_pipeline`)")

    if compiled:
        if not (question or "").strip() and uploaded is None:
            fail_box("Empty query and no document.", "Provide a question or upload a document.", "backend.ai.graph.run_pipeline")
            return
        try:
            history = json.loads(history_raw or "[]")
        except json.JSONDecodeError as exc:
            show_exception(exc, "conversation history JSON")
            return
        state: PipelineState = {
            "text": (question or "").strip(),
            "input_type": "image" if uploaded else "text",
            "conversation_history": history if isinstance(history, list) else [],
        }
        if uploaded:
            state["image_bytes"] = uploaded.getvalue()
        ok, result = run_safe("compiled graph", "backend.ai.graph.run_pipeline", lambda: run_pipeline(state))
        if ok:
            st.success("Compiled graph completed")
            render_answer((result or {}).get("answer") if isinstance(result, dict) else None)
            raw_expander("RAW OUTPUT", result)
        return

    if not step:
        st.caption("Run either stepper or compiled graph. Failures are not hidden.")
        return
    if not (question or "").strip() and uploaded is None:
        fail_box("Empty query and no document.", "Provide a question or upload a document.", "backend.ai.graph")
        return
    try:
        history = json.loads(history_raw or "[]")
        if not isinstance(history, list):
            raise ValueError("History must be a JSON list.")
    except Exception as exc:  # noqa: BLE001
        show_exception(exc, "conversation history JSON")
        return

    state: dict[str, Any] = {
        "text": (question or "").strip(),
        "current_message": (question or "").strip(),
        "input_type": "text",
        "conversation_history": history,
    }
    if uploaded is not None:
        file_bytes = uploaded.getvalue()
        ok_doc, document = run_safe("extract_document", "backend.ai.vision.extract_document", lambda: extract_document(file_bytes))
        if ok_doc and document:
            state["document"] = document
            state["uploaded_document"] = document
            query_extra = document.get("retrieval_query") or ""
            state["text"] = " ".join(part for part in [state["text"], query_extra] if part)

    stages: list[dict[str, Any]] = []
    failed_at = None
    try:
        out = _record_stage(stages, "INPUT", lambda: input_processor(state), "backend.ai.graph.input_processor")
        state.update(out or {})
        out = _record_stage(stages, "LANGUAGE", lambda: language_detector(state), "backend.ai.graph.language_detector")
        state.update(out or {})
        out = _record_stage(stages, "CONVERSATION STATE", lambda: conversation_state_node(state), "backend.ai.graph.conversation_state_node")
        state.update(out or {})
        out = _record_stage(stages, "SAFETY", lambda: safety_checker(state), "backend.ai.graph.safety_checker")
        state.update(out or {})
        out = _record_stage(stages, "INTENT", lambda: intent_classifier(state), "backend.ai.graph.intent_classifier")
        state.update(out or {})
        route = _record_stage(stages, "ACTION ROUTER", lambda: action_router(state), "backend.ai.graph.action_router")

        if route in {"unsafe", "emergency"}:
            stages.append({"name": "RETRIEVAL", "status": "skipped", "output": {"reason": f"action_router={route}"}})
            stages.append({"name": "EVIDENCE GATE", "status": "skipped", "output": {"reason": f"action_router={route}"}})
            stages.append({"name": "ROUTER", "status": "skipped", "output": {"reason": f"action_router={route}"}})
            stages.append({"name": "GENERATION", "status": "skipped", "output": {"reason": "safety short-circuit"}})
        elif route == "unsupported":
            out = _record_stage(stages, "GENERATION", lambda: unsupported_node(state), "backend.ai.graph.unsupported_node")
            state.update(out or {})
        elif route == "drafting":
            out = _record_stage(stages, "GENERATION", lambda: drafting_node(state), "backend.ai.graph.drafting_node")
            state.update(out or {})
        elif route == "research":
            out = _record_stage(stages, "GENERATION", lambda: research_node(state), "backend.ai.graph.research_node")
            state.update(out or {})
        elif route == "lawyers":
            out = _record_stage(stages, "GENERATION", lambda: lawyer_node(state), "backend.ai.graph.lawyer_node")
            state.update(out or {})
        elif route == "general":
            out = _record_stage(stages, "GENERATION", lambda: general_generator_node(state), "backend.ai.graph.general_generator_node")
            state.update(out or {})
        else:
            if route == "vision":
                out = _record_stage(stages, "RETRIEVAL", lambda: vision_node(state), "backend.ai.graph.vision_node")
            else:
                out = _record_stage(stages, "RETRIEVAL", lambda: retriever_node(state), "backend.ai.graph.retriever_node")
            state.update(out or {})
            out = _record_stage(stages, "EVIDENCE GATE", lambda: evidence_gate_node(state), "backend.ai.graph.evidence_gate_node")
            state.update(out or {})
            ev_route = _record_stage(stages, "ROUTER", lambda: evidence_router(state), "backend.ai.graph.evidence_router")
            if ev_route == "generate":
                out = _record_stage(stages, "GENERATION", lambda: generator_node(state), "backend.ai.graph.generator_node")
            elif ev_route == "clarify":
                out = _record_stage(stages, "GENERATION", lambda: clarify_node(state), "backend.ai.graph.clarify_node")
            else:
                out = _record_stage(stages, "GENERATION", lambda: refuse_node(state), "backend.ai.graph.refuse_node")
            state.update(out or {})
        out = _record_stage(stages, "FINAL ANSWER", lambda: output_formatter(state), "backend.ai.graph.output_formatter")
        state.update(out or {})
    except Exception:
        failed_at = next((item["name"] for item in stages if item.get("status") == "failed"), "unknown")

    st.markdown("#### Pipeline visualization")
    viz = "  \n↓  \n".join(PIPELINE_STEPS)
    st.code(viz, language="text")
    if failed_at:
        st.error(f"Stage failed: **{failed_at}**")
    present = {item["name"] for item in stages}
    for name in PIPELINE_STEPS:
        match = next((item for item in stages if item["name"] == name), None)
        if match is None and name == "RETRIEVAL" and "ACTION ROUTER" in present:
            match = next((item for item in stages if item["name"] in {"RETRIEVAL", "ACTION ROUTER"}), None)
        label = name
        if match is None:
            with st.expander(f"{label} — SKIPPED / NOT REACHED"):
                st.write("This stage was not executed (earlier failure or routing skip).")
            continue
        status = match.get("status", "ok")
        badge = {"ok": "STATUS: OK", "failed": "STATUS: FAILED", "skipped": "STATUS: SKIPPED"}.get(status, status)
        with st.expander(f"{label} — {badge}", expanded=status == "failed"):
            st.write(f"**STATUS:** {status}")
            if status == "failed":
                st.error(f"{match.get('exception_type')}: {match.get('error')}")
                st.caption(f"Module: `{match.get('module')}`")
                if st.session_state.get("show_traceback"):
                    st.code(match.get("traceback") or "", language="text")
            st.write("**OUTPUT**")
            st.json(_jsonable(match.get("output")))
    if "ACTION ROUTER" in present:
        with st.expander("ACTION ROUTER (intent routing) — detail"):
            st.json(_jsonable(next(item for item in stages if item["name"] == "ACTION ROUTER")))
    formatted = state.get("formatted") or output_formatter(state)
    st.markdown("#### Final response")
    render_answer((formatted or {}).get("answer") if isinstance(formatted, dict) else None)
    raw_expander("RAW OUTPUT", {"stages": stages, "final_state": formatted})


def _file_preview(uploaded) -> tuple[bytes, str, int]:
    data = uploaded.getvalue()
    mime = uploaded.type or "application/octet-stream"
    return data, mime, len(data)


def page_vision() -> None:
    from backend.ai.llm import generate_json_from_image
    from backend.ai.vision import extract_document, _detect_mime

    st.subheader("VISION / DOCUMENTS")
    tab_doc, tab_img = st.tabs(["Document extraction", "Image question"])
    with tab_doc:
        uploaded = st.file_uploader("Upload PNG / JPG / JPEG / WEBP / PDF", type=["png", "jpg", "jpeg", "webp", "pdf"], key="vision_doc")
        if uploaded and st.button("Run extract_document()", type="primary"):
            data, declared_mime, size = _file_preview(uploaded)
            if not data:
                fail_box("Invalid file: empty upload.", "Choose a non-empty PNG/JPG/WEBP/PDF.", "backend.ai.vision")
                return
            detected = _detect_mime(data)
            if declared_mime.startswith("image/"):
                st.image(data, caption=uploaded.name)
            else:
                st.caption("PDF preview is limited to extraction output (not a rendered page).")
            ok, result = run_safe("extract_document", "backend.ai.vision.extract_document", lambda: extract_document(data))
            if not ok or not result:
                return
            fields = result.get("extracted_fields") or {}
            c1, c2, c3 = st.columns(3)
            c1.write(f"**Detected MIME type:** `{detected}`")
            c2.write(f"**Declared MIME:** `{declared_mime}`")
            c3.write(f"**File size:** {size} bytes")
            st.write(f"**Document type:** {result.get('doc_type') or fields.get('document_type')}")
            st.write(f"**Vision error:** {result.get('vision_error') or 'None'}")
            st.write(f"**Fallback used:** {result.get('fallback_used')}")
            st.write(f"**Authoritative:** {result.get('authoritative')} (user documents are never law)")
            st.markdown("**Extracted text**")
            st.text_area("extracted_text", value=result.get("extracted_text") or "", height=120, label_visibility="collapsed")
            st.markdown("**Structured fields**")
            st.json(_jsonable(fields))
            st.write(f"**Retrieval query:** {result.get('retrieval_query')}")
            st.write(f"**Important facts:** {fields.get('important_facts')}")
            st.write(f"**Sections mentioned:** {fields.get('sections_mentioned')}")
            st.write(f"**Dates:** {fields.get('dates')}")
            st.write(f"**Parties:** {fields.get('parties')}")
            st.write(f"**Authorities:** {fields.get('authorities')}")
            st.write(f"**Deadlines:** {fields.get('deadlines')}")
            st.write(f"**Clauses:** {fields.get('clauses')}")
            raw_expander("RAW OUTPUT", result)

    with tab_img:
        st.caption("Photograph of a legal notice, screenshot of a government document, contract photo, or ID/document image.")
        image = st.file_uploader("Upload image", type=["png", "jpg", "jpeg", "webp"], key="vision_img")
        ask = st.text_input("Question", value="What does this document/image contain?")
        if image and st.button("Run multimodal image understanding", type="primary"):
            data, mime, size = _file_preview(image)
            st.image(data, caption=image.name)
            detected = _detect_mime(data)
            ok_ext, extraction = run_safe("extract_document", "backend.ai.vision.extract_document", lambda: extract_document(data))
            model_json = None
            try:
                model_json = generate_json_from_image(ask, data, detected if detected.startswith("image/") else mime)
            except Exception as exc:  # noqa: BLE001
                show_exception(exc, "backend.ai.llm.generate_json_from_image")
            if model_json is None:
                fail_box(
                    "Multimodal model returned no structured JSON.",
                    "Check HF multimodal support for the configured model. No invented answer is shown.",
                    "backend.ai.llm.generate_json_from_image",
                )
            ok_q = model_json is not None
            if ok_q and model_json:
                st.markdown("**Model response**")
                st.json(_jsonable(model_json))
            if ok_ext and extraction:
                st.markdown("**Structured extraction**")
                st.json(_jsonable(extraction.get("extracted_fields")))
                st.write(f"**Retrieval query:** {extraction.get('retrieval_query')}")
                st.write(f"**Errors:** {extraction.get('vision_error')}")
            raw_expander("RAW OUTPUT", {"mime": detected, "size": size, "question": ask, "model": model_json, "extract_document": extraction})


def page_voice() -> None:
    from backend.ai.graph import run_query_pipeline
    from backend.ai.speech import transcribe
    from backend.ai.tts import LANGUAGE_ALIASES, synthesize

    st.subheader("VOICE")
    st.markdown("AUDIO → STT → TRANSCRIPT → LEGAL PIPELINE → ANSWER")
    audio = st.file_uploader("Upload audio (wav / mp3 / ogg / m4a)", type=["wav", "mp3", "ogg", "m4a"])
    mic = None
    if hasattr(st, "audio_input"):
        mic = st.audio_input("Microphone recording (if supported by this Streamlit version)")
    source = audio or mic
    language = st.text_input("STT language_code (optional)", value="")
    send_to_chat = st.checkbox("After STT, send transcript into the legal chatbot", value=True)
    if st.button("Run speech → text", type="primary"):
        if source is None:
            fail_box("No audio provided.", "Upload a supported audio file or record with the microphone.", "backend.ai.speech")
        else:
            payload = source.getvalue()
            st.audio(payload)
            ok, transcript = run_safe(
                "STT",
                "backend.ai.speech.transcribe",
                lambda: transcribe(payload, source_language=language.strip() or None),
            )
            if ok and transcript is not None:
                st.markdown("### TRANSCRIPT")
                st.write(transcript)
                from backend.config import SETTINGS

                st.write(f"**Language:** `{language.strip() or SETTINGS.sarvam_default_language}`")
                st.write("**Provider:** Sarvam Saaras (`backend.ai.speech`)")
                st.write("**Errors:** None")
                st.write("**Fallback:** No")
                raw_expander("RAW OUTPUT", {"transcript": transcript, "bytes": len(payload)})
                if send_to_chat:
                    st.markdown("#### Legal pipeline")
                    ok2, result = run_safe(
                        "legal pipeline from transcript",
                        "backend.ai.graph.run_query_pipeline",
                        lambda: run_query_pipeline(str(transcript), conversation_history=list(st.session_state.chat_history), conversation_state=dict(st.session_state.pipeline_state)),
                    )
                    if ok2 and result:
                        persist_chat(str(transcript), result)
                        render_answer(result.get("answer"))
                        raw_expander("RAW PIPELINE OUTPUT", result)

    st.divider()
    st.markdown("TEXT → TTS → AUDIO PLAYER")
    tts_text = st.text_area("Input text", value=st.session_state.get("tts_text", "My employer has not paid my salary for two months. What can I do?"), height=80)
    tts_lang = st.selectbox("Target language", options=["en-IN", "hi-IN"] + sorted({v for v in LANGUAGE_ALIASES.values() if v not in {"en-IN", "hi-IN"}}))
    if st.button("Generate audio"):
        if not (tts_text or "").strip():
            fail_box("Empty text.", "Enter text for synthesis.", "backend.ai.tts")
        else:
            ok, audio_bytes = run_safe("TTS", "backend.ai.tts.synthesize", lambda: synthesize(tts_text.strip(), target_language=tts_lang))
            if ok and audio_bytes:
                st.audio(audio_bytes, format="audio/wav")
                st.success("TTS produced audio from the real Sarvam path.")
                raw_expander("RAW OUTPUT", {"bytes": len(audio_bytes), "language": tts_lang})


def page_multimodal() -> None:
    from backend.ai.llm import generate_answer
    from backend.ai.graph import evidence_gate_node, evidence_router
    from backend.ai.vision import extract_document
    from backend.rag.retrieval import retrieve

    st.subheader("MULTIMODAL")
    st.markdown("DOCUMENT → VISION → EXTRACTED INFORMATION → RETRIEVAL → EVIDENCE GATE → LEGAL RESPONSE")
    uploaded = st.file_uploader("Image / PDF upload", type=["png", "jpg", "jpeg", "webp", "pdf"], key="mm_file")
    question = st.text_area(
        "Text question",
        value=st.session_state.get("multimodal_question", "What does this notice require me to do and what deadline is mentioned?"),
        height=80,
    )
    if st.button("Run multimodal legal pipeline", type="primary"):
        if uploaded is None:
            fail_box("No document uploaded.", "Upload a wage notice or other legal document image/PDF.", "backend.ai.vision")
            return
        if not (question or "").strip():
            fail_box("Empty query.", "Enter a question about the document.", "backend.ai.graph")
            return
        data = uploaded.getvalue()
        if uploaded.type and uploaded.type.startswith("image/"):
            st.image(data, caption=uploaded.name)
        ok_doc, document = run_safe("VISION extract_document", "backend.ai.vision.extract_document", lambda: extract_document(data))
        if not ok_doc or not document:
            return
        st.markdown("### DOCUMENT FACTS (user document — non-authoritative)")
        st.info("User document: **Non-authoritative**. Uploaded files are facts about the user's situation, not law.")
        st.json(_jsonable(document.get("extracted_fields")))
        st.write(f"**Retrieval query from document:** {document.get('retrieval_query')}")
        retrieval_q = " ".join(part for part in [question.strip(), document.get("retrieval_query") or ""] if part)
        ok_ret, chunks = run_safe("RETRIEVAL", "backend.rag.retrieval.retrieve", lambda: retrieve(retrieval_q))
        if not ok_ret:
            return
        st.markdown("### LEGAL KNOWLEDGE (knowledge base)")
        display_chunks(chunks or [])
        ok_gate, gate = run_safe(
            "EVIDENCE GATE",
            "backend.ai.graph.evidence_gate_node",
            lambda: evidence_gate_node({"normalized_text": question.strip(), "chunks": chunks or []}),
        )
        if not ok_gate:
            return
        route = evidence_router(gate or {})
        authoritative = bool((gate or {}).get("evidence_sufficient")) and route == "generate"
        st.markdown(f"**Authoritative evidence:** {'Yes' if authoritative else 'No'}")
        st.markdown(f"**Evidence router:** `{route.upper()}`")
        st.json(_jsonable(gate))
        if route != "generate":
            fail_box(
                f"Evidence gate routed to {route.upper()}; legal generation was not run from weak/missing official sources.",
                "Add official knowledge-base evidence or ask a question covered by ingested Acts.",
                "backend.rag.evidence_gate",
            )
            raw_expander("RAW OUTPUT", {"document": document, "chunks": chunks, "gate": gate, "route": route})
            return
        ok_ans, answer = run_safe(
            "LEGAL RESPONSE",
            "backend.ai.llm.generate_answer",
            lambda: generate_answer(question.strip(), chunks or [], extracted_document=document),
        )
        if not ok_ans:
            return
        st.markdown("### AI INTERPRETATION (model output grounded on official chunks + document facts)")
        render_answer(answer)
        raw_expander("RAW OUTPUT", {"document": document, "chunks": chunks, "gate": gate, "route": route, "answer": answer})


def page_drafting() -> None:
    from backend.ai.drafting import DISCLAIMER, TEMPLATES, export_draft, render_draft, required_for
    from backend.ai.language import missing_fields

    st.subheader("LEGAL DRAFTING")
    label = st.selectbox("Document type", list(DRAFT_TYPE_OPTIONS.keys()))
    doc_type = DRAFT_TYPE_OPTIONS[label]
    purpose = st.text_input("Purpose", value="Unpaid wages / legal awareness draft")
    facts = st.text_area("Facts", height=100, value="Employer has not paid wages for two months.")
    jurisdiction = st.text_input("State / jurisdiction", value="Karnataka")
    extra = st.text_area("Optional additional details (JSON object of template fields)", value="{}", height=80)
    required = required_for(doc_type)
    st.caption(f"Required fields for `{doc_type}`: {', '.join(required)}")
    fields: dict[str, Any] = {}
    for field in required:
        default = ""
        if field in {"facts", "grievance", "information_sought"}:
            default = facts
        if field in {"location", "work_place"}:
            default = jurisdiction
        fields[field] = st.text_input(field, value=default, key=f"draft_{doc_type}_{field}")
    if st.button("Generate draft", type="primary"):
        try:
            more = json.loads(extra or "{}")
            if isinstance(more, dict):
                fields.update(more)
        except json.JSONDecodeError as exc:
            show_exception(exc, "additional details JSON")
            return
        fields.setdefault("facts", facts)
        missing = missing_fields(doc_type, fields)
        if missing:
            fail_box(
                f"Missing required fields: {', '.join(missing)}",
                "Fill the template slots required by backend.ai.drafting / language.REQUIRED_FIELDS.",
                "backend.ai.drafting",
            )
            raw_expander("RAW OUTPUT", {"doc_type": doc_type, "fields": fields, "missing": missing})
            return
        ok, body = run_safe("render_draft", "backend.ai.drafting.render_draft", lambda: render_draft(doc_type, fields))
        if not ok:
            return
        st.markdown("**Generated draft**")
        st.text_area("draft_body", value=body, height=280, label_visibility="collapsed")
        st.caption("Use the copy control on the code block below if you need the clipboard.")
        st.code(str(body), language="text")
        st.info(DISCLAIMER)
        st.caption(f"Template source: `backend.ai.drafting.TEMPLATES['{doc_type}']` · purpose: {purpose}")
        st.download_button("Download .txt", data=str(body).encode("utf-8"), file_name=f"{doc_type}.txt")
        ok_pdf, pdf_path = run_safe("export_draft pdf", "backend.ai.drafting.export_draft", lambda: export_draft(doc_type, fields, "pdf"))
        if ok_pdf and pdf_path:
            path = Path(pdf_path)
            if path.exists():
                st.download_button("Download PDF", data=path.read_bytes(), file_name=path.name, mime="application/pdf")
        raw_expander("RAW OUTPUT", {"doc_type": doc_type, "fields": fields, "body": body, "disclaimer": DISCLAIMER, "templates": list(TEMPLATES)})


def _component_row(name: str, status: str, details: str) -> dict[str, str]:
    return {"COMPONENT": name, "STATUS": status, "DETAILS": details}


def page_diagnostics() -> None:
    import platform

    st.subheader("SYSTEM DIAGNOSTICS")
    st.caption("Secrets are never displayed. Failures are shown explicitly.")
    rows: list[dict[str, str]] = []

    rows.append(_component_row("Python", "✓ AVAILABLE", f"{platform.python_version()} / {sys.executable}"))

    try:
        settings = load_settings_cached()
        rows.append(_component_row("Settings", "✓ AVAILABLE", f"env={settings.env} project={settings.project_name}"))
        rows.append(_component_row("HF API", "✓ CONFIGURED" if bool(settings.hf_api_key) else "✗ MISSING", "key present" if settings.hf_api_key else "hf_api_key is empty"))
        rows.append(_component_row("LLM provider", "✓ AVAILABLE", settings.llm_provider))
        rows.append(_component_row("LLM model", "✓ AVAILABLE", settings.llm_model))
        rows.append(_component_row("Embedding model", "✓ AVAILABLE", settings.embedding_model))
        rows.append(_component_row("Cross encoder (config)", "✓ AVAILABLE", settings.cross_encoder_model))
        rows.append(_component_row("STT model (config)", "✓ AVAILABLE" if settings.sarvam_stt_model else "✗ MISSING", settings.sarvam_stt_model or "unset"))
        rows.append(_component_row("TTS model (config)", "✓ AVAILABLE" if settings.sarvam_tts_model else "✗ MISSING", settings.sarvam_tts_model or "unset"))
        rows.append(_component_row("Sarvam API", "✓ CONFIGURED" if bool(settings.sarvam_api_key) else "⚠ NOT SET", "key present" if settings.sarvam_api_key else "sarvam_api_key is empty"))
        rows.append(_component_row("Vision provider", "⚠ FALLBACK" if not settings.hf_api_key else "✓ AVAILABLE", "Qwen multimodal via HuggingFaceProvider.generate_json_with_image"))
    except Exception as exc:  # noqa: BLE001
        settings = None
        rows.append(_component_row("Settings", "✗ FAILED", f"{type(exc).__name__}: {exc}"))
        show_exception(exc, "backend.config.get_settings")

    try:
        model = warmup_embedding_model()
        rows.append(_component_row("Embedding runtime", "✓ AVAILABLE" if model is not None else "⚠ FALLBACK", "SentenceTransformer loaded" if model is not None else "hash fallback embed_text"))
    except Exception as exc:  # noqa: BLE001
        rows.append(_component_row("Embedding runtime", "✗ FAILED", f"{type(exc).__name__}: {exc}"))

    try:
        ce = warmup_cross_encoder()
        rows.append(_component_row("Cross encoder runtime", "✓ AVAILABLE" if ce is not None else "⚠ FALLBACK", "CrossEncoder loaded" if ce is not None else "rerank will use fusion/score fallback"))
    except Exception as exc:  # noqa: BLE001
        rows.append(_component_row("Cross encoder runtime", "✗ FAILED", f"{type(exc).__name__}: {exc}"))

    from backend.config import BM25_PATH

    rows.append(_component_row("BM25", "✓ AVAILABLE" if BM25_PATH.exists() else "✗ MISSING", str(BM25_PATH)))

    qdrant = probe_qdrant()
    rows.append(
        _component_row(
            "QDRANT",
            "✓ CONNECTED" if qdrant.get("ok") else "✗ FAILED",
            qdrant.get("collection") if qdrant.get("ok") else qdrant.get("error", "unreachable"),
        )
    )
    db = probe_database()
    rows.append(_component_row("Database", "✓ CONNECTED" if db.get("ok") else "✗ FAILED", db.get("scheme", "") if db.get("ok") else db.get("error", "")))

    try:
        from backend.ai.graph import compiled_graph

        compiled_graph()
        rows.append(_component_row("LangGraph", "✓ AVAILABLE", "compiled_graph() succeeded"))
    except Exception as exc:  # noqa: BLE001
        rows.append(_component_row("LangGraph", "✗ FAILED", f"{type(exc).__name__}: {exc}"))

    st.dataframe(rows, use_container_width=True, hide_index=True)

    if st.button("Probe LLM (real generate_text_from_any)"):
        from backend.ai.llm import generate_text_from_any

        ok, text = run_safe("LLM probe", "backend.ai.llm.generate_text_from_any", lambda: generate_text_from_any("Reply with the single word PONG and nothing else."))
        if ok:
            if text:
                st.success("LLM probe returned text from the configured provider.")
                st.write(text)
            else:
                fail_box(
                    "LLM generate() returned empty/None.",
                    "Check provider, model id, and HF authentication. No mock answer is substituted.",
                    "backend.ai.llm",
                )
            raw_expander("RAW OUTPUT", {"text": text})

    if st.button("Probe BM25 search"):
        from backend.rag.bm25_search import search_bm25

        ok, hits = run_safe("BM25 probe", "backend.rag.bm25_search.search_bm25", lambda: search_bm25("wages", top_k=3))
        if ok:
            st.write(f"{len(hits or [])} hit(s)")
            raw_expander("RAW OUTPUT", hits)

    if st.button("Probe Qdrant search"):
        from backend.rag.ingestion import embed_text
        from backend.rag.qdrant_store import search_qdrant

        ok, hits = run_safe(
            "Qdrant probe",
            "backend.rag.qdrant_store.search_qdrant",
            lambda: search_qdrant(embed_text("wages"), top_k=3),
        )
        if ok:
            st.write(f"{len(hits or [])} hit(s)")
            raw_expander("RAW OUTPUT", hits)

    raw_expander(
        "RAW OUTPUT (redacted settings snapshot)",
        settings.model_dump() if settings is not None and hasattr(settings, "model_dump") else {"settings": "unavailable"},
    )


def main() -> None:
    ensure_session()
    with st.sidebar:
        st.markdown("### TEST MODULES")
        module = st.radio(
            "TEST MODULES",
            [
                "Chat",
                "RAG",
                "Evidence Gate",
                "LangGraph",
                "Vision / Documents",
                "Voice",
                "Multimodal",
                "Drafting",
                "System Diagnostics",
            ],
            label_visibility="collapsed",
        )
        st.divider()
        st.selectbox("Prepopulated test cases", list(TEST_CASES), key="selected_test_case", on_change=apply_test_case)
        st.checkbox("Show technical traceback", key="show_traceback")
        st.caption("This console is not a public production endpoint.")

    render_header()
    st.divider()
    pages = {
        "Chat": page_chat,
        "RAG": page_rag,
        "Evidence Gate": page_evidence,
        "LangGraph": page_langgraph,
        "Vision / Documents": page_vision,
        "Voice": page_voice,
        "Multimodal": page_multimodal,
        "Drafting": page_drafting,
        "System Diagnostics": page_diagnostics,
    }
    pages[module]()


main()
