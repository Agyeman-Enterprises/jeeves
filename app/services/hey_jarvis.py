"""
Hey Jarvis — Wake Word Listener
Continuously listens for "Hey Jarvis" or "Jarvis" using SpeechRecognition.
When detected, opens the dashboard and notifies the backend.
No API keys required — uses Google's free speech recognition.
"""
from __future__ import annotations

import logging
import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

# Add project root to path so we can import backend
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

try:
    import speech_recognition as sr
except ImportError:
    print("SpeechRecognition not installed. Run: pip install SpeechRecognition pyaudio")
    sys.exit(1)

LOGGER = logging.getLogger("hey_jarvis")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [HeyJarvis] %(message)s",
)

WAKE_PHRASES = {"hey jarvis", "jarvis", "hey jarv", "jarv"}
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000/jarvis/home")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
ALREADY_OPENED = False


def notify_backend() -> None:
    """Tell the backend a wake word was detected — triggers empire wake-up sequence."""
    try:
        import requests
        requests.get(f"{BACKEND_URL}/api/empire/wake-up", timeout=3)
        LOGGER.info("Backend wake-up triggered")
    except Exception:
        pass  # Backend may not be running yet


def open_dashboard() -> None:
    global ALREADY_OPENED
    if not ALREADY_OPENED:
        LOGGER.info("Opening dashboard: %s", FRONTEND_URL)
        webbrowser.open(FRONTEND_URL)
        ALREADY_OPENED = True
    else:
        LOGGER.info("Dashboard already open — triggering voice interaction")
    notify_backend()


def on_wake_word_detected(phrase: str) -> None:
    LOGGER.info("*** WAKE WORD DETECTED: '%s' ***", phrase)
    # Run in thread so we don't block the listener loop
    threading.Thread(target=open_dashboard, daemon=True).start()


def _find_best_mic_device() -> int | None:
    """Find the mic device with the highest actual audio level (not silence)."""
    import struct
    import pyaudio as _pa
    p = _pa.PyAudio()
    best_dev = None
    best_peak = 0
    CHUNK = 512
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info["maxInputChannels"] < 1:
            continue
        try:
            stream = p.open(format=_pa.paInt16, channels=1, rate=16000,
                            input=True, input_device_index=i, frames_per_buffer=CHUNK)
            data = stream.read(CHUNK, exception_on_overflow=False)
            stream.close()
            peak = max(abs(s) for s in struct.unpack(f"{CHUNK}h", data))
            LOGGER.info("  [%d] %s  peak=%d", i, info["name"][:50], peak)
            if peak > best_peak:
                best_peak = peak
                best_dev = i
        except Exception:
            pass
    p.terminate()
    LOGGER.info("Best mic device: [%s] (peak=%d)", best_dev, best_peak)
    return best_dev


def listen_loop() -> None:
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.5

    LOGGER.info("Scanning microphones for best input device...")
    device_index = _find_best_mic_device()
    mic = sr.Microphone(device_index=device_index)

    LOGGER.info("Calibrating for ambient noise (1 second)...")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
    LOGGER.info("Calibration done. Energy threshold: %.0f", recognizer.energy_threshold)
    LOGGER.info("Listening for wake word... Say 'Hey Jarvis' or 'Jarvis'")

    consecutive_errors = 0
    MAX_ERRORS = 10

    while True:
        try:
            with mic as source:
                # Listen for up to 3 seconds of speech
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)

            # Try Google (free, no key needed)
            try:
                text = recognizer.recognize_google(audio).lower()
                LOGGER.debug("Heard: '%s'", text)

                for phrase in WAKE_PHRASES:
                    if phrase in text:
                        on_wake_word_detected(text)
                        break

                consecutive_errors = 0

            except sr.UnknownValueError:
                # Couldn't understand audio — normal, keep going
                consecutive_errors = 0

            except sr.RequestError as e:
                LOGGER.warning("Google Speech API error: %s (offline?)", e)
                consecutive_errors += 1

        except sr.WaitTimeoutError:
            # No speech detected in timeout window — normal
            consecutive_errors = 0

        except OSError as e:
            LOGGER.error("Microphone error: %s", e)
            consecutive_errors += 1
            time.sleep(2)

        except Exception as e:  # noqa: BLE001
            LOGGER.exception("Unexpected error: %s", e)
            consecutive_errors += 1
            time.sleep(1)

        if consecutive_errors >= MAX_ERRORS:
            LOGGER.error("Too many consecutive errors (%d). Restarting listener in 5s...", MAX_ERRORS)
            time.sleep(5)
            consecutive_errors = 0


def main() -> None:
    LOGGER.info("="*50)
    LOGGER.info("  HEY JARVIS — Wake Word Listener")
    LOGGER.info("  Say 'Hey Jarvis' to activate")
    LOGGER.info("="*50)

    # Check microphone
    try:
        sr.Microphone()
    except OSError as e:
        LOGGER.error("No microphone found: %s", e)
        LOGGER.error("Plug in a microphone and restart.")
        sys.exit(1)

    listen_loop()


if __name__ == "__main__":
    main()
