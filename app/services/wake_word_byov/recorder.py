"""
Audio recording utilities for BYOV wake word.
"""

import threading
import numpy as np
import sounddevice as sd

from .features import resample_to_16k, SAMPLE_RATE

RING_SECONDS   = 3
RING_SAMPLES   = SAMPLE_RATE * RING_SECONDS
SAMPLE_SECONDS = 2.0
SAMPLE_SAMPLES = int(SAMPLE_RATE * SAMPLE_SECONDS)
BLOCK_SIZE     = 512


def _device_info(device: int | None) -> dict[str, object]:
    info = sd.query_devices(device, kind="input")
    if not isinstance(info, dict):
        raise RuntimeError(f"sounddevice.query_devices returned {type(info)}")
    return dict(info)


def _native_rate(device: int | None) -> int:
    return int(_device_info(device)["default_samplerate"])


class StreamBuffer:
    """Continuous ring buffer of 16 kHz mono PCM fed by sounddevice."""

    def __init__(self, device: int | None = None) -> None:
        self._device   = device
        self._ring     = np.zeros(RING_SAMPLES, dtype=np.float32)
        self._pos      = 0
        self._lock     = threading.Lock()
        self._stream: sd.InputStream | None = None
        self._src_rate = SAMPLE_RATE

    def _callback(
        self,
        indata:    np.ndarray,
        frames:    int,
        time_info: object,
        status:    sd.CallbackFlags,
    ) -> None:
        if status:
            return
        mono = indata[:, 0].astype(np.float32)
        if self._src_rate != SAMPLE_RATE:
            mono = resample_to_16k(mono, self._src_rate)
        with self._lock:
            n   = len(mono)
            end = self._pos + n
            if end <= RING_SAMPLES:
                self._ring[self._pos:end] = mono
            else:
                split = RING_SAMPLES - self._pos
                self._ring[self._pos:] = mono[:split]
                self._ring[:n - split] = mono[split:]
            self._pos = end % RING_SAMPLES

    def start(self) -> None:
        self._src_rate = _native_rate(self._device)
        self._stream   = sd.InputStream(
            samplerate=self._src_rate,
            channels=1,
            dtype="float32",
            blocksize=BLOCK_SIZE,
            device=self._device,
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def read(self) -> np.ndarray:
        with self._lock:
            pos = self._pos
            return np.concatenate([self._ring[pos:], self._ring[:pos]])


def record_sample(
    duration: float = SAMPLE_SECONDS,
    device: int | None = None,
) -> np.ndarray:
    """Block for `duration` seconds and return a 16 kHz mono float32 PCM array."""
    native   = _native_rate(device)
    n_frames = int(native * duration)

    raw: np.ndarray = sd.rec(
        n_frames,
        samplerate=native,
        channels=1,
        dtype="float32",
        device=device,
    )
    sd.wait()

    mono   = raw[:, 0]
    if native != SAMPLE_RATE:
        mono = resample_to_16k(mono, native)

    target = int(SAMPLE_RATE * duration)
    if len(mono) > target:
        mono = mono[:target]
    elif len(mono) < target:
        mono = np.pad(mono, (0, target - len(mono)))

    return mono.astype(np.float32)
