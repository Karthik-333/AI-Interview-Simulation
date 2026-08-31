"""Optional speech services and deterministic audio-response analysis.

The platform accepts provider adapters (Whisper, Deepgram, or a self-hosted
service) without making the interview dependent on an external vendor.
"""

from __future__ import annotations

import math
import re
import struct
import subprocess
import wave
from io import BytesIO
from dataclasses import dataclass
import base64
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.settings import (
    STT_API_KEY,
    STT_MODEL,
    STT_PROVIDER,
    STT_TIMEOUT_SECONDS,
    TTS_API_KEY,
    TTS_MODEL,
    TTS_PROVIDER,
    TTS_TIMEOUT_SECONDS,
    TTS_VOICE,
)

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional until STT is configured
    OpenAI = None


@dataclass(frozen=True)
class AudioAnalysis:
    """Quality and communication measurements for one audio segment."""

    duration_ms: int
    rms: float
    snr_db: float
    speech_rate_wpm: float
    pause_count: int
    filler_words: int
    confidence: float


def analyze_audio(payload: bytes, sample_rate: int = 16_000, channels: int = 1, sample_width: int = 2) -> AudioAnalysis:
    """Estimate audio quality from PCM data without requiring native DSP libs."""
    if not payload:
        return AudioAnalysis(0, 0.0, 0.0, 0.0, 0, 0, 0.0)
    if sample_width != 2:
        raise ValueError("Only 16-bit PCM audio is supported.")
    samples_data = struct.unpack(f"<{len(payload) // sample_width}h", payload[: len(payload) - (len(payload) % sample_width)])
    rms = math.sqrt(sum(sample * sample for sample in samples_data) / max(len(samples_data), 1))
    samples = max(len(payload) // max(sample_width * channels, 1), 1)
    duration_ms = round(samples / sample_rate * 1000)
    snr_db = round(20 * math.log10(max(rms, 1) / 500), 2)
    return AudioAnalysis(duration_ms, round(rms, 2), snr_db, 0.0, 0, 0, min(max(rms / 4000, 0.0), 1.0))


def decode_webm_opus_to_wav(payload: bytes, *, ffmpeg_binary: str = "ffmpeg") -> bytes:
    """Decode an accumulated WebM/Opus stream to PCM/WAV bytes via ffmpeg.

    WebM chunks must be concatenated before calling this function because the
    container header is only guaranteed to be present in the first chunk.
    """
    if not payload:
        raise ValueError("Cannot decode an empty WebM buffer.")
    process = subprocess.run(
        [
            ffmpeg_binary,
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "webm",
            "-i",
            "pipe:0",
            "-f",
            "wav",
            "-acodec",
            "pcm_s16le",
            "pipe:1",
        ],
        input=payload,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if process.returncode != 0:
        detail = process.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"Unable to decode WebM/Opus audio: {detail}")
    return process.stdout


def stream_transcription(wav_bytes: bytes) -> dict:
    """Transcribe decoded WAV bytes through the configured OpenAI-compatible API.

    ``groq`` is the default provider and uses Groq's OpenAI-compatible base URL.
    The adapter returns a stable shape so an ``openai`` branch can be added
    without changing WebSocket or session code.
    """
    if not wav_bytes:
        raise ValueError("Cannot transcribe empty audio.")
    if not STT_API_KEY:
        raise RuntimeError("STT_API_KEY is not configured.")
    if OpenAI is None:
        raise RuntimeError("The optional openai package is not installed.")
    if STT_PROVIDER == "groq":
        base_url = "https://api.groq.com/openai/v1"
    elif STT_PROVIDER == "openai":
        base_url = None
    else:
        raise ValueError(f"Unsupported STT provider: {STT_PROVIDER}")

    client_kwargs = {"api_key": STT_API_KEY, "timeout": STT_TIMEOUT_SECONDS}
    if base_url:
        client_kwargs["base_url"] = base_url
    client = OpenAI(**client_kwargs)
    response = client.audio.transcriptions.create(
        model=STT_MODEL,
        file=("utterance.wav", BytesIO(wav_bytes), "audio/wav"),
        response_format="verbose_json",
    )
    text = normalize_transcript(str(getattr(response, "text", "") or ""))
    return {
        "text": text,
        "confidence": getattr(response, "confidence", None),
        "provider": STT_PROVIDER,
        "model": STT_MODEL,
    }


def synthesize_speech(text: str) -> dict:
    """Synthesize speech with Gemini's native audio generation API.

    Gemini returns raw 16-bit PCM audio. This adapter wraps it in a mono WAV
    container so existing browser playback receives a playable audio file.
    """
    text = (text or "").strip()
    if not text:
        raise ValueError("Cannot synthesize empty text.")
    if not TTS_API_KEY:
        raise RuntimeError("TTS_API_KEY is not configured.")
    if TTS_PROVIDER != "gemini":
        raise ValueError(f"Unsupported TTS provider: {TTS_PROVIDER}")

    request = Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{TTS_MODEL}:generateContent",
        data=json.dumps(
            {
                "contents": [{"parts": [{"text": text}]}],
                "generationConfig": {
                    "responseModalities": ["AUDIO"],
                    "speechConfig": {
                        "voiceConfig": {
                            "prebuiltVoiceConfig": {"voiceName": TTS_VOICE}
                        }
                    },
                },
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": TTS_API_KEY},
        method="POST",
    )
    try:
        with urlopen(request, timeout=TTS_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError("Gemini TTS request failed.") from exc
    try:
        encoded_audio = payload["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
        pcm_audio = base64.b64decode(encoded_audio, validate=True)
    except (KeyError, ValueError, TypeError) as exc:
        raise RuntimeError("Gemini TTS returned an invalid audio payload.") from exc

    wav_buffer = BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(24_000)
        wav_file.writeframes(pcm_audio)
    return {
        "audio": wav_buffer.getvalue(),
        "content_type": "audio/wav",
        "provider": TTS_PROVIDER,
        "model": TTS_MODEL,
        "voice": TTS_VOICE,
    }


def has_audio_pause(last_chunk_at: float | None, now: float, pause_threshold_seconds: float) -> bool:
    """Return whether the gap since the previous chunk marks an utterance pause."""
    return last_chunk_at is not None and now - last_chunk_at >= pause_threshold_seconds


def normalize_transcript(text: str) -> str:
    """Normalize whitespace and restore conservative sentence punctuation."""
    normalized = re.sub(r"\s+", " ", (text or "").strip())
    if normalized and normalized[-1] not in ".!?":
        normalized += "."
    return normalized


def analyze_transcript(text: str, duration_ms: int = 0) -> dict:
    """Return language-agnostic communication signals from a transcript."""
    words = re.findall(r"[A-Za-z']+", text or "")
    fillers = sum(1 for word in words if word.lower() in {"um", "uh", "like", "actually", "basically"})
    pauses = max(0, len(re.findall(r"\.{2,}|…", text or "")))
    minutes = duration_ms / 60_000 if duration_ms else 0
    return {
        "word_count": len(words),
        "filler_words": fillers,
        "pause_count": pauses,
        "speech_rate_wpm": round(len(words) / minutes, 2) if minutes else 0.0,
        "normalized_text": normalize_transcript(text),
    }
