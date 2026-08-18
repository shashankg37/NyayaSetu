from nyaya_setu_ai.ai_stubs.draft_fields import missing_fields as ai_missing_fields


def missing_fields(doc_type: str, known_fields: dict) -> list[str]:
    """Choose the most useful questions for a document draft using the real AI package."""
    try:
        return ai_missing_fields(doc_type, known_fields)
    except Exception as e:
        # Fallback if the AI service is unavailable
        print(f"Error in AI missing fields: {e}")
        return []

