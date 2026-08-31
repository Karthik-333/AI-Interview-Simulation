"""Local persistence adapter for finalized interview audio."""

from pathlib import Path

from app.core.settings import AUDIO_STORAGE_PATH


def save_audio(session_id: int, turn_index: int, audio_bytes: bytes) -> str:
    """Write one WAV utterance and return its storage-relative path.

    Session and turn identifiers are integers supplied by the application,
    rather than user-controlled path fragments, which prevents traversal.
    """
    if session_id < 0 or turn_index < 0:
        raise ValueError("Audio identifiers must be non-negative.")
    if not audio_bytes:
        raise ValueError("Cannot persist empty audio.")
    relative_path = Path(str(session_id)) / f"{turn_index}.wav"
    root = Path(AUDIO_STORAGE_PATH).resolve()
    destination = (root / relative_path).resolve()
    if root != destination and root not in destination.parents:
        raise ValueError("Invalid audio storage path.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(audio_bytes)
    return relative_path.as_posix()
