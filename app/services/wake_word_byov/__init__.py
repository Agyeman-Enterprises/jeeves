"""
BYOV Wake Word — Jeeves edition.
Identical algorithm to the JARVIS version, isolated here so Jeeves has no
hard dependency on the JARVIS source tree.

Usage:
    from app.services.wake_word_byov import WakeWordService, WakeWordStore
"""

from .service import WakeWordService
from .store   import WakeWordStore

__all__ = ["WakeWordService", "WakeWordStore"]
