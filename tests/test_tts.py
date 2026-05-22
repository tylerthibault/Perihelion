from __future__ import annotations

from pathlib import Path

from app import create_app
import tts


def make_app(tmp_path):
    db_path = tmp_path / "spacesim.sqlite3"
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(db_path),
            "SECRET_KEY": "test-key",
            "TTS_CACHE_DIR": str(tmp_path / "tts-cache"),
        }
    )
    return app


def register(client, username: str = "voicepilot"):
    return client.post("/api/auth/register", json={"username": username, "password": "secret12"})


def test_clean_tts_text_strips_control_suffixes():
    text = "Hello, captain.\n\nPending confirmation: Wait one day"

    assert tts.clean_tts_text(text) == "Hello, captain."


def test_kokoro_voice_selection_is_deterministic():
    npc = {"id": 42, "name": "Niko Rusk", "gender": "Female", "role": "Mechanic"}

    assert tts.kokoro_voice_for_npc(npc) == tts.kokoro_voice_for_npc(npc)
    assert tts.kokoro_voice_for_npc(npc) in tts.KOKORO_FEMALE_VOICES


def test_tts_speak_route_returns_cached_audio_url(tmp_path, monkeypatch):
    app = make_app(tmp_path)
    client = app.test_client()
    register(client)
    filename = f"{'a' * 64}.wav"

    def fake_synthesize(text, npc, cache_dir):
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        Path(cache_dir, filename).write_bytes(b"RIFF....WAVE")
        return {"provider": "kokoro", "voice": "af_heart", "speed": 1.0, "filename": filename, "text": text}

    monkeypatch.setattr(tts, "synthesize_tts", fake_synthesize)

    response = client.post(
        "/api/tts/speak",
        json={"text": "Hello there.", "npc": {"id": 1, "name": "Ada Voss", "gender": "Female", "role": "Broker"}},
    )
    body = response.get_json()
    audio = client.get(body["audioUrl"])

    assert response.status_code == 200
    assert body["provider"] == "kokoro"
    assert body["fallbackProvider"] == "browser"
    assert audio.status_code == 200
    assert audio.mimetype == "audio/wav"


def test_tts_speak_route_reports_browser_fallback_when_kokoro_unavailable(tmp_path, monkeypatch):
    app = make_app(tmp_path)
    client = app.test_client()
    register(client)

    def fake_synthesize(_text, _npc, _cache_dir):
        raise tts.TTSUnavailable("Missing Kokoro dependencies: kokoro")

    monkeypatch.setattr(tts, "synthesize_tts", fake_synthesize)

    response = client.post("/api/tts/speak", json={"text": "Hello there.", "npc": {"id": 1}})
    body = response.get_json()

    assert response.status_code == 503
    assert body["fallbackProvider"] == "browser"
    assert "kokoro" in body["message"].lower()
