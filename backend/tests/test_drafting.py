from backend.ai.drafting import render_draft
from backend.ai.language import missing_fields


def test_rti_draft_requires_fields_then_renders(tmp_path, monkeypatch):
    fields = {
        "applicant_name": "Ravi",
        "address": "Bengaluru",
        "public_authority": "Labour Department",
        "information_sought": "Muster roll for January",
    }
    assert missing_fields("rti", {"applicant_name": "Ravi"}) != []
    text = render_draft("rti", fields)
    assert "Right to Information" in text
    assert "not legally verified" in text.lower() or "not legally verified" in text
