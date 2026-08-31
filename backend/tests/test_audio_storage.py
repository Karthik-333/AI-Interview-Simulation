from pathlib import Path

from app.services import audio_storage


def test_save_audio_uses_session_and_turn_layout(tmp_path, monkeypatch):
    monkeypatch.setattr(audio_storage, "AUDIO_STORAGE_PATH", tmp_path)
    assert audio_storage.save_audio(12, 3, b"RIFF wav") == "12/3.wav"
    assert (tmp_path / "12" / "3.wav").read_bytes() == b"RIFF wav"


def test_save_audio_rejects_invalid_identifiers(tmp_path, monkeypatch):
    monkeypatch.setattr(audio_storage, "AUDIO_STORAGE_PATH", tmp_path)
    try:
        audio_storage.save_audio(-1, 0, b"wav")
    except ValueError:
        pass
    else:
        raise AssertionError("negative session IDs must be rejected")
