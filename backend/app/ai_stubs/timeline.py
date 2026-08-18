from app.ai.ai_stubs.timeline import reconstruct_timeline as ai_reconstruct_timeline


def reconstruct_timeline(narrative: str) -> list[dict]:
    """Later this will identify events, dates, and available next actions from a narrative."""
    return ai_reconstruct_timeline(narrative)
