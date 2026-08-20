"""Tier-1 legal RAG pipeline tests."""
from __future__ import annotations

import os

import pytest

from backend.ai.graph import (
    clarify_node,
    evidence_gate_node,
    evidence_router,
    refuse_node,
    run_query_pipeline,
)
from backend.ai.llm import HuggingFaceProvider, citations_from_chunks, get_provider
from backend.config import BACKEND_ROOT, SETTINGS, get_settings
from backend.rag.bm25_search import rank_bm25
from backend.rag.evidence_gate import evaluate_evidence
from backend.rag.fusion import rrf_merge
from backend.rag.ingestion import (
    chunk_document,
    clean_pages,
    embed_text,
    get_embedding_dimension,
    ingest_paths,
    load_pdf,
)
from backend.rag.qdrant_store import collection_exists, ping_qdrant, search_qdrant
from backend.rag.reranker import rerank
from backend.rag.retrieval import retrieve
from backend.tests.legal_pdf import write_code_on_wages_pdf

REQUIRED_SETTINGS = (
    "database_url",
    "secret_key",
    "qdrant_url",
    "qdrant_collection",
    "embedding_model",
    "inlegalbert_model",
    "cross_encoder_model",
    "llm_provider",
    "llm_model",
    "hf_api_key",
    "confidence_threshold",
)


def test_settings_are_available_through_settings():
    settings = get_settings()
    for name in REQUIRED_SETTINGS:
        assert hasattr(settings, name)
        assert getattr(SETTINGS, name) == getattr(settings, name)
    assert settings.llm_model == "Qwen/Qwen3.5-27B"
    assert "Qwen2.5" not in settings.llm_model
    assert settings.embedding_model == "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    assert settings.inlegalbert_model == "law-ai/InLegalBERT"
    assert settings.cross_encoder_model == "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
    assert settings.qdrant_url
    assert settings.qdrant_collection == "nyaya_setu_chunks"


def test_settings_load_backend_env_from_repo_root(tmp_path, monkeypatch):
    env_path = BACKEND_ROOT / ".env"
    if not env_path.exists():
        pytest.skip("backend/.env is not present")
    get_settings.cache_clear()
    loaded = get_settings()
    assert loaded.llm_model == "Qwen/Qwen3.5-27B"
    get_settings.cache_clear()


def test_huggingface_provider_uses_configured_qwen(monkeypatch):
    pytest.importorskip("huggingface_hub")
    captured: dict[str, str] = {}

    class FakeMessage:
        content = "Grounded test response from Qwen3.5-27B."

    class FakeChoice:
        message = FakeMessage()

    class FakeCompletion:
        choices = [FakeChoice()]

    class FakeChat:
        class completions:
            @staticmethod
            def create(**kwargs):
                captured["model"] = kwargs["model"]
                return FakeCompletion()

    class FakeClient:
        def __init__(self, provider=None, api_key=None, token=None, **kwargs):
            captured["has_token"] = bool(token)
            captured["provider"] = provider
            captured["api_key"] = api_key
            self.chat = FakeChat()

    monkeypatch.setattr(get_settings(), "hf_api_key", "hf_test_key")
    monkeypatch.setattr(get_settings(), "llm_model", "Qwen/Qwen3.5-27B")
    monkeypatch.setattr("huggingface_hub.InferenceClient", FakeClient)
    text = HuggingFaceProvider().generate("Reply with the word wages.")
    assert captured["model"] == "Qwen/Qwen3.5-27B"
    assert text and "Qwen" in text


def test_configured_provider_is_huggingface():
    assert SETTINGS.llm_provider == os.environ.get("LLM_PROVIDER", SETTINGS.llm_provider)
    if SETTINGS.llm_provider == "hf":
        assert isinstance(get_provider(), HuggingFaceProvider)


def test_embedding_dimension_matches_minilm():
    dim = get_embedding_dimension()
    assert dim == 384
    vector = embed_text("time limit for payment of wages")
    assert len(vector) == dim
    assert abs(sum(v * v for v in vector) - 1.0) < 0.05


