from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.ai.lawyers import match_lawyers
from backend.api.deps import current_user
from backend.database import get_db
from backend.models.database import Lawyer, User
from backend.models.schemas.features import LawyerMatchRequest

router = APIRouter(prefix="/lawyers", tags=["lawyers"])


@router.get("")
def list_lawyers(db: Session = Depends(get_db), user: User = Depends(current_user)):
    del user
    lawyers = db.query(Lawyer).all()
    return [
        {
            "id": item.id,
            "name": item.name,
            "specialization": item.specialization,
            "jurisdiction": item.jurisdiction,
            "state": item.state,
            "district": item.district,
            "languages": item.languages,
            "years_experience": item.years_experience,
            "fee_min": item.fee_min,
            "fee_max": item.fee_max,
            "legal_aid": item.legal_aid,
            "pro_bono": item.pro_bono,
            "verified": item.verified,
        }
        for item in lawyers
    ]


@router.post("/match")
def match(payload: LawyerMatchRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    del user
    return {"matches": match_lawyers(db, payload.model_dump())}
