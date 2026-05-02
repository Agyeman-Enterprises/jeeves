"""
MFCC feature extraction — numpy/scipy implementation.
Mirrors the algorithm in the JARVIS backend and the TypeScript Thredz version
so templates trained in any environment are cross-compatible.

Pipeline: PCM → pre-emphasis → framing → Hamming → FFT → mel filterbank → log → DCT → MFCC
"""

import numpy as np
from scipy.fft     import rfft, dct as scipy_dct
from scipy.signal  import resample_poly
from math          import gcd
from functools     import lru_cache

# ─── Constants (match TypeScript and JARVIS versions) ─────────────────────────
SAMPLE_RATE  = 16_000
N_FFT        = 512
HOP_LENGTH   = 160
N_MELS       = 40
N_MFCC       = 13
FMIN         = 80.0
FMAX         = 7_600.0
PRE_EMPHASIS = 0.97


# ─── Mel conversion ───────────────────────────────────────────────────────────

def hz_to_mel(hz: float) -> float:
    return 2595.0 * np.log10(1.0 + hz / 700.0)

def mel_to_hz(mel: float) -> float:
    return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)


# ─── Mel filterbank (cached) ──────────────────────────────────────────────────

@lru_cache(maxsize=1)
def build_mel_filterbank() -> np.ndarray:
    bins       = N_FFT // 2 + 1
    mel_min    = hz_to_mel(FMIN)
    mel_max    = hz_to_mel(FMAX)
    mel_points = np.linspace(mel_min, mel_max, N_MELS + 2)
    hz_points  = np.array([mel_to_hz(m) for m in mel_points])
    fft_bins   = np.floor((N_FFT + 1) * hz_points / SAMPLE_RATE).astype(int)

    filterbank = np.zeros((N_MELS, bins))
    for m in range(1, N_MELS + 1):
        for k in range(fft_bins[m - 1], fft_bins[m]):
            if 0 <= k < bins:
                filterbank[m - 1, k] = (k - fft_bins[m - 1]) / (fft_bins[m] - fft_bins[m - 1])
        for k in range(fft_bins[m], fft_bins[m + 1]):
            if 0 <= k < bins:
                filterbank[m - 1, k] = (fft_bins[m + 1] - k) / (fft_bins[m + 1] - fft_bins[m])
    return filterbank


# ─── Resampling ───────────────────────────────────────────────────────────────

def resample_to_16k(audio: np.ndarray, source_rate: int) -> np.ndarray:
    if source_rate == SAMPLE_RATE:
        return audio
    g    = gcd(SAMPLE_RATE, source_rate)
    up   = SAMPLE_RATE // g
    down = source_rate // g
    return resample_poly(audio, up, down).astype(np.float32)


# ─── MFCC extraction ──────────────────────────────────────────────────────────

def extract_mfcc(pcm: np.ndarray) -> np.ndarray:
    signal       = np.concatenate([[pcm[0]], pcm[1:] - PRE_EMPHASIS * pcm[:-1]])
    filterbank   = build_mel_filterbank()
    window       = np.hamming(N_FFT)
    frames: list[np.ndarray] = []

    for start in range(0, len(signal) - N_FFT, HOP_LENGTH):
        frame      = signal[start : start + N_FFT] * window
        spectrum   = np.abs(rfft(frame, n=N_FFT)) ** 2
        mel_energy = filterbank @ spectrum
        log_mel    = np.log(np.maximum(mel_energy, 1e-10))
        mfcc       = scipy_dct(log_mel, type=2, n=N_MFCC, norm=None)[:N_MFCC]
        frames.append(mfcc.astype(np.float32))

    if not frames:
        return np.zeros((1, N_MFCC), dtype=np.float32)
    return np.stack(frames)


def normalize_mfcc(frames: np.ndarray) -> np.ndarray:
    mean = frames.mean(axis=0, keepdims=True)
    std  = frames.std(axis=0, keepdims=True)
    std  = np.where(std < 1e-9, 1.0, std)
    return (frames - mean) / std
