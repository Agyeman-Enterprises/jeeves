"""
Voice Pipeline — continuous listening with wake word → STT → JARVIS → TTS response.
Full loop: always listening, activates on wake word, transcribes, gets response, speaks.
"""
from __future__ import annotations

import asyncio
import logging
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

LOGGER = logging.getLogger(__name__)

# ── Optional audio imports ─────────────────────────────────────────────────
try:
    import pyaudio as _pyaudio
    _PYAUDIO_AVAILABLE = True
except ImportError:
    _pyaudio = None  # type: ignore[assignment]
    _PYAUDIO_AVAILABLE = False

try:
    import numpy as _np
    _NUMPY_AVAILABLE = True
except ImportError:
    _np = None  # type: ignore[assignment]
    _NUMPY_AVAILABLE = False


# Pipeline state constants
STATE_IDLE = "idle"
STATE_LISTENING = "listening"
STATE_RECORDING = "recording"
STATE_PROCESSING = "processing"
STATE_SPEAKING = "speaking"
STATE_STOPPED = "stopped"

# Audio recording settings
_SAMPLE_RATE = 16000
_CHANNELS = 1
_CHUNK_SIZE = 1024
_FORMAT_INT16 = 8  # pyaudio.paInt16 = 8
_MAX_RECORD_SECONDS = 5
_SILENCE_THRESHOLD = 500   # RMS below this = silence
_SILENCE_CHUNKS = 20        # ~1.25 seconds of silence to auto-stop