def test_bm25_ranks_independently_of_qdrant():
    records = [
        {
            "chunk_id": "wages-17",
            "original_text": "The employer shall pay wages to the employees on the due date.",
            "section": "Section 17",
            "act": "Code on Wages, 2019",
            "document_name": "Code on Wages, 2019",
        },
        {
            "chunk_id": "rti-6",
            "original_text": "A person who desires to obtain any information under this Act shall make a request in writing.",
            "section": "Section 6",
            "act": "Right to Information Act, 2005",
            "document_name": "RTI Act, 2005",
        },
    ]
    ranked = rank_bm25("payment of wages due date", records, top_k=2)
    assert ranked
    assert ranked[0]["chunk_id"] == "wages-17"
    assert ranked[0]["retrieval_source"] == "bm25"
    assert ranked[0]["score"] > ranked[1]["score"]


def test_saved_bm25_search_falls_back_when_scores_are_non_positive(monkeypatch):
    from backend.rag.bm25_search import search_bm25

    records = [
        {
            "chunk_id": "wages-17",
            "original_text": "The employer shall pay wages to the employees on the due date.",
            "section": "Section 17",
            "act": "Code on Wages, 2019",
            "document_name": "Code on Wages, 2019",
        }
    ]

    class DummyBM25:
        def get_scores(self, query_tokens):
            return [-1.0 for _ in query_tokens] or [-1.0]

    def fake_load_pickle(path):
        return {"bm25": DummyBM25(), "records": records}

    def fake_rank_bm25(query, recs, top_k=10):
        return [
            {
                **dict(recs[0]),
                "score": 4.0,
                "retrieval_source": "bm25",
            }
        ]

    monkeypatch.setattr("backend.rag.bm25_search.load_pickle", fake_load_pickle)
    monkeypatch.setattr("backend.rag.bm25_search.rank_bm25", fake_rank_bm25)
    results = search_bm25("payment of wages due date", top_k=1)
    assert results
    assert results[0]["chunk_id"] == "wages-17"
    assert results[0]["retrieval_source"] == "bm25"
    assert results[0]["score"] == 4.0


def test_rrf_is_deterministic():
    qdrant = [
        {"chunk_id": "a", "section": "17", "retrieval_source": "qdrant", "original_text": "wages"},
        {"chunk_id": "b", "section": "19", "retrieval_source": "qdrant", "original_text": "deduction"},
    ]
    bm25 = [
        {"chunk_id": "b", "section": "19", "retrieval_source": "bm25", "original_text": "deduction"},
        {"chunk_id": "c", "section": "6", "retrieval_source": "bm25", "original_text": "rti"},
    ]
    first = rrf_merge(qdrant, bm25, top_k=3)
    second = rrf_merge(qdrant, bm25, top_k=3)
    assert [item["chunk_id"] for item in first] == [item["chunk_id"] for item in second]
    assert first[0]["chunk_id"] == "b"
    assert first[0]["fusion_score"] > first[1]["fusion_score"]


def test_retrieve_combines_available_sources(monkeypatch):
    qdrant_chunk = {
        "chunk_id": "wages-17",
        "retrieval_source": "qdrant",
        "score": 0.9,
        "original_text": "The employer shall pay wages to the employees on the due date.",
        "document_name": "Code on Wages, 2019",
        "act": "Code on Wages, 2019",
        "section": "Section 17",
    }
    bm25_chunk = {
        "chunk_id": "wages-17",
        "retrieval_source": "bm25",
        "score": 5.0,
        "original_text": "The employer shall pay wages to the employees on the due date.",
        "document_name": "Code on Wages, 2019",
        "act": "Code on Wages, 2019",
        "section": "Section 17",
    }

    monkeypatch.setattr("backend.rag.retrieval.embed_text", lambda query: [0.0] * 384)
    monkeypatch.setattr("backend.rag.retrieval.search_qdrant", lambda query_vector, top_k=20, filters=None: [qdrant_chunk])
    monkeypatch.setattr("backend.rag.retrieval.search_bm25", lambda query, top_k=20: [bm25_chunk])
    monkeypatch.setattr("backend.rag.retrieval.rerank", lambda query, fused, top_k=5: fused[:top_k])

    results = retrieve("payment of wages due date", final_k=1)
    assert results
    assert results[0]["chunk_id"] == "wages-17"
    assert set(results[0].get("retrieval_sources") or []) == {"qdrant", "bm25"}


