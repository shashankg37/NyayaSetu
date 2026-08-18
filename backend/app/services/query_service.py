from sqlalchemy.orm import Session
from app.ai_stubs.generation import generate_answer
from app.ai_stubs.intent import classify_intent
from app.ai_stubs.retrieval import retrieve
from app.ai_stubs.speech import transcribe
from app.models import InputType, Query, Response, Session as UserSession

def session_for(db: Session, session_id: int | None, user_id: int | None = None) -> UserSession:
    if session_id:
        session = db.get(UserSession, session_id)
        if not session: raise ValueError("Session not found")
        return session
    session = UserSession(user_id=user_id); db.add(session); db.flush(); return session

def answer(db: Session, text: str, input_type: InputType, session_id: int | None, user_id: int | None = None) -> dict:
    session = session_for(db, session_id, user_id)
    query = Query(session_id=session.id, raw_input_type=input_type, raw_input_ref=text, intent=classify_intent(text))
    chunks = retrieve(text); payload = generate_answer(text, chunks)
    db.add(query); db.flush(); db.add(Response(query_id=query.id, answer_payload=payload, confidence_score=payload['confidence'], fallback_used=payload['fallback_used'])); db.commit()
    return payload

def voice_answer(db: Session, audio: bytes, session_id: int | None, user_id: int | None = None) -> dict:
    return answer(db, transcribe(audio), InputType.voice, session_id, user_id)
