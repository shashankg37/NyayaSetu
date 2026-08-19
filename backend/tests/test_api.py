import os

from fastapi.testclient import TestClient

from backend.database import Base, engine
from backend.main import app
from backend.models.database import Lawyer

client = TestClient(app)


def _auth_headers():
    Base.metadata.create_all(bind=engine)
    email = "citizen@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": "password123", "consent_given": True})
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health_and_auth_me():
    Base.metadata.create_all(bind=engine)
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    headers = _auth_headers()
    me = client.get("/api/v1/users/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "citizen@example.com"


def test_drafting_and_research_and_lawyers(monkeypatch):
    headers = _auth_headers()
    start = client.post("/api/v1/drafting/start", json={"doc_type": "rti", "known_fields": {}}, headers=headers)
    assert start.status_code == 201
    draft_id = start.json()["id"]
    client.post(
        f"/api/v1/drafting/{draft_id}/answer",
        json={
            "fields": {
                "applicant_name": "Ravi",
                "address": "Bengaluru",
                "public_authority": "PWD",
                "information_sought": "Bills for 2024",
            }
        },
        headers=headers,
    )
    generated = client.post(f"/api/v1/drafting/{draft_id}/generate", headers=headers)
    assert generated.status_code == 200
    assert generated.json()["draft_status"] == "generated"

    monkeypatch.setattr("backend.api.research.research", lambda query: {"query": query, "sufficient": False, "citations": []})
    researched = client.post("/api/v1/research/query", json={"query": "wages section 17"}, headers=headers)
    assert researched.status_code == 200

    from backend.database import SessionLocal

    db = SessionLocal()
    if not db.query(Lawyer).first():
        db.add(
            Lawyer(
                name="Asha",
                specialization="labour",
                jurisdiction="india",
                state="Karnataka",
                languages=["en"],
                years_experience=8,
                legal_aid=True,
                pro_bono=False,
                verified=True,
            )
        )
        db.commit()
    db.close()
    matched = client.post("/api/v1/lawyers/match", json={"legal_domain": "labour", "state": "Karnataka"}, headers=headers)
    assert matched.status_code == 200
    assert "matches" in matched.json()
