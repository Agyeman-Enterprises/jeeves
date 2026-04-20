from __future__ import annotations

import logging
import os
from typing import Generator, Optional

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None  # type: ignore[assignment, misc]

LOGGER = logging.getLogger(__name__)

WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL", "small")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")  # "cpu" or "cuda"
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")  # "int8", "float16", "float32"


class WhisperSTT:
    def __init__(self, model_name: str = WHISPER_MODEL_NAME) -> None:
        if not WhisperModel:
            LOGGER.error("faster-whisper not installed. Install with: pip install faster-whisper")
            self.model = None
            return

        LOGGER.info("Loading faster-whisper model: %s (device=%s, compute_type=%s)", model_name, WHISPER_DEVICE, WHISPER_COMPUTE_TYPE)
        try:
            use_cuda = WHISPER_DEVICE == "cuda"
            self.model = WhisperModel(
                model_name,
                device=WHISPER_DEVICE,
                compute_type=WHISPER_COMPUTE_TYPE,
            )
            LOGGER.info("Whisper model loaded successfully")
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Failed to load Whisper model: %s", exc)
            self.model = None

    def transcribe_file(self, file_path: str) -> Optional[str]:
        if not self.model:
            LOGGER.error("Whisper model not available")
            return None

        try:
            segments, info = self.model.transcribe(file_path, beam_size=5)
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text)
            result = " ".join(text_parts).strip()
            LOGGER.debug("Transcribed %d segments, language=%s", len(text_parts), info.language)
            return result if result else None
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Whisper transcription failed: %s", exc)
            return None

    def transcribe_stream(self, audio_stream: Generator[bytes, None, None]) -> Generator[str, None, None]:
        """
        Stream transcription for real-time audio input.
        Yields partial transcriptions as they become available.
        """
        if not self.model:
            LOGGER.error("Whisper model not available for streaming")
            return

        # For now, collect chunks and transcribe in batches
        # TODO: Implement true streaming with VAD (Voice Activity Detection)
        audio_chunks = []
        for chunk in audio_stream:
            audio_chunks.append(chunk)
            # Transcribe every N chunks or on silence
            if len(audio_chunks) >= 10:  # Arbitrary threshold
                # Combine chunks and transcribe
                # This is a simplified version; real streaming would use VAD
                pass

        yield "Streaming transcription not yet fully implemented"


stt_client = WhisperSTT()

