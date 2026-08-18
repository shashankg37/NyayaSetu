from nyaya_setu_ai.ai_stubs.generation import generate_answer as ai_generate_answer


def generate_answer(query: str, chunks: list[dict]) -> dict:
    """Create a cited, grounded answer from retrieved passages using the real AI package."""
    try:
        return ai_generate_answer(query, chunks)
    except Exception as e:
        # Fallback if the AI service is unavailable
        print(f"Error in AI generation: {e}")
        return {
            "your_right": "Unable to generate answer at this time.",
            "what_law_says": "",
            "what_this_means": "",
            "what_you_can_do": [],
            "source": {"act": "", "section": ""},
            "confidence": 0.0,
            "fallback_used": True
        }
