import base64

import pytest

from backend.ai import speech, tts
from backend.ai.speech import SpeechTranscriptionError, transcribe
from backend.ai.tts import SpeechSynthesisError, normalize_language_code, synthesize
from backend.ai.vision import extract_document


class _Response:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.text = str(payload)

    def json(self):
        return self._payload


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


@pytest.mark.parametrize(
    ("language", "transcript"),
    [
        ("en-IN", "My employer has not paid wages."),
        ("hi-IN", "मेरे नियोक्ता ने मजदूरी नहीं दी।"),
        ("kn-IN", "ನನ್ನ ಉದ್ಯೋಗದಾತರು ವೇತನ ನೀಡಿಲ್ಲ."),
    ],
)
def test_sarvam_stt_uses_saaras_v3_for_indian_languages(monkeypatch, language, transcript):
    calls = {}
    monkeypatch.setattr(speech.SETTINGS, "sarvam_api_key", "test-key", raising=False)
    monkeypatch.setattr(speech.SETTINGS, "sarvam_base_url", "https://api.sarvam.ai", raising=False)
    monkeypatch.setattr(speech.SETTINGS, "sarvam_stt_model", "saaras:v3", raising=False)
    monkeypatch.setattr(speech.SETTINGS, "sarvam_timeout_seconds", 60, raising=False)

    def fake_post(url, headers=None, files=None, data=None, timeout=None):
        calls.update({"url": url, "headers": headers, "files": files, "data": data, "timeout": timeout})
        return _Response({"transcript": transcript, "language_code": language})

    monkeypatch.setattr(speech.requests, "post", fake_post)

    assert transcribe(b"RIFF" + b"0" * 120, source_language=language) == transcript
    assert calls["url"] == "https://api.sarvam.ai/speech-to-text"
    assert calls["headers"] == {"api-subscription-key": "test-key"}
    assert calls["data"]["model"] == "saaras:v3"
    assert calls["data"]["mode"] == "transcribe"
    assert calls["data"]["language_code"] == language
    assert "file" in calls["files"]


def test_sarvam_stt_empty_and_unconfigured_fail(monkeypatch):
    with pytest.raises(SpeechTranscriptionError, match="empty"):
        transcribe(b"")
    monkeypatch.setattr(speech.SETTINGS, "sarvam_api_key", "", raising=False)
    with pytest.raises(SpeechTranscriptionError, match="Sarvam STT is not configured"):
        transcribe(b"RIFF" + b"0" * 120)


@pytest.mark.parametrize(
    ("language", "expected"),
    [
        ("en", "en-IN"),
        ("hi", "hi-IN"),
        ("kn", "kn-IN"),
        ("hi-IN", "hi-IN"),
    ],
)
def test_sarvam_tts_language_normalization(monkeypatch, language, expected):
    monkeypatch.setattr(tts.SETTINGS, "sarvam_default_language", "en-IN", raising=False)
    assert normalize_language_code(language) == expected


def test_sarvam_tts_uses_bulbul_v3(monkeypatch):
    audio = b"RIFFWAVE"
    calls = {}
    monkeypatch.setattr(tts.SETTINGS, "sarvam_api_key", "test-key", raising=False)
    monkeypatch.setattr(tts.SETTINGS, "sarvam_base_url", "https://api.sarvam.ai", raising=False)
    monkeypatch.setattr(tts.SETTINGS, "sarvam_tts_model", "bulbul:v3", raising=False)
    monkeypatch.setattr(tts.SETTINGS, "sarvam_tts_speaker", "shubh", raising=False)
    monkeypatch.setattr(tts.SETTINGS, "sarvam_default_language", "en-IN", raising=False)
    monkeypatch.setattr(tts.SETTINGS, "sarvam_timeout_seconds", 60, raising=False)

    def fake_post(url, headers=None, json=None, timeout=None):
        calls.update({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return _Response({"audios": [base64.b64encode(audio).decode("ascii")]})

    monkeypatch.setattr(tts.requests, "post", fake_post)

    assert synthesize("You can file a wage complaint.", target_language="hi") == audio
    assert calls["url"] == "https://api.sarvam.ai/text-to-speech"
    assert calls["headers"]["api-subscription-key"] == "test-key"
    assert calls["json"]["model"] == "bulbul:v3"
    assert calls["json"]["speaker"] == "shubh"
    assert calls["json"]["language_code"] == "hi-IN"


def test_sarvam_tts_invalid_and_unconfigured_fail(monkeypatch):
    with pytest.raises(SpeechSynthesisError, match="No text"):
        synthesize("")
    monkeypatch.setattr(tts.SETTINGS, "sarvam_api_key", "", raising=False)
    with pytest.raises(SpeechSynthesisError, match="Sarvam TTS is not configured"):
        synthesize("hello")


def test_qwen_document_understanding_shapes_retrieval_query(monkeypatch):
    def fake_qwen(prompt, image_bytes, mime_type):
        assert "Do not answer the legal question" in prompt
        assert mime_type == "image/png"
        return {
            "document_type": "legal_notice",
            "parties": ["Worker", "Employer"],
            "dates": ["2026-01-12"],
            "authorities": ["Labour Department"],
            "sections_mentioned": ["Code on Wages section 17"],
            "deadlines": ["15 days"],
            "clauses": ["unpaid wages"],
            "important_facts": "Worker claims unpaid wages from employer.",
            "retrieval_query": "unpaid wages legal notice Code on Wages section 17",
        }

    monkeypatch.setattr("backend.ai.vision.generate_json_from_image", fake_qwen)
    result = extract_document(b"\x89PNG\r\n\x1a\n" + b"0" * 128)

    assert result["authoritative"] is False
    assert result["doc_type"] == "legal_notice"
    assert result["fallback_used"] is False
    assert result["vision_error"] is None
    assert "Code on Wages" in result["retrieval_query"]


def test_irrelevant_or_unreadable_image_uses_safe_fallback(monkeypatch):
    monkeypatch.setattr("backend.ai.vision.generate_json_from_image", lambda *args, **kwargs: None)
    result = extract_document(b"\x89PNG\r\n\x1a\n" + b"0" * 128)

    assert result["authoritative"] is False
    assert result["fallback_used"] is True
    assert result["doc_type"] == "unknown_document"
    assert "Qwen multimodal provider unavailable" in result["vision_error"]
