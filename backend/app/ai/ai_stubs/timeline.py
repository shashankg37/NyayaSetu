from __future__ import annotations


def reconstruct_timeline(narrative: str) -> list[dict]:
    """Build a simple, explainable timeline from the user's narrative."""
    return [
        {"event": "Situation reported", "detail": narrative, "next_step": "Keep relevant documents and dates."},
        {
            "event": "Seek assistance",
            "detail": "Approach the appropriate authority or legal-aid service.",
            "next_step": "Submit a written representation.",
        },
    ]

