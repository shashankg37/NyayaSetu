from backend.eval.generation import evaluate_generation
from backend.eval.metrics import precision_at_k, recall_at_k
from backend.rag.fusion import rrf_merge


def test_hybrid_beats_single_list_on_fixture():
    dense = [{"chunk_id": "gold", "retrieval_source": "qdrant"}, {"chunk_id": "noise1", "retrieval_source": "qdrant"}]
    sparse = [{"chunk_id": "noise2", "retrieval_source": "bm25"}, {"chunk_id": "gold", "retrieval_source": "bm25"}]
    fused = rrf_merge(dense, sparse, top_k=2)
    relevant = {"gold"}
    assert recall_at_k(relevant, fused, 1) >= recall_at_k(relevant, dense, 1)
    assert precision_at_k(relevant, fused, 1) >= precision_at_k(relevant, sparse, 1)


def test_generation_metrics_are_measured_not_invented():
    report = evaluate_generation(
        [
            {
                "answer": {
                    "your_right": "Wages are due.",
                    "what_law_says": "pay wages on the due date",
                    "what_you_can_do": ["Contact DLSA"],
                    "citations": [{"act": "Code on Wages", "section": "17"}],
                    "fallback_used": False,
                },
                "chunks": [{"original_text": "The employer shall pay wages on the due date."}],
            },
            {
                "answer": {"your_right": "No evidence", "fallback_used": True, "what_you_can_do": ["Ask DLSA"]},
                "chunks": [],
            },
        ]
    )
    assert report["n"] == 2
    assert 0 <= report["hallucination_rate"] <= 1
