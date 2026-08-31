import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api import voice
from app.services import audio_storage
from app.models.base import Base
from app.models.interview import InterviewSession
from app.services import interview_service
from app.services.voice_session_service import VoiceSessionState


class FakeWebSocket:
    def __init__(self):
        self.events = []

    async def send_json(self, payload):
        self.events.append(payload)


def _configure_transcription(monkeypatch):
    monkeypatch.setattr(voice, "decode_webm_opus_to_wav", lambda payload: b"RIFF/WAVE decoded")
    monkeypatch.setattr(
        voice,
        "stream_transcription",
        lambda wav: {"text": "Persist this answer.", "confidence": 0.9, "provider": "groq", "model": "whisper-large-v3-turbo"},
    )
    monkeypatch.setattr(voice, "submit_answer", lambda session_id, text, audio_path=None: {"next_question": ""})


def test_enabled_audio_persistence_writes_file_and_exposes_path(tmp_path, monkeypatch):
    _configure_transcription(monkeypatch)
    monkeypatch.setattr(voice, "ENABLE_AUDIO_PERSISTENCE", True)
    monkeypatch.setattr(audio_storage, "AUDIO_STORAGE_PATH", tmp_path)
    websocket = FakeWebSocket()
    state = VoiceSessionState(session_id=10)

    assert asyncio.run(voice._emit_transcription(websocket, state, b"encoded"))
    assert (tmp_path / "10" / "1.wav").read_bytes() == b"RIFF/WAVE decoded"
    final_event = next(event for event in websocket.events if event["type"] == "final_transcript")
    assert final_event["audio_path"] == "10/1.wav"
    assert state.transcript[0]["audio_path"] == "10/1.wav"


def test_disabled_audio_persistence_writes_nothing_and_leaves_path_unset(tmp_path, monkeypatch):
    _configure_transcription(monkeypatch)
    monkeypatch.setattr(voice, "ENABLE_AUDIO_PERSISTENCE", False)
    monkeypatch.setattr(audio_storage, "AUDIO_STORAGE_PATH", tmp_path)
    websocket = FakeWebSocket()
    state = VoiceSessionState(session_id=11)

    assert asyncio.run(voice._emit_transcription(websocket, state, b"encoded"))
    assert list(tmp_path.rglob("*.wav")) == []
    final_event = next(event for event in websocket.events if event["type"] == "final_transcript")
    assert "audio_path" not in final_event
    assert "audio_path" not in state.transcript[0]


def test_audio_path_is_retrievable_from_persisted_session_history(monkeypatch):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    test_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(interview_service, "SessionLocal", test_session)
    monkeypatch.setattr(interview_service, "run_question_generation", lambda name: "Question?")
    monkeypatch.setattr(interview_service, "run_evaluation", lambda question, answer: {
        "score": 8,
        "strengths": [],
        "weaknesses": [],
        "feedback": "Good.",
        "next_question": "Next?",
    })

    started = interview_service.start_interview("Candidate")
    interview_service.submit_answer(started["session_id"], "Answer text.", "10/1.wav")
    session = interview_service.get_interview_session(started["session_id"])

    assert session["history"][0]["audio_path"] == "10/1.wav"
