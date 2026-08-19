from backend.ai.lawyers import match_lawyers
from backend.database import Base, engine, SessionLocal
from backend.models.database import Lawyer


def test_weighted_lawyer_matching():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.query(Lawyer).delete()
    db.add_all(
        [
            Lawyer(
                name="Asha",
                specialization="labour",
                jurisdiction="india",
                state="Karnataka",
                district="Bengaluru",
                languages=["en", "kn"],
                years_experience=12,
                legal_aid=True,
                pro_bono=True,
                verified=True,
            ),
            Lawyer(
                name="Vikram",
                specialization="criminal",
                jurisdiction="india",
                state="Delhi",
                languages=["en"],
                years_experience=3,
                legal_aid=False,
                pro_bono=False,
                verified=False,
            ),
        ]
    )
    db.commit()
    matches = match_lawyers(db, {"legal_domain": "labour", "state": "Karnataka", "language": "en"})
    db.close()
    assert matches[0]["name"] == "Asha"
    assert matches[0]["match_score"] > 0
