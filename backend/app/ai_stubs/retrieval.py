from app.ai.ai_stubs.retrieval import retrieve as ai_retrieve


def retrieve(query: str) -> list[dict]:
    """Retrieve authoritative legal passages using the real AI package's retrieval system."""
    try:
        return ai_retrieve(query)
    except Exception as e:
        # Fallback if the AI service is unavailable
        print(f"Error in AI retrieval: {e}")
        return []
