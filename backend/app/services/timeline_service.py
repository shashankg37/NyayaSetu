from sqlalchemy.orm import Session
from app.ai.ai_stubs.timeline import reconstruct_timeline
from app.models import Timeline
from app.services.query_service import session_for

def build(db: Session, narrative: str, session_id: int | None, user_id: int | None) -> Timeline:
    events = reconstruct_timeline(narrative)
    session = session_for(db, session_id, user_id); timeline = Timeline(session_id=session.id, events=events); db.add(timeline); db.commit(); db.refresh(timeline); return timeline
