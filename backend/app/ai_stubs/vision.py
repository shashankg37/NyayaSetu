from nyaya_setu_ai.ai_stubs.vision import extract_document as ai_extract_document


def extract_document(file_bytes: bytes) -> dict:
    """Classify a legal document and extract meaningful fields using the real AI package."""
    try:
        return ai_extract_document(file_bytes)
    except Exception as e:
        # Fallback if the AI service is unavailable
        print(f"Error in AI document extraction: {e}")
        return {
            "doc_type": "unknown",
            "extracted_fields": {},
            "error": str(e)
        }
