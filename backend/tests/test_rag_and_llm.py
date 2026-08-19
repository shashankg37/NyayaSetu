from backend.ai.llm import generate_answer
from backend.eval.metrics import mrr, precision_at_k, recall_at_k
from backend.rag.ingestion import chunk_text_simple, clean_text
from backend.rag.reranker import rerank


def test_cleaning_and_chunking_preserve_section():
    raw = "THE GAZETTE OF INDIA\n\nSection 17. Time limit for payment of wages.\nThe employer shall pay wages on the due date.\n"
    cleaned = clean_text(raw)
    chunks = chunk_text_simple(cleaned, document_id="wages", document_name="Code on Wages", source="Code on Wages")
    assert chunks
    assert "GAZETTE" not in chunks[0].original_text
    assert chunks[0].chunk_id
    assert chunks[0].section


def test_rerank_without_model_returns_top_k(monkeypatch):
    monkeypatch.setattr("backend.rag.reranker._load_cross_encoder", lambda: None)
    items = [{"chunk_id": "1", "original_text": "wages"}, {"chunk_id": "2", "original_text": "rti"}]
    assert len(rerank("wages", items, top_k=1)) == 1


def test_retrieval_metrics_helpers():
    relevant = {"a"}
    retrieved = [{"chunk_id": "b"}, {"chunk_id": "a"}]
    assert recall_at_k(relevant, retrieved, 2) == 1.0
    assert precision_at_k(relevant, retrieved, 2) == 0.5
    assert mrr(relevant, retrieved) == 0.5


def test_llm_fallback_when_provider_unavailable(monkeypatch):
    monkeypatch.setattr("backend.ai.llm.generate_json_from_any", lambda prompt: None)
    result = generate_answer("unpaid wages", [{"original_text": "Section 17 wages", "act": "Code on Wages", "section": "17"}])
    assert result["fallback_used"] is True
    assert result["service_error"] is True
    assert result["citations"][0]["section"] == "17"
