from backend.rag.fusion import rrf_merge


def test_rrf_combines_ranks_and_keeps_metadata():
    qdrant = [
        {"chunk_id": "a", "document_name": "Code on Wages", "section": "17", "retrieval_source": "qdrant"},
        {"chunk_id": "b", "document_name": "Code on Wages", "section": "19", "retrieval_source": "qdrant"},
    ]
    bm25 = [
        {"chunk_id": "b", "document_name": "Code on Wages", "section": "19", "retrieval_source": "bm25"},
        {"chunk_id": "c", "document_name": "RTI Act", "section": "6", "retrieval_source": "bm25"},
    ]
    fused = rrf_merge(qdrant, bm25, top_k=3)
    assert [item["chunk_id"] for item in fused][0] == "b"
    assert fused[0]["fusion_score"] > fused[1]["fusion_score"]
    assert "qdrant" in fused[0]["retrieval_sources"]
    assert "bm25" in fused[0]["retrieval_sources"]
    assert fused[0]["section"] == "19"
