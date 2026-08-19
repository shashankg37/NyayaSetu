from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.ai.research import research
from backend.api.deps import current_user
from backend.database import get_db
from backend.models.database import User
from backend.models.schemas.features import ResearchRequest

router = APIRouter(prefix="/research", tags=["research"])


@router.post("/query")
def research_query(payload: ResearchRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    del db
    return research(payload.query)