class VoicePipeline:
    """
    Manages the continuous voice loop:
      listen for wake word → activate → record utterance → STT → JARVIS → TTS → repeat
    """

    def __init__(self) -> None:
        self._state = STATE_STOPPED
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._orchestrator = None  # injected at start()
        self._lock = threading.Lock()
        self._last_transcript: Optional[str] = None
        self._last_response: Optional[str] = None
        self._error: Optional[str] = None

    # ── Public API ──────────────────────────────────────────────────────────

    def start(self, orchestrator: Any) -> Dict[str, Any]:
        """Start the continuous voice pipeline in a background thread."""
        with self._lock:
            if self._state not in (STATE_STOPPED, STATE_IDLE):
                return {"status": "already_running", "state": self._state}
            if not _PYAUDIO_AVAILABLE:
                return {
                    "status": "error",
                    "error": "pyaudio not installed. Run: pip install pyaudio",
                }
            self._orchestrator = orchestrator
            self._stop_event.clear()
            self._state = STATE_LISTENING
            self._thread = threading.Thread(
                target=self._pipeline_loop,
                daemon=True,
                name="VoicePipelineThread",
            )
            self._thread.start()
            LOGGER.info("Voice pipeline started")
            return {"status": "started", "state": self._state}

    def stop(self) -> Dict[str, Any]:
        """Stop the voice pipeline."""
        with self._lock:
            if self._state == STATE_STOPPED:
                return {"status": "already_stopped"}
            self._stop_event.set()
            self._state = STATE_STOPPED
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        LOGGER.info("Voice pipeline stopped")
        return {"status": "stopped"}

    def status(self) -> Dict[str, Any]:
        """Return current pipeline status."""
        return {
            "state": self._state,
            "running": self._state not in (STATE_STOPPED,),
            "last_transcript": self._last_transcript,
            "last_response": self._last_response,
            "error": self._error,
        }

    # ── Internal pipeline loop ──────────────────────────────────────────────

    def _pipeline_loop(self) -> None:
        """Main loop: wait for wake word → record → transcribe → respond → repeat."""
        LOGGER.info("Voice pipeline loop starting")
        try:
            while not self._stop_event.is_set():
                self._set_state(STATE_LISTENING)

                # Wait for activation (wake word or simulated trigger)
                activated = self._wait_for_activation()
                if not activated or self._stop_event.is_set():
                    continue

                # Play activation sound / say "Yes?"
                self._play_activation_cue()

                # Record the user's utterance
                self._set_state(STATE_RECORDING)
                audio_bytes = self._record_utterance()
                if not audio_bytes:
                    LOGGER.warning("No audio recorded — returning to listening")
                    continue

                # Transcribe
                self._set_state(STATE_PROCESSING)
                transcript = self._transcribe(audio_bytes)
                if not transcript:
                    LOGGER.info("Empty transcript — returning to listening")
                    continue
                self._last_transcript = transcript
                LOGGER.info("Transcript: %s", transcript)

                # Route through JARVIS
                response_text = self._route_to_jarvis(transcript)
                self._last_response = response_text
                LOGGER.info("JARVIS response: %s", response_text[:100] if response_text else "")

                # Speak the response
                self._set_state(STATE_SPEAKING)
                self._speak(response_text or "I'm sorry, I couldn't process that.")

        except Exception as exc:
            LOGGER.exception("Voice pipeline crashed: %s", exc)
            self._error = str(exc)
        finally:
            self._set_state(STATE_STOPPED)
            LOGGER.info("Voice pipeline loop exited")

    def _wait_for_activation(self) -> bool:
        """
        Wait for a wake-word trigger.
        Uses the wakeword_engine if available; otherwise polls an internal flag
        that can be set via the /voice/pipeline/activate endpoint.
        """
        try:
            from app.services.wakeword import wakeword_engine
            if wakeword_engine.engine is not None:
                # Engine is running; wait until it fires our callback
                activated = threading.Event()

                def _on_wake():
                    activated.set()

                # Temporarily override callback
                original_cb = getattr(wakeword_engine, "_callback", None)
                wakeword_engine._callback = _on_wake
                # Poll every 0.5s so we can check stop_event
                while not self._stop_event.is_set():
                    if activated.wait(timeout=0.5):
                        wakeword_engine._callback = original_cb
                        return True
                wakeword_engine._callback = original_cb
                return False
        except Exception:
            pass

        # Fallback: poll for external activation signal
        while not self._stop_event.is_set():
            if getattr(self, "_activation_pending", False):
                self._activation_pending = False  # type: ignore[attr-defined]
                return True
            time.sleep(0.3)
        return False

    def trigger_activation(self) -> None:
        """Externally trigger voice pipeline activation (e.g. from API endpoint)."""
        self._activation_pending = True  # type: ignore[attr-defined]

    def _play_activation_cue(self) -> None:
        """Speak a short acknowledgment to signal JARVIS is listening."""
        try:
            self._speak("Yes?", blocking=True, max_wait=3)
        except Exception as exc:
            LOGGER.debug("Activation cue failed: %s", exc)

    def _record_utterance(self, max_seconds: int = _MAX_RECORD_SECONDS) -> Optional[bytes]:
        """Record audio until silence is detected or max duration reached."""
        if not _PYAUDIO_AVAILABLE or _pyaudio is None:
            return None
        try:
            pa = _pyaudio.PyAudio()
            stream = pa.open(
                format=_FORMAT_INT16,
                channels=_CHANNELS,
                rate=_SAMPLE_RATE,
                input=True,
                frames_per_buffer=_CHUNK_SIZE,
            )
            frames = []
            max_chunks = int(_SAMPLE_RATE / _CHUNK_SIZE * max_seconds)
            silence_count = 0

            for _ in range(max_chunks):
                if self._stop_event.is_set():
                    break
                data = stream.read(_CHUNK_SIZE, exception_on_overflow=False)
                frames.append(data)

                # Simple silence detection using RMS
                if _NUMPY_AVAILABLE and _np is not None:
                    try:
                        audio_array = _np.frombuffer(data, dtype=_np.int16).astype(_np.float32)
                        rms = _np.sqrt(_np.mean(audio_array ** 2))
                        if rms < _SILENCE_THRESHOLD:
                            silence_count += 1
                        else:
                            silence_count = 0
                        if silence_count >= _SILENCE_CHUNKS and len(frames) > 10:
                            break  # Enough silence — utterance complete
                    except Exception:
                        pass

            stream.stop_stream()
            stream.close()
            pa.terminate()

            if not frames:
                return None

            # Convert to WAV bytes
            import wave
            import io
            buf = io.BytesIO()
            with wave.open(buf, "wb") as wf:
                wf.setnchannels(_CHANNELS)
                wf.setsampwidth(2)  # 16-bit = 2 bytes
                wf.setframerate(_SAMPLE_RATE)
                wf.writeframes(b"".join(frames))
            return buf.getvalue()
        except Exception as exc:
            LOGGER.exception("Recording failed: %s", exc)
            return None

    def _transcribe(self, audio_bytes: bytes) -> Optional[str]:
        """Transcribe audio bytes to text using available STT."""
        try:
            from app.services.stt_whisper import stt_client
            if stt_client.model is not None:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp.write(audio_bytes)
                    tmp_path = tmp.name
                try:
                    text = stt_client.transcribe_file(tmp_path)
                    return text.strip() if text else None
                finally:
                    try:
                        Path(tmp_path).unlink(missing_ok=True)
                    except Exception:
                        pass
        except Exception as exc:
            LOGGER.warning("Local Whisper transcription failed: %s", exc)

        # Fallback: Fireworks STT
        try:
            from app.services.fireworks_service import fireworks_stt
            if fireworks_stt.is_available():
                text, _ = fireworks_stt.transcribe(audio_bytes, filename="utterance.wav")
                return text.strip() if text else None
        except Exception as exc:
            LOGGER.warning("Fireworks transcription failed: %s", exc)

        return None

    def _route_to_jarvis(self, text: str) -> Optional[str]:
        """Send transcript through the JARVIS orchestrator and return response text."""
        if self._orchestrator is None:
            return "Orchestrator not available."
        try:
            response = self._orchestrator.route_query(text, context={"source": "voice_pipeline"})
            if hasattr(response, "content"):
                return response.content
            return str(response)
        except Exception as exc:
            LOGGER.exception("Orchestrator routing failed: %s", exc)
            return f"I encountered an error: {exc}"

    def _speak(self, text: str, blocking: bool = False, max_wait: int = 30) -> None:
        """Synthesize text and play it. Optionally blocks until playback finishes."""
        try:
            from app.services.local_tts import synthesize_to_wav
            audio_path = synthesize_to_wav(text)
            if audio_path and Path(audio_path).exists():
                _play_wav(audio_path, blocking=blocking, max_wait=max_wait)
            else:
                LOGGER.warning("TTS produced no audio for: %s", text[:50])
        except Exception as exc:
            LOGGER.warning("speak() failed: %s", exc)

    def _set_state(self, state: str) -> None:
        with self._lock:
            self._state = state


def _play_wav(path: str, blocking: bool = False, max_wait: int = 30) -> None:
    """Play a WAV file using the best available method on Windows."""
    import subprocess
    import sys

    def _do_play() -> None:
        try:
            # Try: winsound (Windows built-in, no deps)
            import winsound
            winsound.PlaySound(path, winsound.SND_FILENAME)
        except ImportError:
            # Non-Windows fallback: ffplay / aplay
            players = ["ffplay", "aplay", "mpg123"]
            for player in players:
                try:
                    subprocess.run(
                        [player, "-nodisp", "-autoexit", path],
                        capture_output=True,
                        timeout=max_wait,
                    )
                    return
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue
            LOGGER.warning("No audio player found to play WAV")
        except Exception as exc:
            LOGGER.warning("WAV playback failed: %s", exc)

    if blocking:
        _do_play()
    else:
        t = threading.Thread(target=_do_play, daemon=True)
        t.start()


# ── Module-level singleton ─────────────────────────────────────────────────
voice_pipeline = VoicePipeline()
