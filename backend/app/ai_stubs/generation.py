def generate_answer(query: str, chunks: list[dict]) -> dict:
    """Later this will create a cited, grounded answer from retrieved passages."""
    # TODO: replace with real AI logic
    return {"your_right": "You may seek help for unpaid wages.", "what_law_says": "Workers have protections concerning payment of wages.", "what_this_means": "Keep records of work and amounts due before approaching the relevant authority.", "what_you_can_do": ["Collect wage records", "Submit a written complaint", "Contact District Legal Services Authority if you need help"], "source": {"act": "Legal awareness material", "section": "Payment of wages guidance"}, "confidence": 0.78, "fallback_used": False}
