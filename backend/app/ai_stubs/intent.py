from nyaya_setu_ai.ai_stubs.intent import classify_intent as ai_classify_intent


def classify_intent(text: str) -> str:
    """Classify a user's legal-help intent using the real AI package."""
    try:
        return ai_classify_intent(text)
    except Exception as e:
        # Fallback if the AI service is unavailable
        print(f"Error in AI intent classification: {e}")
        return "unknown"
