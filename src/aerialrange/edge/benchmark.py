"""Per-stage latency benchmark (build.md Section 10.4).

A pipeline is a list of (name, callable) stages; each stage's output is the next stage's
input. Protocol sizes are `{{N_WARMUP}}`, `{{N_TIMED_FRAMES}}`, `{{N_REPEATS}}` from
configs/edge.yaml. Reports median, 95th and 99th percentiles per stage and end to end,
throughput, and peak Python-traced memory. Overlay drawing is not a stage here (excluded from
the budget, Section 10.1).
"""

from __future__ import annotations

import time
import tracemalloc
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from itertools import cycle, islice
from typing import Any

import numpy as np

Stage = tuple[str, Callable[[Any], Any]]


@dataclass(frozen=True)
class BenchmarkProtocol:
    n_warmup: int
    n_timed: int
    n_repeats: int

    def __post_init__(self) -> None:
        if self.n_timed < 1 or self.n_repeats < 1 or self.n_warmup < 0:
            raise ValueError("need n_timed >= 1, n_repeats >= 1, n_warmup >= 0")


def _stats(ms: np.ndarray) -> dict[str, float]:
    return {
        "median_ms": float(np.median(ms)),
        "mean_ms": float(ms.mean()),
        "p95_ms": float(np.percentile(ms, 95)),
        "p99_ms": float(np.percentile(ms, 99)),
        "max_ms": float(ms.max()),
    }


def run_benchmark(
    stages: Sequence[Stage], inputs: Sequence[Any], protocol: BenchmarkProtocol
) -> dict[str, Any]:
    """Time each stage on `inputs` (cycled). Warm-up runs are not recorded."""
    names = [n for n, _ in stages]

    def one(x: Any) -> list[float]:
        t = []
        for _, fn in stages:
            t0 = time.perf_counter()
            x = fn(x)
            t.append((time.perf_counter() - t0) * 1000)
        return t

    for x in islice(cycle(inputs), protocol.n_warmup):
        one(x)
    tracemalloc.start()
    rows = []
    for _ in range(protocol.n_repeats):
        for x in islice(cycle(inputs), protocol.n_timed):
            rows.append(one(x))
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    t = np.array(rows)
    out = {n: _stats(t[:, i]) for i, n in enumerate(names)}
    out["end_to_end"] = _stats(t.sum(axis=1))
    return {
        "stages": out,
        "n_samples": len(rows),
        "throughput_fps": 1000.0 / out["end_to_end"]["mean_ms"],
        "peak_traced_mb": peak / 2**20,
        "protocol": protocol.__dict__,
    }


def budget_verdict(stages: dict[str, dict[str, float]], budget_ms: float | None) -> dict[str, Any]:
    """Whether end-to-end latency meets `{{LATENCY_BUDGET_MS}}` at the median and the 99th
    percentile (Section 10.4). Refuses to judge without a budget."""
    if budget_ms is None:
        raise ValueError("no latency budget: {{TARGET_FPS}} is unresolved")
    e = stages["end_to_end"]
    return {
        "budget_ms": budget_ms,
        "meets_at_median": e["median_ms"] <= budget_ms,
        "meets_at_p99": e["p99_ms"] <= budget_ms,
    }
