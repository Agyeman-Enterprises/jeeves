"""
BYOV Wake-Word Listener for Jeeves.

Replaces the OpenWakeWord engine with on-device MFCC + DTW detection from
app.services.wake_word_byov. The full voice capture -> STT -> LLM -> TTS
pipeline is unchanged.

Usage (standalone):
    python -m app.services.wake_word_listener

Training:
    python -m app.services.wake_word_byov.train_cli --agent-id jeeves
"""

from __future__ import annotations

import io
import logging
import os
import struct
import subprocess
import tempfile
import time
import wave

import requests

from app.services.wake_word_byov import WakeWordService, WakeWordStore

LOGGER = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────

BACKEND_URL       = os.getenv("JARVIS_BACKEND_URL", "http://localhost:8000")
AGENT_ID          = os.getenv("WAKE_WORD_AGENT_ID", "jeeves")
LISTEN_DURATION   = 10
SILENCE_THRESHOLD = 500
SILENCE_DURATION  = 2.0


# ── Full voice pipeline ───────────────────────────────────────────────────────

def _capture_speech() -> bytes | None:
    """Capture post-wakeword speech via sounddevice, return WAV bytes."""
    try:
        import sounddevice as sd
    except ImportError:
        LOGGER.error("sounddevice not installed")
        return None

    RATE  = 16_000
    CHUNK = 1_280
    _raw_chunks: list[bytes] = []

    def _callback(
        indata:    bytes,
        frames:    int,
        time_info: object,
        status:    sd.CallbackFlags,
    ) -> None:
        _raw_chunks.append(bytes(indata))

    stream = sd.RawInputStream(
        samplerate=RATE, channels=1, dtype="int16",
        blocksize=CHUNK, callback=_callback
    )

    collected: list[bytes] = []
    silence_start: float | None = None
    deadline = time.time() + LISTEN_DURATION

    LOGGER.info("Listening for speech (max %.0fs)...", LISTEN_DURATION)
    with stream:
        while time.time() < deadline:
            time.sleep(0.04)
            while _raw_chunks:
                chunk = _raw_chunks.pop(0)
                collected.append(chunk)
                n_samples = len(chunk) // 2
                samples   = struct.unpack(f"{n_samples}h", chunk)
                peak      = max(abs(s) for s in samples)
                if peak < SILENCE_THRESHOLD:
                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start >= SILENCE_DURATION:
                        LOGGER.info("Silence detected — stopping capture")
                        break
                else:
                    silence_start = None
            else:
                continue
            break   # inner break propagated by else/continue/break pattern

    if not collected:
        return None

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(RATE)
        wf.writeframes(b"".join(collected))
    return buf.getvalue()


def _process_speech(audio_data: bytes) -> None:
    """Transcribe -> query JARVIS backend -> synthesise reply -> play."""
    try:
        files = {"file": ("audio.wav", audio_data, "audio/wav")}
        resp  = requests.post(f"{BACKEND_URL}/api/voice/transcribe",
                               files=files, timeout=30)
        resp.raise_for_status()
        text = resp.json().get("text", "")
        if not text:
            LOGGER.warning("No transcription returned")
            return

        LOGGER.info("Transcribed: %s", text)

        q_resp = requests.post(f"{BACKEND_URL}/query",
                                json={"query": text}, timeout=60)
        q_resp.raise_for_status()
        reply = q_resp.json().get("content") or q_resp.json().get("reply", "")
        LOGGER.info("Jeeves reply: %s...", reply[:80])

        tts = requests.post(f"{BACKEND_URL}/api/voice/speak",
                             json={"text": reply}, timeout=30)
        tts.raise_for_status()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(tts.content)
            tmp_path = tmp.name

        _play_audio(tmp_path)

        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    except Exception as exc:
        LOGGER.error("Error processing speech: %s", exc)


def _play_audio(path: str) -> None:
    import platform
    system = platform.system()
    try:
        if system == "Windows":
            import winsound
            winsound.PlaySound(path, winsound.SND_FILENAME)
        elif system == "Darwin":
            subprocess.run(["afplay", path], check=False)
        else:
            subprocess.run(["aplay", path], check=False)
    except Exception as exc:
        LOGGER.warning("Could not play audio: %s", exc)


# ── WakeWordListener ──────────────────────────────────────────────────────────

class WakeWordListener:
    """
    Wraps WakeWordService and adds the full voice-capture pipeline.
    Detects wake word -> captures speech -> sends to JARVIS -> plays reply.
    """

    def __init__(self, agent_id: str = AGENT_ID) -> None:
        self._agent_id = agent_id
        self._svc: WakeWordService | None = None

    def _on_wake_word(self) -> None:
        LOGGER.info("*** WAKE WORD DETECTED ***")
        import threading
        threading.Thread(target=self._handle_wake, daemon=True).start()

    def _handle_wake(self) -> None:
        audio = _capture_speech()
        if audio:
            _process_speech(audio)

    def start(self) -> None:
        store = WakeWordStore(self._agent_id)
        if not store.exists():
            LOGGER.error(
                "No wake-word template for agent_id='%s'. "
                "Train first: python -m app.services.wake_word_byov.train_cli "
                "--agent-id %s",
                self._agent_id, self._agent_id,
            )
            return

        self._svc = WakeWordService(
            callback=self._on_wake_word,
            agent_id=self._agent_id,
        )
        self._svc.start()

        LOGGER.info("=" * 60)
        LOGGER.info("  Jeeves BYOV Wake-Word Listener started")
        LOGGER.info("  Agent ID : %s", self._agent_id)
        LOGGER.info("  Say your trained phrase to activate Jeeves")
        LOGGER.info("=" * 60)

        try:
            while self._svc.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            LOGGER.info("Shutting down...")
        finally:
            self.stop()

    def stop(self) -> None:
        if self._svc is not None:
            self._svc.stop()
            self._svc = None
        LOGGER.info("Wake-word listener stopped")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    WakeWordListener().start()


if __name__ == "__main__":
    main()
