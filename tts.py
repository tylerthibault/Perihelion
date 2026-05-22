from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import threading
from pathlib import Path
from typing import Any


KOKORO_SAMPLE_RATE = 24000
KOKORO_FEMALE_VOICES = [
    "af_heart",
    "af_bella",
    "af_nicole",
    "af_sarah",
    "af_sky",
    "af_nova",
    "af_river",
    "af_jessica",
    "af_aoede",
    "af_kore",
]
KOKORO_MALE_VOICES = [
    "am_adam",
    "am_echo",
    "am_eric",
    "am_fenrir",
    "am_liam",
    "am_michael",
    "am_onyx",
    "am_puck",
]
KOKORO_LANG_CODE = "a"
TTS_CACHE_VERSION = 1
TTS_MAX_CHARS = 1400

_kokoro_pipeline = None
_kokoro_lock = threading.Lock()


class TTSUnavailable(RuntimeError):
    pass


def tts_status(cache_dir: str | Path) -> dict[str, Any]:
    missing = missing_kokoro_dependencies()
    available = not missing
    message = (
        "Kokoro neural voice is ready."
        if available
        else f"Kokoro unavailable; browser voice fallback will be used. Missing: {', '.join(missing)}."
    )
    return {
        "preferredProvider": "kokoro",
        "fallbackProvider": "browser",
        "available": available,
        "message": message,
        "cacheDir": str(cache_dir),
    }


def missing_kokoro_dependencies() -> list[str]:
    missing = []
    for package in ("kokoro", "soundfile", "numpy"):
        if importlib.util.find_spec(package) is None:
            missing.append(package)
    return missing


def synthesize_tts(text: str, npc: dict[str, Any], cache_dir: str | Path) -> dict[str, Any]:
    clean_text = clean_tts_text(text)
    if not clean_text:
        raise ValueError("No speakable text was provided.")

    missing = missing_kokoro_dependencies()
    if missing:
        raise TTSUnavailable(f"Kokoro dependencies not installed: {', '.join(missing)}")

    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    voice = kokoro_voice_for_npc(npc)
    speed = kokoro_speed_for_npc(npc)
    cache_key = tts_cache_key(clean_text, voice, speed)
    audio_path = cache_path / f"{cache_key}.wav"

    if not audio_path.exists():
        synthesize_kokoro_audio(clean_text, voice, speed, audio_path)

    return {
        "provider": "kokoro",
        "voice": voice,
        "speed": speed,
        "filename": audio_path.name,
        "text": clean_text,
    }


def synthesize_kokoro_audio(text: str, voice: str, speed: float, audio_path: Path) -> None:
    import numpy as np
    import soundfile as sf

    pipeline = get_kokoro_pipeline()
    chunks = []
    for _, _, audio in pipeline(text, voice=voice, speed=speed, split_pattern=r"\n+"):
        if hasattr(audio, "detach"):
            audio = audio.detach().cpu().numpy()
        chunks.append(audio)

    if not chunks:
        raise TTSUnavailable("Kokoro returned no audio.")

    audio_data = chunks[0] if len(chunks) == 1 else np.concatenate(chunks)
    sf.write(audio_path, audio_data, KOKORO_SAMPLE_RATE)


def get_kokoro_pipeline():
    global _kokoro_pipeline
    if _kokoro_pipeline is not None:
        return _kokoro_pipeline
    with _kokoro_lock:
        if _kokoro_pipeline is None:
            from kokoro import KPipeline

            _kokoro_pipeline = KPipeline(lang_code=KOKORO_LANG_CODE)
    return _kokoro_pipeline


def kokoro_voice_for_npc(npc: dict[str, Any]) -> str:
    gender = str(npc.get("gender") or "").lower()
    voices = KOKORO_MALE_VOICES if gender == "male" else KOKORO_FEMALE_VOICES
    digest = stable_digest(
        {
            "id": npc.get("id"),
            "name": npc.get("name"),
            "gender": npc.get("gender"),
            "role": npc.get("role"),
        }
    )
    return voices[int(digest[:8], 16) % len(voices)]


def kokoro_speed_for_npc(npc: dict[str, Any]) -> float:
    digest = stable_digest({"id": npc.get("id"), "name": npc.get("name"), "role": npc.get("role")})
    offset = (int(digest[8:10], 16) % 9 - 4) * 0.025
    return round(max(0.86, min(1.08, 0.98 + offset)), 2)


def tts_cache_key(text: str, voice: str, speed: float) -> str:
    return stable_digest(
        {
            "version": TTS_CACHE_VERSION,
            "provider": "kokoro",
            "voice": voice,
            "speed": speed,
            "text": text,
        }
    )


def stable_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def clean_tts_text(text: str) -> str:
    clean = str(text or "")
    clean = re.sub(r"Pending confirmation:.*$", "", clean, flags=re.IGNORECASE | re.DOTALL)
    clean = re.sub(r"Ship action (ignored|applied):.*$", "", clean, flags=re.IGNORECASE | re.DOTALL)
    clean = re.sub(r"Action rejected:.*$", "", clean, flags=re.IGNORECASE | re.DOTALL)
    clean = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", clean)
    clean = clean.replace("`", "")
    clean = re.sub(r"[*_#>]+", "", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:TTS_MAX_CHARS]


def valid_audio_filename(filename: str) -> bool:
    return bool(re.fullmatch(r"[a-f0-9]{64}\.wav", filename or ""))
