import numpy as np
import pytest

from aerialrange.detect.tiling import detect_tiled, nms, tile_grid


def test_tile_grid_covers_image_with_overlap():
    tiles = tile_grid(width=1000, height=600, tile=512, overlap=0.25)
    xs = sorted({t[0] for t in tiles})
    ys = sorted({t[1] for t in tiles})
    assert xs[0] == 0 and xs[-1] + 512 == 1000
    assert ys[0] == 0 and ys[-1] + 512 == 600
    assert all(b - a <= 512 * 0.75 + 1 for a, b in zip(xs, xs[1:], strict=False))


def test_tile_grid_small_image_is_one_tile():
    assert tile_grid(300, 200, 512, 0.2) == [(0, 0, 300, 200)]


def test_tile_grid_validates_overlap():
    with pytest.raises(ValueError):
        tile_grid(1000, 1000, 512, 1.0)


def test_nms_suppresses_same_class_only():
    boxes = np.array([[0, 0, 10, 10], [1, 1, 10, 10], [0, 0, 10, 10]], float)
    scores = np.array([0.9, 0.8, 0.7])
    cls = np.array([0, 0, 1])
    keep = nms(boxes, scores, cls, iou_thr=0.5)
    assert sorted(keep.tolist()) == [0, 2]


def test_detect_tiled_maps_boxes_to_full_image_and_merges_duplicates():
    """Fake detector: finds an object at full-image ltwh (600, 100, 20, 20) in any tile that
    contains it, reporting tile-local coordinates."""
    obj = np.array([600.0, 100.0, 20.0, 20.0])

    def fake(img_tile, x0, y0):
        h, w = img_tile.shape[:2]
        left, top = obj[0] - x0, obj[1] - y0
        if 0 <= left and left + obj[2] <= w and 0 <= top and top + obj[3] <= h:
            return np.array([[left, top, obj[2], obj[3]]]), np.array([0.9]), np.array([3])
        return np.zeros((0, 4)), np.zeros(0), np.zeros(0, int)

    img = np.zeros((600, 1000, 3), np.uint8)
    boxes, scores, cls = detect_tiled(
        img, lambda im, x0, y0: fake(im, x0, y0), tile=512, overlap=0.25, nms_iou=0.5
    )
    assert len(boxes) == 1
    np.testing.assert_allclose(boxes[0], obj)
    assert cls[0] == 3
