"""Conversational drafting for a small set of awareness templates."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from backend.ai.language import REQUIRED_FIELDS, detect_draft_type, missing_fields
from backend.config import get_settings

DISCLAIMER = (
    "This is an AI-generated draft for legal-awareness purposes. "
    "It is not legally verified and is not a substitute for professional legal advice."
)

TEMPLATES = {
    "rti": (
        "Application under the Right to Information Act, 2005\n\n"
        "To: The Public Information Officer\n{public_authority}\n\n"
        "From: {applicant_name}\n{address}\n\n"
        "Subject: Request for information\n\n"
        "I request the following information:\n{information_sought}\n\n"
        "Date: {today}\nSignature: {applicant_name}\n\n{disclaimer}"
    ),
    "wage_complaint": (
        "Complaint regarding unpaid wages\n\n"
        "Complainant: {worker_name}\nEmployer: {employer_name}\nWorkplace: {work_place}\n"
        "Period unpaid: {period_unpaid}\nAmount claimed: {amount}\n\n"
        "I request inquiry and payment of the wages due.\n\nDate: {today}\n\n{disclaimer}"
    ),
    "consumer_complaint": (
        "Consumer complaint\n\n"
        "Complainant: {complainant_name}\nOpposite party: {opposite_party}\n"
        "Goods/service: {goods_or_service}\nGrievance: {grievance}\nRelief sought: {relief_sought}\n\n"
        "Date: {today}\n\n{disclaimer}"
    ),
    "government_grievance": (
        "Grievance to government department\n\n"
        "Applicant: {applicant_name}\nDepartment: {department}\nLocation: {location}\n"
        "Grievance: {grievance}\n\nDate: {today}\n\n{disclaimer}"
    ),
    "legal_notice": (
        "Legal notice (draft)\n\n"
        "From: {sender_name}\nTo: {recipient_name}\n\nFacts: {facts}\nDemand: {demand}\n\n"
        "Date: {today}\n\n{disclaimer}"
    ),
}


def resolve_doc_type(text: str, known: dict[str, Any] | None = None) -> str | None:
    if known and known.get("doc_type"):
        return str(known["doc_type"])
    return detect_draft_type(text)


def required_for(doc_type: str) -> list[str]:
    return list(REQUIRED_FIELDS.get(doc_type, ["details"]))


def render_draft(doc_type: str, fields: dict[str, Any]) -> str:
    missing = missing_fields(doc_type, fields)
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")
    template = TEMPLATES[doc_type]
    payload = {**fields, "today": datetime.utcnow().date().isoformat(), "disclaimer": DISCLAIMER}
    return template.format_map({key: payload.get(key, "") for key in _format_keys(template)})


def _format_keys(template: str) -> set[str]:
    import string

    return set(name for _, name, _, _ in string.Formatter().parse(template) if name)


def export_draft(doc_type: str, fields: dict[str, Any], fmt: str = "pdf") -> Path:
    text = render_draft(doc_type, fields)
    root = get_settings().storage_root / "drafts"
    root.mkdir(parents=True, exist_ok=True)
    stem = f"{doc_type}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    if fmt == "docx":
        from docx import Document  # type: ignore

        path = root / f"{stem}.docx"
        document = Document()
        document.add_paragraph(text)
        document.save(path)
        return path

    from reportlab.lib.pagesizes import A4  # type: ignore
    from reportlab.pdfgen import canvas  # type: ignore

    path = root / f"{stem}.pdf"
    pdf = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    y = height - 50
    for line in text.splitlines():
        pdf.drawString(40, y, line[:110])
        y -= 14
        if y < 40:
            pdf.showPage()
            y = height - 50
    pdf.save()
    return path
