"""Manually verify the configured Google Cloud TTS credentials and voice.

Run from the repository root with:
    PYTHONPATH=backend python backend/scripts/verify_tts.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.error import HTTPError

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.speech_service import synthesize_speech


OUTPUT_PATH = Path("/tmp/tts_check.mp3")
SAMPLE_TEXT = "This is a test of the interview voice."


def _format_error(exc: BaseException) -> str:
    """Expose provider response details when the adapter wraps an HTTP error."""
    cause = exc
    while cause.__cause__ is not None:
        cause = cause.__cause__
    if isinstance(cause, HTTPError):
        body = cause.read().decode("utf-8", errors="replace")
        try:
            return f"Google API HTTP {cause.code}: {json.dumps(json.loads(body), indent=2)}"
        except json.JSONDecodeError:
            return f"Google API HTTP {cause.code}: {body or cause.reason}"
    return f"{type(exc).__name__}: {exc}"


def main() -> int:
    """Call the real TTS provider and write the returned MP3."""
    try:
        result = synthesize_speech(SAMPLE_TEXT)
        audio = result["audio"]
        OUTPUT_PATH.write_bytes(audio)
    except Exception as exc:
        print(f"TTS verification failed: {_format_error(exc)}")
        return 1

    print(f"TTS verification succeeded: {OUTPUT_PATH} ({len(audio)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
