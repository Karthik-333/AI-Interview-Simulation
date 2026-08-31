import asyncio
import base64
import json
import wave

from app.api import voice
from app.services import speech_service
from app.services.voice_session_service import VoiceSessionState


class FakeWebSocket:
    def __init__(self):
        self.events = []

    async def send_json(self, payload):
        self.events.append(payload)


def test_gemini_tts_adapter_wraps_pcm_as_wav(monkeypatch):
    pcm = b"\x01\x00\x02\x00"

    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return None
        def read(self):
            encoded = base64.b64encode(pcm).decode("ascii")
            return json.dumps({
                "candidates": [{
                    "content": {
                        "parts": [{"inlineData": {"data": encoded}}]
                    }
                }]
            }).encode()

    calls = {}
    monkeypatch.setattr(speech_service, "urlopen", lambda request, timeout: (calls.update({"request": request, "timeout": timeout}) or Response()))
    monkeypatch.setattr(speech_service, "TTS_API_KEY", "test-key")
    monkeypatch.setattr(speech_service, "TTS_PROVIDER", "gemini")
    monkeypatch.setattr(speech_service, "TTS_MODEL", "gemini-2.5-flash-preview-tts")
    monkeypatch.setattr(speech_service, "TTS_VOICE", "Kore")
    result = speech_service.synthesize_speech("What did you build?")

    with wave.open(__import__("io").BytesIO(result["audio"]), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == 24_000
        assert wav_file.readframes(2) == pcm
    body = json.loads(calls["request"].data)
    assert calls["request"].headers["X-goog-api-key"] == "test-key"
    assert body["generationConfig"]["responseModalities"] == ["AUDIO"]
    assert body["generationConfig"]["speechConfig"]["voiceConfig"]["prebuiltVoiceConfig"]["voiceName"] == "Kore"


def test_agent_audio_event_is_emitted_for_new_turn(monkeypatch):
    websocket = FakeWebSocket()
    monkeypatch.setattr(voice, "synthesize_speech", lambda text: {"audio": b"mp3", "content_type": "audio/mpeg", "provider": "google", "voice": "en-US-Neural2-F"})

    asyncio.run(voice._emit_agent_turn(websocket, 7, "Tell me about your API design."))

    assert websocket.events[0] == {"type": "agent_text", "session_id": 7, "text": "Tell me about your API design."}
    assert websocket.events[1]["type"] == "agent_audio"
    assert base64.b64decode(websocket.events[1]["audio"]) == b"mp3"
    assert websocket.events[1]["text"] == websocket.events[0]["text"]


def test_tts_failure_keeps_text_turn(monkeypatch):
    websocket = FakeWebSocket()
    monkeypatch.setattr(voice, "synthesize_speech", lambda text: (_ for _ in ()).throw(TimeoutError("timeout")))

    asyncio.run(voice._emit_agent_turn(websocket, 8, "Follow-up question"))

    assert [event["type"] for event in websocket.events] == ["agent_text"]
