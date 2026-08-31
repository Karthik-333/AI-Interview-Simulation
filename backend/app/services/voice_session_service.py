"""Connection-local voice interview state with recovery-friendly snapshots."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from app.services.speech_service import has_audio_pause


@dataclass
class VoiceSessionState:
    """State exchanged by a WebSocket voice session."""

    session_id: int
    connected_at: float = field(default_factory=time.monotonic)
    last_seen: float = field(default_factory=time.monotonic)
    transcript: list[dict] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    audio_buffer: bytearray = field(default_factory=bytearray)
    last_audio_chunk_at: float | None = None

    def add_transcript(self, speaker: str, text: str, *, partial: bool = False) -> dict:
        self.last_seen = time.monotonic()
        event = {"speaker": speaker, "text": text, "partial": partial, "timestamp": time.time()}
        if partial and self.transcript and self.transcript[-1].get("partial"):
            self.transcript[-1] = event
        else:
            self.transcript.append(event)
        return event

    def append_audio_chunk(self, payload: bytes, *, now: float | None = None, pause_threshold_seconds: float = 0.9) -> bytes | None:
        """Append an encoded WebM/Opus chunk and finalize after an input lull.

        The returned bytes are the previous utterance's complete WebM stream,
        ready for one decode/transcription operation. The current chunk always
        starts the next utterance after a pause.
        """
        timestamp = time.monotonic() if now is None else now
        finalized = None
        if has_audio_pause(self.last_audio_chunk_at, timestamp, pause_threshold_seconds):
            finalized = bytes(self.audio_buffer) if self.audio_buffer else None
            self.audio_buffer.clear()
        self.audio_buffer.extend(payload)
        self.last_audio_chunk_at = timestamp
        return finalized

    def flush_audio(self) -> bytes | None:
        """Return and clear the current accumulated WebM/Opus utterance."""
        if not self.audio_buffer:
            return None
        finalized = bytes(self.audio_buffer)
        self.audio_buffer.clear()
        self.last_audio_chunk_at = None
        return finalized


_sessions: dict[int, VoiceSessionState] = {}


def get_voice_session(session_id: int) -> VoiceSessionState:
    """Get or recover a session snapshot after a dropped connection."""
    state = _sessions.setdefault(session_id, VoiceSessionState(session_id=session_id))
    state.last_seen = time.monotonic()
    return state
