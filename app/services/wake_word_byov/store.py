"""
Template persistence — JSON files in ~/.jeeves/wake_word/.
One file per agent_id so different Jeeves instances can have different phrases.
"""

import json
import os
from pathlib    import Path
from dataclasses import dataclass, asdict
import numpy as np


@dataclass
class WakeWordTemplate:
    frames:       list[list[float]]   # serialised np.ndarray (n_frames, N_MFCC)
    threshold:    float
    phrase:       str
    created_at:   float               # unix timestamp
    sample_count: int


class WakeWordStore:

    def __init__(self, agent_id: str = "default"):
        self._path = self._resolve_path(agent_id)

    @staticmethod
    def _resolve_path(agent_id: str) -> Path:
        base = Path(os.environ.get("JEEVES_DATA_DIR", Path.home() / ".jeeves"))
        wake = base / "wake_word"
        wake.mkdir(parents=True, exist_ok=True)
        return wake / f"{agent_id}.json"

    def save(self, template: WakeWordTemplate) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(asdict(template), f, indent=2)

    def load(self) -> WakeWordTemplate | None:
        if not self._path.exists():
            return None
        with open(self._path, encoding="utf-8") as f:
            data = json.load(f)
        return WakeWordTemplate(**data)

    def delete(self) -> None:
        if self._path.exists():
            self._path.unlink()

    def exists(self) -> bool:
        return self._path.exists()

    def frames_as_array(self) -> np.ndarray | None:
        t = self.load()
        if t is None:
            return None
        return np.array(t.frames, dtype=np.float32)
