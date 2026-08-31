"""WebSocket voice transport with text and HTTP-compatible fallbacks."""

import base64
import json
import logging
import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.speech_service import (
    analyze_transcript,
    decode_webm_opus_to_wav,
    stream_transcription,
    synthesize_speech,
)
from app.core.settings import ENABLE_AUDIO_PERSISTENCE
from app.services.audio_storage import save_audio
from app.services.interview_service import submit_answer, get_interview_session
from app.services.voice_session_service import get_voice_session

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Voice"])


async def _emit_agent_turn(websocket: WebSocket, session_id: int, text: str) -> None:
    """Send the next interviewer text turn and optional synchronized audio."""
    await websocket.send_json({"type": "agent_text", "session_id": session_id, "text": text})
    try:
        result = await asyncio.to_thread(synthesize_speech, text)
    except Exception as exc:
        logger.warning("voice_tts_failed", extra={"session_id": session_id, "error": str(exc)})
        return
    await websocket.send_json({
        "type": "agent_audio",
        "session_id": session_id,
        "text": text,
        "audio": base64.b64encode(result["audio"]).decode("ascii"),
        "content_type": result["content_type"],
        "provider": result["provider"],
        "voice": result["voice"],
    })


async def _emit_transcription(websocket: WebSocket, state, encoded_webm: bytes, *, emit_agent_turn: bool = False) -> bool:
    """Decode and transcribe one complete utterance without blocking the socket."""
    try:
        wav_bytes = await asyncio.to_thread(decode_webm_opus_to_wav, encoded_webm)
        result = await asyncio.to_thread(stream_transcription, wav_bytes)
        text = result["text"]
    except Exception as exc:  # provider and decoder libraries expose different failure types
        logger.warning("voice_transcription_failed", extra={"session_id": state.session_id, "error": str(exc)})
        await websocket.send_json({
            "type": "transcription_error",
            "code": "stt_unavailable",
            "message": "Live transcription is unavailable. You can continue in text mode.",
        })
        return False

    partial_event = {
        "type": "partial_transcript",
        "event": {"speaker": "candidate", "text": text, "partial": True},
        "confidence": result.get("confidence"),
        "provider": result.get("provider"),
        "model": result.get("model"),
    }
    await websocket.send_json(partial_event)
    final_event = state.add_transcript("candidate", text, partial=False)
    audio_path = None
    if ENABLE_AUDIO_PERSISTENCE:
        try:
            audio_path = await asyncio.to_thread(save_audio, state.session_id, len(state.transcript), wav_bytes)
            final_event["audio_path"] = audio_path
        except Exception as exc:
            logger.warning("voice_audio_persistence_failed", extra={"session_id": state.session_id, "error": str(exc)})
    final_payload = {
        "type": "final_transcript",
        "event": final_event,
        "confidence": result.get("confidence"),
        "provider": result.get("provider"),
        "model": result.get("model"),
        "analysis": analyze_transcript(text),
    }
    if audio_path:
        final_payload["audio_path"] = audio_path
    await websocket.send_json(final_payload)
    if emit_agent_turn:
        result = await asyncio.to_thread(submit_answer, state.session_id, text, audio_path)
        if isinstance(result, dict) and result.get("next_question"):
            await _emit_agent_turn(websocket, state.session_id, result["next_question"])
    return True


@router.websocket("/ws/interview/{session_id}")
async def interview_voice_socket(websocket: WebSocket, session_id: int):
    """Stream audio chunks, partial transcripts, quality metrics, and control events."""
    await websocket.accept()
    state = get_voice_session(session_id)
    await websocket.send_json({"type": "ready", "session_id": session_id, "transport": "websocket", "codec": "opus"})
    try:
        session = await asyncio.to_thread(get_interview_session, session_id)
        if session and session.get("suggested_next_question"):
            await _emit_agent_turn(websocket, session_id, session["suggested_next_question"])
    except Exception:
        logger.warning("voice_initial_question_failed", extra={"session_id": session_id}, exc_info=True)
    try:
        while True:
            message = await websocket.receive_json()
            event_type = message.get("type")
            if event_type == "ping":
                await websocket.send_json({"type": "pong"})
            elif event_type == "transcript":
                event = state.add_transcript("candidate", str(message.get("text", "")), partial=bool(message.get("partial")))
                analysis = analyze_transcript(event["text"], int(message.get("duration_ms", 0)))
                await websocket.send_json({"type": "transcript", "event": event, "analysis": analysis})
            elif event_type == "audio":
                try:
                    payload = base64.b64decode(message.get("data", ""), validate=True)
                except (ValueError, TypeError):
                    await websocket.send_json({"type": "error", "code": "invalid_audio", "message": "Audio payload was not valid base64."})
                    continue
                finalized = state.append_audio_chunk(
                    payload,
                    pause_threshold_seconds=float(message.get("pause_threshold_seconds", 0.9)),
                )
                state.metrics = {
                    "latency_ms": message.get("latency_ms", 0),
                    "buffer_bytes": len(state.audio_buffer),
                    "utterance_ready": finalized is not None,
                    "encoding": "webm/opus",
                }
                await websocket.send_json({"type": "audio_quality", "metrics": state.metrics})
                if finalized is not None:
                    await _emit_transcription(websocket, state, finalized, emit_agent_turn=True)
                    await websocket.send_json({
                        "type": "audio_utterance_ready",
                        "bytes": len(finalized),
                        "encoding": "webm/opus",
                        "message": "Accumulated audio is ready for decoding/transcription.",
                    })
            elif event_type == "end_utterance":
                finalized = state.flush_audio()
                if finalized is not None:
                    await _emit_transcription(websocket, state, finalized, emit_agent_turn=True)
            elif event_type == "state":
                await websocket.send_json({"type": "state", "session_id": session_id, "transcript": state.transcript, "metrics": state.metrics})
            else:
                await websocket.send_json({"type": "error", "code": "unsupported_event", "message": f"Unsupported voice event: {event_type}"})
    except WebSocketDisconnect:
        logger.info("voice_socket_disconnected", extra={"session_id": session_id})
