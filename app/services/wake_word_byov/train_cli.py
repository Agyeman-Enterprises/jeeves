"""
Interactive CLI trainer for the Jeeves BYOV wake word system.

Usage (from C:/DEV/jeeves):
    python3 -m app.services.wake_word_byov.train_cli
    python3 -m app.services.wake_word_byov.train_cli --agent-id jeeves --samples 8
"""

import argparse
import sys
import time

import numpy as np

from .features  import extract_mfcc, normalize_mfcc
from .dtw       import compute_threshold
from .store     import WakeWordStore, WakeWordTemplate
from .recorder  import record_sample, SAMPLE_SECONDS

DEFAULT_SAMPLES = 8
COUNTDOWN       = 3


def _hr(char: str = "─", width: int = 56) -> None:
    print(char * width)


def _countdown(n: int = COUNTDOWN) -> None:
    for i in range(n, 0, -1):
        print(f"  {i}...", end="", flush=True)
        time.sleep(1)
    print()


def _record_with_feedback(sample_num: int, total: int) -> np.ndarray:
    print(f"\n  Sample {sample_num}/{total}  — say your wake phrase clearly.")
    _countdown()
    print(f"  🔴 Recording for {SAMPLE_SECONDS:.0f}s …", end="", flush=True)
    pcm = record_sample()
    print("  ✓")
    return pcm


def train(
    agent_id:  str = "jeeves",
    n_samples: int = DEFAULT_SAMPLES,
    device:    int | None = None,
    phrase:    str | None = None,
) -> None:
    _hr("═")
    print("  Jeeves — BYOV Wake Word Trainer")
    _hr("═")
    print(f"  Agent ID : {agent_id}")
    print(f"  Samples  : {n_samples}")
    print()

    if phrase is None:
        phrase = input("  Enter your wake phrase (e.g. 'Hey Jeeves'): ").strip()
    if not phrase:
        print("ERROR: wake phrase cannot be empty.", file=sys.stderr)
        sys.exit(1)

    print(f"\n  You will be asked to say '{phrase}' {n_samples} times.")
    print("  Speak at a normal volume, ~30 cm from the mic.")
    input("  Press Enter when ready…")

    mfcc_samples: list[np.ndarray] = []
    for i in range(1, n_samples + 1):
        pcm    = _record_with_feedback(i, n_samples)
        frames = normalize_mfcc(extract_mfcc(pcm))
        mfcc_samples.append(frames)

    print()
    _hr()
    print("  Computing template and detection threshold…")

    template_frames, threshold = compute_threshold(mfcc_samples)

    print(f"  Threshold  : {threshold:.4f}")
    print(f"  Frames     : {len(template_frames)}")

    store    = WakeWordStore(agent_id)
    template = WakeWordTemplate(
        frames       = template_frames.tolist(),
        threshold    = threshold,
        phrase       = phrase,
        created_at   = time.time(),
        sample_count = n_samples,
    )
    store.save(template)

    _hr()
    print(f"  ✅  Template saved → {store._path}")
    print(f"  Wake phrase : '{phrase}'")
    print(f"  Agent ID    : {agent_id}")
    _hr("═")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python3 -m app.services.wake_word_byov.train_cli",
        description="Train a BYOV wake word template for Jeeves.",
    )
    parser.add_argument("--agent-id", default="jeeves")
    parser.add_argument("--samples",  type=int, default=DEFAULT_SAMPLES)
    parser.add_argument("--device",   type=int, default=None)
    parser.add_argument("--phrase",   default=None)
    parser.add_argument("--list-devices", action="store_true")

    args = parser.parse_args()

    if args.list_devices:
        import sounddevice as sd
        print(sd.query_devices())
        sys.exit(0)

    if args.samples < 2:
        print("ERROR: --samples must be at least 2.", file=sys.stderr)
        sys.exit(1)

    train(
        agent_id  = args.agent_id,
        n_samples = args.samples,
        device    = args.device,
        phrase    = args.phrase,
    )


if __name__ == "__main__":
    main()