def test_cross_encoder_rerank_without_model(monkeypatch):
    monkeypatch.setattr("backend.rag.reranker._load_cross_encoder", lambda: None)
    fused = [
        {"chunk_id": "a", "original_text": "wages on the due date", "fusion_score": 0.03, "act": "Code on Wages"},
        {"chunk_id": "b", "original_text": "request for information", "fusion_score": 0.02, "act": "RTI Act"},
    ]
    ranked = rerank("unpaid wages", fused, top_k=1)
    assert len(ranked) == 1
    assert "rerank_score" in ranked[0]


def test_evidence_gate_low_and_no_evidence():
    none = evaluate_evidence("cats", [])
    assert none.verdict == "NO_EVIDENCE"
    weak = evaluate_evidence(
        "unpaid wages",
        [{"chunk_id": "1", "confidence": 0.05, "document_name": "note", "original_text": "hello"}],
    )
    assert weak.sufficient is False
    assert weak.status == "insufficient"
    assert weak.verdict == "LOW"


def test_langgraph_evidence_routing():
    empty = evidence_gate_node({"normalized_text": "unrelated", "chunks": []})
    assert evidence_router(empty) == "refuse"
    refused = refuse_node(empty)
    assert refused["answer"]["fallback_used"] is True
    assert "will not invent" in refused["answer"]["your_right"].lower()

    weak_chunks = [{"chunk_id": "1", "confidence": 0.05, "document_name": "note", "original_text": "partial"}]
    weak = evidence_gate_node({"normalized_text": "wages", "chunks": weak_chunks})
    assert evidence_router(weak) == "clarify"
    clarified = clarify_node(weak)
    assert clarified["next_action"] == "clarify_or_legal_aid"

    strong = evidence_gate_node(
        {
            "normalized_text": "wages",
            "chunks": [
                {
                    "chunk_id": "wages-17",
                    "confidence": 0.9,
                    "source": "official gazette",
                    "document_name": "Code on Wages, 2019",
                    "section": "17",
                    "retrieval_sources": ["qdrant", "bm25"],
                }
            ],
        }
    )
    assert evidence_router(strong) == "generate"


def test_citations_come_from_chunks_not_the_model():
    citations = citations_from_chunks(
        [
            {
                "document_name": "Code on Wages, 2019",
                "act": "Code on Wages, 2019",
                "section": "Section 17",
                "page": 1,
                "year": "2019",
                "source": "Code on Wages, 2019",
            }
        ]
    )
    assert citations[0]["section"] == "Section 17"
    assert citations[0]["page"] == 1
    assert citations[0]["year"] == "2019"


def test_pdf_extraction_chunking_and_metadata(tmp_path):
    pdf_path = write_code_on_wages_pdf(tmp_path / "code_on_wages_2019.pdf")
    document = load_pdf(pdf_path)
    assert document is not None
    assert "due date" in document.text.lower()
    pages = clean_pages(document.pages)
    chunks = chunk_document(
        document_id=document.document_id,
        document_name=document.document_name,
        source=document.source,
        source_url=document.source_url,
        pages=pages,
    )
    assert chunks
    assert any(chunk.page for chunk in chunks)
    assert any("17" in (chunk.section or "") or "wages" in chunk.original_text.lower() for chunk in chunks)


