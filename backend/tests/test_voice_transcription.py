import asyncio
from pathlib import Path

from app.api import voice
from app.services import speech_service
from app.services.voice_session_service import VoiceSessionState


class FakeWebSocket:
    def __init__(self):
        self.events = []

    async def send_json(self, payload):
        self.events.append(payload)


def test_transcription_emits_partial_and_final_events(monkeypatch):
    encoded = (Path(__file__).with_name("fixtures") / "voice_sample.webm").read_bytes()
    websocket = FakeWebSocket()
    state = VoiceSessionState(session_id=42)
    added = []

    monkeypatch.setattr(voice, "decode_webm_opus_to_wav", lambda payload: b"decoded-wav")
    monkeypatch.setattr(
        voice,
        "stream_transcription",
        lambda wav: {"text": "I built an API.", "confidence": 0.97, "provider": "groq", "model": "whisper-large-v3-turbo"},
    )
    original_add = state.add_transcript

    def record_add(speaker, text, *, partial=False):
        added.append((speaker, text, partial))
        return original_add(speaker, text, partial=partial)

    monkeypatch.setattr(state, "add_transcript", record_add)
    assert asyncio.run(voice._emit_transcription(websocket, state, encoded))

    assert [event["type"] for event in websocket.events] == ["partial_transcript", "final_transcript"]
    assert websocket.events[0]["event"] == {"speaker": "candidate", "text": "I built an API.", "partial": True}
    assert websocket.events[1]["event"]["partial"] is False
    assert added == [("candidate", "I built an API.", False)]


def test_groq_openai_compatible_client_adapter(monkeypatch):
    calls = {}

    class FakeResponse:
        text = "decoded answer"
        confidence = 0.91

    class FakeTranscriptions:
        def create(self, **kwargs):
            calls.update(kwargs)
            return FakeResponse()

    class FakeAudio:
        transcriptions = FakeTranscriptions()

    class FakeOpenAI:
        def __init__(self, **kwargs):
            calls["client"] = kwargs
        audio = FakeAudio()

    monkeypatch.setattr(speech_service, "OpenAI", FakeOpenAI)
    monkeypatch.setattr(speech_service, "STT_API_KEY", "test-key")
    monkeypatch.setattr(speech_service, "STT_PROVIDER", "groq")
    result = speech_service.stream_transcription(b"RIFF audio")

    assert result["text"] == "decoded answer."
    assert result["provider"] == "groq"
    assert calls["client"]["base_url"] == "https://api.groq.com/openai/v1"
    assert calls["model"] == "whisper-large-v3-turbo"


def test_transcription_failure_emits_recovery_event(monkeypatch):
    websocket = FakeWebSocket()
    state = VoiceSessionState(session_id=43)
    monkeypatch.setattr(voice, "decode_webm_opus_to_wav", lambda payload: b"decoded-wav")

    def fail(_wav):
        raise TimeoutError("provider timeout")

    monkeypatch.setattr(voice, "stream_transcription", fail)
    assert not asyncio.run(voice._emit_transcription(websocket, state, b"encoded"))
    assert websocket.events[0]["type"] == "transcription_error"
    assert state.transcript == []
