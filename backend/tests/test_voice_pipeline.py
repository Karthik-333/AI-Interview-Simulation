import struct
from pathlib import Path

from app.services.speech_service import analyze_audio, analyze_transcript, decode_webm_opus_to_wav, normalize_transcript
from app.services.voice_session_service import VoiceSessionState


def test_audio_quality_and_transcript_analysis():
    payload = b"".join(struct.pack("<h", 1000) for _ in range(16_000))
    quality = analyze_audio(payload)
    assert quality.duration_ms == 1000
    assert quality.rms > 0
    analysis = analyze_transcript("Um I designed an API...", duration_ms=60_000)
    assert analysis["filler_words"] == 1
    assert analysis["pause_count"] == 1
    assert normalize_transcript("  hello   world ") == "hello world."


def test_webm_chunks_buffer_in_order_and_decode_as_one_stream():
    fixture = Path(__file__).with_name("fixtures") / "voice_sample.webm"
    encoded = fixture.read_bytes()
    chunks = [encoded[index:index + 1800] for index in range(0, len(encoded), 1800)]
    state = VoiceSessionState(session_id=1)

    for index, chunk in enumerate(chunks):
        assert state.append_audio_chunk(chunk, now=index * 0.5, pause_threshold_seconds=0.9) is None

    accumulated = state.flush_audio()
    assert accumulated == encoded
    decoded = decode_webm_opus_to_wav(accumulated)
    assert decoded.startswith(b"RIFF")
    assert b"WAVE" in decoded[:16]


def test_audio_lull_finalizes_previous_utterance_before_new_chunk():
    encoded = (Path(__file__).with_name("fixtures") / "voice_sample.webm").read_bytes()
    chunks = [encoded[index:index + 1800] for index in range(0, len(encoded), 1800)]
    state = VoiceSessionState(session_id=2)
    state.append_audio_chunk(chunks[0], now=0.0)
    state.append_audio_chunk(chunks[1], now=0.5)
    finalized = state.append_audio_chunk(chunks[2], now=2.0, pause_threshold_seconds=0.9)

    assert finalized == chunks[0] + chunks[1]
    assert decode_webm_opus_to_wav(finalized).startswith(b"RIFF")
