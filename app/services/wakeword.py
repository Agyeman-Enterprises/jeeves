from __future__ import annotations

import logging
import os
import threading
from pathlib import Path
from typing import Callable, Optional

try:
    import pvporcupine
    import pyaudio
except ImportError:
    pvporcupine = None  # type: ignore[assignment, misc]
    pyaudio = None  # type: ignore[assignment, misc]

LOGGER = logging.getLogger(__name__)

WAKE_WORD_MODEL_PATH = os.getenv("WAKE_WORD_MODEL_PATH", "data/porcupine/jarvis.ppn")
WAKE_WORD_KEYWORD = os.getenv("WAKE_WORD", "jarvis").lower()


class WakeWordEngine:
    """
    Local wake-word detection using Porcupine.
    Listens continuously for the wake word and triggers a callback when detected.
    """

    def __init__(self, keyword: str = WAKE_WORD_KEYWORD, model_path: Optional[str] = None) -> None:
        if not pvporcupine or not pyaudio:
            LOGGER.warning("pvporcupine or pyaudio not installed. Wake-word detection disabled.")
            self.engine = None
            self.is_listening = False
            return

        self.keyword = keyword
        self.model_path = model_path or WAKE_WORD_MODEL_PATH
        self.engine = None
        self.is_listening = False
        self._thread: Optional[threading.Thread] = None
        self._pa: Optional[pyaudio.PyAudio] = None
        self._stream: Optional[pyaudio.Stream] = None

        try:
            # Try to load custom model file if it exists
            if Path(self.model_path).exists():
                LOGGER.info("Loading custom Porcupine model from: %s", self.model_path)
                self.engine = pvporcupine.create(keyword_paths=[self.model_path])
            else:
                # Use built-in keyword (requires Porcupine access key)
                access_key = os.getenv("PORCUPINE_ACCESS_KEY")
                if access_key:
                    LOGGER.info("Using built-in Porcupine keyword: %s", keyword)
                    self.engine = pvporcupine.create(access_key=access_key, keywords=[keyword])
                else:
                    LOGGER.warning(
                        "Porcupine access key not set (PORCUPINE_ACCESS_KEY). "
                        "Wake-word detection disabled. Get a free key at: https://console.picovoice.ai/"
                    )
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Failed to initialize Porcupine engine: %s", exc)
            self.engine = None

    def start_listening(self, callback: Callable[[], None]) -> bool:
        """
        Start listening for the wake word in a background thread.
        Returns True if listening started successfully.
        """
        if not self.engine:
            LOGGER.error("Wake-word engine not initialized")
            return False

        if self.is_listening:
            LOGGER.warning("Wake-word listener already running")
            return False

        self.is_listening = True
        self._thread = threading.Thread(
            target=self._listen_loop,
            args=(callback,),
            daemon=True,
            name="WakeWordListener",
        )
        self._thread.start()
        LOGGER.info("Wake-word listener started (keyword: %s)", self.keyword)
        return True

    def stop_listening(self) -> None:
        """Stop the wake-word listener."""
        if not self.is_listening:
            return

        self.is_listening = False
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

        if self._pa:
            try:
                self._pa.terminate()
            except Exception:
                pass
            self._pa = None

        if self._thread:
            self._thread.join(timeout=2.0)

        LOGGER.info("Wake-word listener stopped")

    def _listen_loop(self, callback: Callable[[], None]) -> None:
        """Internal loop that processes audio and detects wake words."""
        if not self.engine:
            return

        try:
            self._pa = pyaudio.PyAudio()
            sample_rate = self.engine.sample_rate
            frame_length = self.engine.frame_length

            self._stream = self._pa.open(
                rate=sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=frame_length,
            )

            LOGGER.debug("Wake-word audio stream opened (rate=%d, frame_length=%d)", sample_rate, frame_length)

            while self.is_listening:
                try:
                    pcm = self._stream.read(frame_length, exception_on_overflow=False)
                    keyword_index = self.engine.process(pcm)

                    if keyword_index >= 0:
                        LOGGER.info("Wake word detected: %s", self.keyword)
                        callback()
                except Exception as exc:  # noqa: BLE001
                    if self.is_listening:
                        LOGGER.exception("Error in wake-word detection loop: %s", exc)
                    break

        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Wake-word listener thread error: %s", exc)
        finally:
            self.stop_listening()

    def __del__(self) -> None:
        """Cleanup on deletion."""
        self.stop_listening()
        if self.engine:
            try:
                self.engine.delete()
            except Exception:
                pass


# Global instance
wakeword_engine = WakeWordEngine()

