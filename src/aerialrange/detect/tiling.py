"""Tiled inference for small objects (baseline B3, build.md Section 9.2).

The image is split into overlapping square tiles (`{{TILE_SIZE}}` px, overlap fraction
`{{TILE_OVERLAP}}`, chosen on validation); each tile is detected separately, boxes are mapped
back to full-image coordinates and merged with class-wise non-maximum suppression. The
latency cost is reported with the accuracy (Section 9.2).
"""

from __future__ import annotations

import math
from collections.abc import Callable

import numpy as np
from numpy.typing import NDArray

from aerialrange.track.evaluate import iou_distance

TileDetector = Callable[[NDArray, int, int], tuple[NDArray, NDArray, NDArray]]


def tile_grid(
    width: int, height: int, tile: int, overlap: float
) -> list[tuple[int, int, int, int]]:
    """Tiles (x0, y0, w, h) covering the image; the last tile in each row/column is aligned
    to the image edge so no tile extends past it."""
    if not 0 <= overlap < 1:
        raise ValueError("overlap must be in [0, 1)")

    def starts(n: int) -> list[int]:
        if n <= tile:
            return [0]
        step = tile * (1 - overlap)
        k = math.ceil((n - tile) / step) + 1
        return sorted({min(round(i * step), n - tile) for i in range(k)})

    tw, th = min(tile, width), min(tile, height)
    return [(x, y, tw, th) for y in starts(height) for x in starts(width)]


def nms(boxes_ltwh: NDArray, scores: NDArray, cls: NDArray, iou_thr: float) -> NDArray:
    """Indices kept by greedy class-wise non-maximum suppression."""
    keep = []
    for c in np.unique(cls):
        idx = np.nonzero(cls == c)[0]
        idx = idx[np.argsort(-scores[idx], kind="mergesort")]
        while len(idx):
            i = idx[0]
            keep.append(i)
            if len(idx) == 1:
                break
            d = iou_distance(boxes_ltwh[i : i + 1], boxes_ltwh[idx[1:]], iou_thr)[0]
            idx = idx[1:][np.isnan(d)]  # NaN distance means IoU below threshold: keep
    return np.array(sorted(keep), int)


def detect_tiled(
    img: NDArray, detector: TileDetector, tile: int, overlap: float, nms_iou: float
) -> tuple[NDArray, NDArray, NDArray]:
    """Run `detector(tile_image, x0, y0)` on every tile; returns merged (ltwh, scores, cls)
    in full-image coordinates."""
    h, w = img.shape[:2]
    B, S, C = [], [], []
    for x0, y0, tw, th in tile_grid(w, h, tile, overlap):
        b, s, c = detector(img[y0 : y0 + th, x0 : x0 + tw], x0, y0)
        if len(b):
            b = np.asarray(b, float).copy()
            b[:, 0] += x0
            b[:, 1] += y0
            B.append(b)
            S.append(np.asarray(s, float))
            C.append(np.asarray(c, int))
    if not B:
        return np.zeros((0, 4)), np.zeros(0), np.zeros(0, int)
    b, s, c = np.concatenate(B), np.concatenate(S), np.concatenate(C)
    k = nms(b, s, c, nms_iou)
    return b[k], s[k], c[k]
