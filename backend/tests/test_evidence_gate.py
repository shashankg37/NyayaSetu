from backend.rag.evidence_gate import evaluate_evidence


def test_evidence_gate_rejects_empty_results():
    decision = evaluate_evidence("unpaid wages", [])
    assert decision.sufficient is False
    assert decision.status == "no_evidence"
    assert decision.verdict == "NO_EVIDENCE"


def test_evidence_gate_accepts_scored_official_chunk(monkeypatch):
    from backend.config import get_settings

    monkeypatch.setattr(get_settings(), "confidence_threshold", 0.4)
    monkeypatch.setattr(get_settings(), "evidence_coverage_min", 0.1)
    chunks = [
        {
            "chunk_id": "1",
            "confidence": 0.82,
            "fusion_score": 0.03,
            "source": "Code on Wages official gazette",
            "document_name": "Code on Wages, 2019",
            "section": "17",
            "retrieval_sources": ["qdrant", "bm25"],
        }
    ]
    decision = evaluate_evidence("unpaid wages", chunks)
    assert decision.sufficient is True
    assert decision.status == "sufficient"
    assert decision.verdict in {"HIGH", "SUFFICIENT"}
    assert decision.confidence == 0.82
