"""
Wake-word detection for Jeeves — BYOV (Bring Your Own Voice) edition.

Replaces the old Porcupine-based engine with the on-device MFCC + DTW engine
from app.services.wake_word_byov. No API key. Works offline. Trains on your voice.

Module-level interface (unchanged):
    from app.services.wakeword import wakeword_engine
    wakeword_engine.start_listening(callback)  -> bool
    wakeword_engine.stop_listening()           -> None
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable

LOGGER    = logging.getLogger(__name__)
_AGENT_ID = os.getenv("WAKE_WORD_AGENT_ID", "jeeves")


class WakeWordEngine:
    """
    Adapter over WakeWordService with the legacy start_listening / stop_listening
    interface used by Jeeves startup and wake_word_listener.py.
    """

    def __init__(self, agent_id: str = _AGENT_ID) -> None:
        self._agent_id    = agent_id
        self._service     = None
        self.is_listening = False
        self._available   = False
        self._WakeWordService = None

        try:
            from app.services.wake_word_byov import WakeWordService, WakeWordStore
            self._WakeWordService = WakeWordService
            self._store           = WakeWordStore(agent_id)
            self._available       = True
        except Exception as exc:
            LOGGER.warning(
                "BYOV wake-word module unavailable "
                "(missing numpy/scipy/sounddevice?): %s", exc
            )

    def start_listening(self, callback: Callable[[], None]) -> bool:
        """
        Load the trained template and begin background detection.
        Returns True if started, False if no template exists or module unavailable.
        Train: python -m app.services.wake_word_byov.train_cli
        """
        if not self._available:
            LOGGER.warning("BYOV module not available — wake-word disabled")
            return False

        if not self._store.exists():
            LOGGER.info(
                "No wake-word template for agent_id='%s'. "
                "Train: python -m app.services.wake_word_byov.train_cli "
                "--agent-id %s",
                self._agent_id, self._agent_id,
            )
            return False

        if self.is_listening:
            LOGGER.warning("Wake-word listener already running")
            return False

        try:
            device = _parse_device_env()
            svc = self._WakeWordService(
                callback=callback,
                agent_id=self._agent_id,
                device=device,
            )
            svc.start()
            self._service     = svc
            self.is_listening = True
            LOGGER.info("BYOV wake-word listening started (agent_id=%s)", self._agent_id)
            return True
        except Exception as exc:
            LOGGER.exception("Failed to start BYOV wake-word service: %s", exc)
            return False

    def stop_listening(self) -> None:
        if not self.is_listening or self._service is None:
            return
        try:
            self._service.stop()
        except Exception as exc:
            LOGGER.warning("Error stopping wake-word service: %s", exc)
        finally:
            self._service     = None
            self.is_listening = False
            LOGGER.info("BYOV wake-word listener stopped")


def _parse_device_env() -> int | None:
    raw = os.getenv("WAKE_WORD_DEVICE", "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        LOGGER.warning("WAKE_WORD_DEVICE='%s' is not an integer — using default", raw)
        return None


# ── Module-level singleton ────────────────────────────────────────────────────

wakeword_engine = WakeWordEngine()
