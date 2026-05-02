"""
WakeWordService — background thread wake word detection for Jeeves.
"""

import threading
import time
import logging
from collections.abc import Callable

import numpy as np

from .features  import extract_mfcc, normalize_mfcc, SAMPLE_RATE
from .dtw       import dtw_distance
from .store     import WakeWordStore
from .recorder  import StreamBuffer, RING_SAMPLES

logger = logging.getLogger(__name__)

POLL_INTERVAL  = 0.2
WINDOW_SECONDS = 1.5
WINDOW_SAMPLES = int(SAMPLE_RATE * WINDOW_SECONDS)
RMS_GATE       = 0.005
COOLDOWN       = 1.5


class WakeWordService:
    """
    Continuous BYOV wake word detector.

    Usage:
        svc = WakeWordService(callback=lambda: ..., agent_id="jeeves")
        svc.start()
        svc.stop()
    """

    def __init__(
        self,
        callback:  Callable[[], None],
        agent_id:  str = "default",
        device:    int | None = None,
    ) -> None:
        self._callback  = callback
        self._store     = WakeWordStore(agent_id)
        self._device    = device
        self._thread:   threading.Thread | None = None
        self._stop_evt  = threading.Event()
        self._buffer:   StreamBuffer | None = None
        self._template: np.ndarray | None = None
        self._threshold = 0.0

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.is_running:
            return
        template_obj = self._store.load()
        if template_obj is None:
            raise RuntimeError(
                f"No wake word template for agent_id='{self._store._path.stem}'. "
                "Train first: python -m app.services.wake_word_byov.train_cli"
            )
        self._template  = np.array(template_obj.frames, dtype=np.float32)
        self._threshold = template_obj.threshold
        logger.info("WakeWordService: loaded template '%s' (threshold=%.3f)",
                    template_obj.phrase, self._threshold)

        self._stop_evt.clear()
        self._buffer = StreamBuffer(device=self._device)
        self._buffer.start()

        self._thread = threading.Thread(
            target=self._run, name="WakeWordService", daemon=True
        )
        self._thread.start()
        logger.info("WakeWordService: listening started")

    def stop(self) -> None:
        self._stop_evt.set()
        if self._buffer is not None:
            self._buffer.stop()
            self._buffer = None
        if self._thread is not None:
            self._thread.join(timeout=3.0)
            self._thread = None
        logger.info("WakeWordService: stopped")

    def _run(self) -> None:
        last_trigger = 0.0
        while not self._stop_evt.is_set():
            time.sleep(POLL_INTERVAL)
            if self._buffer is None or self._template is None:
                continue
            now = time.monotonic()
            if now - last_trigger < COOLDOWN:
                continue
            snapshot = self._buffer.read()
            window   = snapshot[-WINDOW_SAMPLES:]
            rms      = float(np.sqrt(np.mean(window ** 2)))
            if rms < RMS_GATE:
                continue
            try:
                dist = dtw_distance(normalize_mfcc(extract_mfcc(window)), self._template)
            except Exception:
                logger.exception("WakeWordService: detection error")
                continue
            if dist < self._threshold:
                logger.info("Wake word detected (dist=%.3f < threshold=%.3f)",
                            dist, self._threshold)
                last_trigger = now
                try:
                    self._callback()
                except Exception:
                    logger.exception("WakeWordService: callback raised")
