from backend.ai.speech import SpeechTranscriptionError, transcribe
from backend.ai.tts import SpeechSynthesisError, synthesize
from backend.ai.vision import extract_document


def test_stt_does_not_fake_success():
    try:
        transcribe(b"too-small")
        assert False, "expected failure"
    except SpeechTranscriptionError:
        pass


def test_tts_does_not_fake_success():
    try:
        synthesize("hello")
        assert False, "expected failure"
    except SpeechSynthesisError:
        pass


def test_vision_distinguishes_extraction_from_law():
    result = extract_document(b"%PDF-1.4 empty")
    assert result["authoritative"] is False
    assert result["origin"] == "user_document_extraction"
    assert "extracted_fields" in result