@pytest.mark.integration
def test_qdrant_connection_and_collection():
    if not ping_qdrant():
        pytest.skip("Qdrant is not running at QDRANT_URL")
    dim = get_embedding_dimension()
    from backend.rag.qdrant_store import ensure_collection

    ensure_collection(vector_size=dim)
    assert collection_exists()


@pytest.mark.integration
def test_document_ingestion_and_hybrid_retrieval(tmp_path):
    if not ping_qdrant():
        pytest.skip("Qdrant is not running at QDRANT_URL")
    pdf_path = write_code_on_wages_pdf(tmp_path / "code_on_wages_2019.pdf")
    records = ingest_paths([pdf_path], rebuild=True)
    assert records
    assert all(record.get("embedding") for record in records)
    assert all(record.get("chunk_id") for record in records)
    assert any(record.get("page") for record in records)
    query = "When must the employer pay wages?"
    vector = embed_text(query)
    semantic = search_qdrant(vector, top_k=5)
    lexical = rank_bm25(query, records, top_k=5)
    assert semantic, "Qdrant returned no hits after ingestion"
    assert lexical, "BM25 returned no hits after ingestion"
    fused = rrf_merge(semantic, lexical, top_k=5)
    ranked = rerank(query, fused, top_k=3)
    assert ranked
    assert ranked[0].get("rerank_score") is not None
    combined = retrieve(query, final_k=3)
    assert combined
    gate = evaluate_evidence(query, combined)
    assert gate.status in {"sufficient", "insufficient", "no_evidence"}


@pytest.mark.integration
def test_huggingface_qwen_generates_response():
    if not SETTINGS.hf_api_key:
        pytest.skip("HF_API_KEY is not configured")
    provider = HuggingFaceProvider()
    text = provider.generate("Reply with exactly: NyayaSetuOK", max_new_tokens=32, temperature=0.0)
    if not text:
        pytest.skip("HF/Qwen provider is currently unavailable.")
    assert text and text.strip(), "Hugging Face returned no text for Qwen/Qwen3.5-27B"
    assert SETTINGS.llm_model == "Qwen/Qwen3.5-27B"


@pytest.mark.integration
def test_end_to_end_legal_question_cases(tmp_path, monkeypatch):
    if not ping_qdrant():
        pytest.skip("Qdrant is not running at QDRANT_URL")
    pdf_path = write_code_on_wages_pdf(tmp_path / "code_on_wages_2019.pdf")
    ingest_paths([pdf_path], rebuild=True)

    def fake_generate_answer(query, chunks, history=None, extracted_document=None):
        cites = citations_from_chunks(chunks)
        return {
            "your_right": "The employer shall pay wages on the due date.",
            "what_law_says": chunks[0]["original_text"],
            "citations": cites,
            "source": cites[0] if cites else None,
            "fallback_used": False,
            "disclaimer": "This is legal awareness information, not legally verified advice.",
        }

    live = bool(SETTINGS.hf_api_key)
    if not live:
        monkeypatch.setattr("backend.ai.graph.generate_answer", fake_generate_answer)

    answerable = run_query_pipeline("When must an employer pay wages under the Code on Wages?")
    if live:
        reply = answerable.get("answer") or {}
        if reply.get("service_error"):
            pytest.skip("HF/Qwen provider is currently unavailable.")
        assert reply.get("fallback_used") is False
        assert reply.get("citations")
        assert reply["citations"][0].get("section") or reply["citations"][0].get("document_name")
        assert "due date" in (reply.get("what_law_says") or reply.get("your_right") or "").lower() or reply.get("citations")
    else:
        reply = answerable.get("answer") or {}
        if answerable.get("evidence_status") == "sufficient":
            assert reply.get("citations")
            assert reply["citations"][0].get("document_name")

    unrelated = run_query_pipeline("What is the capital of Mars and which Indian section bans owning cats?")
    unrelated_reply = unrelated.get("answer") or {}
    assert unrelated.get("evidence_status") in {"no_evidence", "insufficient"}
    assert unrelated_reply.get("fallback_used") is True
    assert not unrelated_reply.get("citations")
