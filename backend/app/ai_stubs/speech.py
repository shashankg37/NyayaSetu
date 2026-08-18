from app.ai.ai_stubs.speech import transcribe as ai_transcribe


def transcribe(audio_bytes: bytes) -> str:
    """Transcribe Indian-language audio using the real AI package."""
    try:
        return ai_transcribe(audio_bytes)
    except Exception as e:
        # Fallback if the AI service is unavailable
        print(f"Error in AI transcription: {e}")
        return ""
