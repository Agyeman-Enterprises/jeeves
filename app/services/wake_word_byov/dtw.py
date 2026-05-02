"""
Dynamic Time Warping — numpy implementation.
Mirrors dtw.ts exactly so Python-trained templates match browser detection.
"""

import numpy as np


def dtw_distance(a: np.ndarray, b: np.ndarray) -> float:
    n, m = len(a), len(b)
    if n == 0 or m == 0:
        return float("inf")

    cost = np.full((n, m), np.inf, dtype=np.float64)

    def eucl(i: int, j: int) -> float:
        d = a[i] - b[j]
        return float(np.sqrt(np.dot(d, d)))

    cost[0, 0] = eucl(0, 0)
    for i in range(1, n):
        cost[i, 0] = cost[i - 1, 0] + eucl(i, 0)
    for j in range(1, m):
        cost[0, j] = cost[0, j - 1] + eucl(0, j)

    for i in range(1, n):
        for j in range(1, m):
            cost[i, j] = eucl(i, j) + min(
                cost[i - 1, j],
                cost[i, j - 1],
                cost[i - 1, j - 1],
            )

    return float(cost[n - 1, m - 1]) / (n + m)


def compute_threshold(
    samples: list[np.ndarray],
) -> tuple[np.ndarray, float]:
    k = len(samples)
    assert k >= 2, "Need at least 2 training samples"

    avg_dists = []
    for i in range(k):
        total = sum(dtw_distance(samples[i], samples[j]) for j in range(k) if j != i)
        avg_dists.append(total / (k - 1))

    best_idx  = int(np.argmin(avg_dists))
    template  = samples[best_idx]

    dists     = np.array([dtw_distance(template, s) for s in samples])
    threshold = float(dists.mean() + 1.5 * dists.std())

    return template, threshold
