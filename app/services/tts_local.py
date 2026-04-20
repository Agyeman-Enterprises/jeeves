from __future__ import annotations

import logging
import os
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Optional

import requests

try:
    import torch  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    torch = None

try:
    from TTS.api import TTS  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    TTS = None

LOGGER = logging.getLogger(__name__)

DEFAULT_PIPER_MODEL_URL = os.getenv(
    "PIPER_MODEL_URL",
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US-amy-low.onnx?download=1",
)
DEFAULT_PIPER_CONFIG_URL = os.getenv(
    "PIPER_CONFIG_URL",
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US-amy-low.onnx.json?download=1",
)
PIPER_DIR = Path(os.getenv("PIPER_MODEL_DIR", "data/piper"))
TTS_OUTPUT_DIR = Path(os.getenv("TTS_OUTPUT_DIR", "data/tts_output"))
XTTS_MODEL_NAME = os.getenv(
    "XTTS_MODEL_NAME", "tts_models/multilingual/multi-dataset/xtts_v2"
)


class LocalTTS:
    """
    Local text-to-speech provider that defaults to Piper for short responses
    and falls back to XTTSv2 for longer passages.

    The synthesize method returns the path to a generated WAV file.
    """

    def __init__(self) -> None:
        self.model_dir = PIPER_DIR
        self.output_dir = TTS_OUTPUT_DIR
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.piper_model_path = self._ensure_file(DEFAULT_PIPER_MODEL_URL, "en_US-amy-low.onnx")
        self.piper_config_path = self._ensure_file(
            DEFAULT_PIPER_CONFIG_URL, "en_US-amy-low.onnx.json"
        )
        self.piper_binary = shutil.which(os.getenv("PIPER_BINARY", "piper"))

        if not self.piper_binary:
            LOGGER.warning("Piper binary not found on PATH. Install piper-tts for local speech.")

        self.xtts_model_name = XTTS_MODEL_NAME
        self._xtts_instance: Optional[TTS] = None
        self._xtts_failed = False

    # --------------------------------------------------------------------- #
    def synthesize(self, text: str) -> Optional[Path]:
        """Generate speech audio for the provided text and return a WAV path."""
        cleaned = (text or "").strip()
        if not cleaned:
            LOGGER.warning("LocalTTS: Received empty text payload.")
            return None

        if len(cleaned) <= 280 and self._can_use_piper():
            audio_path = self._synthesize_with_piper(cleaned)
            if audio_path:
                return audio_path

        return self._synthesize_with_xtts(cleaned)

    # --------------------------------------------------------------------- #
    def _can_use_piper(self) -> bool:
        return bool(self.piper_binary and self.piper_model_path and self.piper_model_path.exists())

    def _synthesize_with_piper(self, text: str) -> Optional[Path]:
        if not self._can_use_piper():
            return None

        output_path = self.output_dir / f"jarvis-piper-{uuid.uuid4().hex}.wav"
        cmd = [
            self.piper_binary,
            "--model",
            str(self.piper_model_path),
            "--output_file",
            str(output_path),
        ]
        if self.piper_config_path and self.piper_config_path.exists():
            cmd.extend(["--config", str(self.piper_config_path)])

        try:
            subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                check=True,
            )
            return output_path
        except Exception as exc:  # pragma: no cover - subprocess heavy
            LOGGER.exception("Piper synthesis failed: %s", exc)
            if output_path.exists():
                output_path.unlink(missing_ok=True)  # type: ignore[arg-type]
            return None

    def _synthesize_with_xtts(self, text: str) -> Optional[Path]:
        tts = self._load_xtts()
        if not tts:
            LOGGER.error("LocalTTS: XTTS model unavailable.")
            return None

        output_path = self.output_dir / f"jarvis-xtts-{uuid.uuid4().hex}.wav"
        try:
            tts.tts_to_file(text=text, file_path=str(output_path))
            return output_path
        except Exception as exc:  # pragma: no cover - heavy dependency
            LOGGER.exception("XTTSv2 synthesis failed: %s", exc)
            if output_path.exists():
                output_path.unlink(missing_ok=True)  # type: ignore[arg-type]
            return None

    def _ensure_file(self, url: str, filename: str) -> Optional[Path]:
        if not url:
            return None

        destination = self.model_dir / filename
        if destination.exists():
            return destination

        LOGGER.info("Downloading %s -> %s", url, destination)
        try:
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            destination.write_bytes(response.content)
            return destination
        except Exception as exc:  # pragma: no cover - network
            LOGGER.warning("Failed to download %s: %s", url, exc)
            return None

    def _load_xtts(self) -> Optional[TTS]:
        if self._xtts_instance:
            return self._xtts_instance
        if self._xtts_failed or not TTS:
            return None

        try:
            use_cuda = bool(torch and torch.cuda.is_available())
        except Exception:  # pragma: no cover - torch optional
            use_cuda = False

        try:
            self._xtts_instance = TTS(model_name=self.xtts_model_name, progress_bar=False, use_cuda=use_cuda)
            return self._xtts_instance
        except Exception as exc:  # pragma: no cover - heavy dependency
            LOGGER.warning("Failed to load XTTS model '%s': %s", self.xtts_model_name, exc)
            self._xtts_failed = True
            return None


