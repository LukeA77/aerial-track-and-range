"""Run a detector + tracker over a VisDrone sequence (build.md Sections 9.2 and 9.3).

Uses the detector library's own trackers (ByteTrack, BoT-SORT) through `model.track`.
Appearance re-identification stays off (motion and overlap only, Section 9.3). Each
detector class maps to an evaluation group through `class_to_group`; classes not in the map
are dropped before tracking.
"""

from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np


def run_sequence(
    model: Any,
    frames: Sequence[Path],
    tracker_cfg: str,
    imgsz: int,
    class_to_group: Mapping[int, str],
) -> tuple[dict[str, np.ndarray], dict[str, float]]:
    """Track one sequence. Returns rows per group, (frame, id, left, top, width, height,
    score), with 1-based frame numbers as in VisDrone, and timing totals in seconds."""
    rows: dict[str, list] = {g: [] for g in set(class_to_group.values())}
    classes = sorted(class_to_group)
    t_total = 0.0
    for k, path in enumerate(frames, start=1):
        t0 = time.perf_counter()
        res = model.track(
            source=str(path),
            persist=k > 1,
            tracker=tracker_cfg,
            imgsz=imgsz,
            classes=classes,
            verbose=False,
        )[0]
        t_total += time.perf_counter() - t0
        b = res.boxes
        if b is None or b.id is None or len(b) == 0:
            continue
        xyxy = b.xyxy.cpu().numpy()
        ids = b.id.cpu().numpy().astype(int)
        cls = b.cls.cpu().numpy().astype(int)
        conf = b.conf.cpu().numpy()
        for (x1, y1, x2, y2), i, c, s in zip(xyxy, ids, cls, conf, strict=True):
            g = class_to_group.get(int(c))
            if g is not None:
                rows[g].append((k, i, x1, y1, x2 - x1, y2 - y1, s))
    out = {g: np.array(v, float).reshape(-1, 7) for g, v in rows.items()}
    return out, {"track_seconds": t_total, "frames": len(frames)}
