"""Weighted matching against PostgreSQL lawyer profiles."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from backend.models.database import Lawyer


def match_lawyers(db: Session, criteria: dict[str, Any], limit: int = 5) -> list[dict[str, Any]]:
    query = db.query(Lawyer)
    if criteria.get("legal_aid_only"):
        query = query.filter((Lawyer.legal_aid.is_(True)) | (Lawyer.pro_bono.is_(True)))
    lawyers = query.all()
    scored: list[tuple[float, Lawyer]] = []
    for lawyer in lawyers:
        score = 0.0
        domain = (criteria.get("legal_domain") or "").lower()
        if domain and domain in (lawyer.specialization or "").lower():
            score += 0.3
        jurisdiction = (criteria.get("jurisdiction") or "").lower()
        if jurisdiction and jurisdiction in (lawyer.jurisdiction or "").lower():
            score += 0.2
        state = (criteria.get("state") or "").lower()
        if state and state == (lawyer.state or "").lower():
            score += 0.15
        district = (criteria.get("district") or "").lower()
        if district and district == (lawyer.district or "").lower():
            score += 0.05
        language = (criteria.get("language") or "").lower()
        languages = [str(item).lower() for item in (lawyer.languages or [])]
        if language and language in languages:
            score += 0.15
        score += min(lawyer.years_experience, 30) / 30 * 0.1
        if lawyer.legal_aid or lawyer.pro_bono:
            score += 0.05
        if lawyer.verified:
            score += 0.05
        scored.append((score, lawyer))
    scored.sort(key=lambda item: item[0], reverse=True)
    results = []
    for score, lawyer in scored[:limit]:
        if score <= 0:
            continue
        results.append(
            {
                "id": lawyer.id,
                "name": lawyer.name,
                "specialization": lawyer.specialization,
                "jurisdiction": lawyer.jurisdiction,
                "state": lawyer.state,
                "district": lawyer.district,
                "languages": lawyer.languages,
                "years_experience": lawyer.years_experience,
                "fee_min": lawyer.fee_min,
                "fee_max": lawyer.fee_max,
                "legal_aid": lawyer.legal_aid,
                "pro_bono": lawyer.pro_bono,
                "verified": lawyer.verified,
                "match_score": round(score, 3),
            }
        )
    if not results:
        for score, lawyer in scored[:limit]:
            results.append(
                {
                    "id": lawyer.id,
                    "name": lawyer.name,
                    "specialization": lawyer.specialization,
                    "jurisdiction": lawyer.jurisdiction,
                    "state": lawyer.state,
                    "languages": lawyer.languages,
                    "years_experience": lawyer.years_experience,
                    "legal_aid": lawyer.legal_aid,
                    "verified": lawyer.verified,
                    "match_score": round(score, 3),
                }
            )
    return results
