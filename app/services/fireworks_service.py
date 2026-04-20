"""
Fireworks AI — Whisper-v3 transcription service.

Fireworks hosts Whisper-v3 as managed inference — same API shape as OpenAI Whisper,
supports 99 languages including Twi, Haitian Creole, Tagalog, Yoruba, Ga (best-effort).
Pricing: ~$0.00009/sec audio (≈$0.003/min) — far cheaper than OpenAI Whisper.

HIPAA note: No BAA from Fireworks yet — demo/pilot use only.
For production with real PHI, switch to self-hosted Whisper on Fly.io/Modal.

Usage:
    from app.services.fireworks_service import fireworks_stt
    text, lang = await fireworks_stt.transcribe(audio_bytes, filename="audio.webm")
"""

from __future__ import annotations

import logging
import os
import tempfile
from typing import Optional, Tuple

import requests

LOGGER = logging.getLogger(__name__)

FIREWORKS_TRANSCRIBE_URL = "https://audio-prod.us-virginia-1.direct.fireworks.ai/inference/whisper-v3"
FIREWORKS_TRANSCRIBE_URL_V2 = "https://audio-prod.api.fireworks.ai/v1/audio/transcriptions"

# Seconds before giving up on the API call
REQUEST_TIMEOUT = 30


class FireworksSTT:
    """
    Wraps Fireworks Whisper-v3 transcription.
    Falls back gracefully if the API key is missing or the call fails.
    """

    def __init__(self) -> None:
        self.api_key: Optional[str] = os.getenv("FIREWORKS_API_KEY") or None
        self.model: str = os.getenv("FIREWORKS_STT_MODEL", "whisper-v3")
        self.enabled: bool = bool(self.api_key)

        if self.enabled:
            LOGGER.info("Fireworks STT enabled (model=%s)", self.model)
        else:
            LOGGER.info(
                "Fireworks STT disabled — set FIREWORKS_API_KEY to enable 99-language transcription"
            )

    def is_available(self) -> bool:
        return self.enabled

    def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "audio.webm",
        language: Optional[str] = None,
    ) -> Tuple[str, Optional[str]]:
        """
        Transcribe audio bytes using Fireworks Whisper-v3.

        Returns:
            (transcript_text, detected_language_code)
            On failure, returns ("", None) so caller can fall back to local Whisper.

        Args:
            audio_bytes: Raw audio bytes (webm, mp3, wav, m4a, ogg supported)
            filename:    Hint for MIME type detection (affects some decoders)
            language:    Optional BCP-47 hint (e.g. "tw", "tl", "es"). If None,
                         Whisper auto-detects — usually correct.
        """
        if not self.enabled:
            return "", None

        # Guess MIME type from extension
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "webm"
        mime_map = {
            "webm": "audio/webm",
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "m4a": "audio/mp4",
            "ogg": "audio/ogg",
            "flac": "audio/flac",
        }
        mime = mime_map.get(ext, "audio/webm")

        files = {"file": (filename, audio_bytes, mime)}
        data: dict = {
            "model": self.model,
            "response_format": "verbose_json",  # gives us language detection
        }
        if language:
            data["language"] = language

        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            response = requests.post(
                FIREWORKS_TRANSCRIBE_URL_V2,
                headers=headers,
                files=files,
                data=data,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            result = response.json()
            text = (result.get("text") or "").strip()
            detected_lang = result.get("language")  # ISO 639-1 code, e.g. "tw", "tl"
            LOGGER.debug(
                "Fireworks transcription complete: lang=%s, chars=%d",
                detected_lang,
                len(text),
            )
            return text, detected_lang

        except requests.exceptions.Timeout:
            LOGGER.warning("Fireworks STT timed out after %ds — falling back", REQUEST_TIMEOUT)
        except requests.exceptions.HTTPError as exc:
            LOGGER.warning("Fireworks STT HTTP error %s — falling back", exc.response.status_code)
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Fireworks STT error: %s — falling back", exc)

        return "", None


# Module-level singleton
fireworks_stt = FireworksSTT()
