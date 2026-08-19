from fastapi.testclient import TestClient

from backend.database import Base, engine
from backend.main import app

client = TestClient(app)


def _headers():
    Base.metadata.create_all(bind=engine)
    client.post("/api/v1/auth/register", json={"email": "e2e@example.com", "password": "password123", "consent_given": True})
    token = client.post("/api/v1/auth/login", json={"email": "e2e@example.com", "password": "password123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


WAGE_CHUNK = {
    "chunk_id": "wages-17",
    "document_name": "Code on Wages, 2019",
    "act": "Code on Wages, 2019",
    "section": "17",
    "page": 12,
    "source_url": "https://example.invalid/code-on-wages",
    "source": "official gazette",
    "original_text": "The employer shall pay wages to the employees on the due date.",
    "confidence": 0.88,
    "retrieval_sources": ["qdrant", "bm25"],
}


def test_legal_question_grounded_path(monkeypatch):
    monkeypatch.setattr("backend.ai.graph.retrieve", lambda query, **kwargs: [WAGE_CHUNK])
    monkeypatch.setattr(
        "backend.ai.graph.generate_answer",
        lambda query, chunks, history=None, extracted_document=None: {
            "your_right": "You can seek payment of wages due.",
            "what_law_says": chunks[0]["original_text"],
            "citations": [{"document_name": "Code on Wages, 2019", "section": "17", "page": 12, "source_url": chunks[0]["source_url"]}],
            "fallback_used": False,
        },
    )
    headers = _headers()
    response = client.post("/api/v1/chat/message", json={"message": "My employer hasn't paid me for two months."}, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["reply"]["fallback_used"] is False
    assert body["reply"]["citations"][0]["section"] == "17"


def test_multi_turn_daily_wage(monkeypatch):
    monkeypatch.setattr("backend.ai.graph.retrieve", lambda query, **kwargs: [WAGE_CHUNK])
    monkeypatch.setattr(
        "backend.ai.graph.generate_answer",
        lambda query, chunks, history=None, extracted_document=None: {
            "your_right": f"Context kept: {query}",
            "citations": [{"document_name": "Code on Wages, 2019", "section": "17"}],
            "fallback_used": False,
        },
    )
    headers = _headers()
    first = client.post("/api/v1/chat/message", json={"message": "My employer hasn't paid me."}, headers=headers)
    conv_id = first.json()["conversation_id"]
    second = client.post(
        "/api/v1/chat/message",
        json={"conversation_id": conv_id, "message": "Daily wage."},
        headers=headers,
    )
    assert second.status_code == 200
    history = client.get(f"/api/v1/chat/{conv_id}/history", headers=headers).json()["history"]
    assert len(history) >= 4


def test_insufficient_evidence_does_not_hallucinate(monkeypatch):
    monkeypatch.setattr("backend.ai.graph.retrieve", lambda query, **kwargs: [])
    headers = _headers()
    response = client.post(
        "/api/v1/chat/message",
        json={"message": "Cite the section that bans owning cats in India."},
        headers=headers,
    )
    assert response.status_code == 200
    reply = response.json()["reply"]
    assert reply["fallback_used"] is True
    assert reply.get("citations") in ([], None)


def test_voice_turn_based(monkeypatch):
    monkeypatch.setattr("backend.ai.graph.transcribe", lambda audio: "My employer has not paid wages.")
    monkeypatch.setattr("backend.ai.graph.retrieve", lambda query, **kwargs: [WAGE_CHUNK])
    monkeypatch.setattr(
        "backend.ai.graph.generate_answer",
        lambda query, chunks, history=None, extracted_document=None: {
            "your_right": "Wages are due on the due date.",
            "citations": [{"section": "17"}],
            "fallback_used": False,
        },
    )
    monkeypatch.setattr("backend.api.voice.synthesize", lambda text, target_language="en": b"RIFFWAVE")
    headers = _headers()
    response = client.post(
        "/api/v1/voice/chat",
        headers=headers,
        files={"file": ("speech.wav", b"RIFF" + b"0" * 120, "audio/wav")},
    )
    assert response.status_code == 200
    assert "Wages" in response.json()["reply_text"]
    assert response.json()["reply_audio_b64"]
