import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import archive_midair as am  # noqa: E402


def test_move_verified_copies_then_deletes(tmp_path):
    src = tmp_path / "a" / "x.png"
    src.parent.mkdir()
    src.write_bytes(b"frame-data")
    dst = tmp_path / "b" / "x.png"
    am.move_verified(src, dst)
    assert not src.exists() and dst.read_bytes() == b"frame-data"


def test_move_verified_keeps_source_if_copy_differs(tmp_path, monkeypatch):
    src = tmp_path / "x.png"
    src.write_bytes(b"frame-data")
    dst = tmp_path / "out" / "x.png"
    real = am.sha256
    monkeypatch.setattr(am, "sha256", lambda p: "bad" if p == dst else real(p))
    with pytest.raises(RuntimeError):
        am.move_verified(src, dst)
    assert src.exists() and not dst.exists()


def test_trajectory_complete_needs_all_markers_and_no_partials(tmp_path):
    for m in am.REQUIRED:
        (tmp_path / m / "trajectory_0001").mkdir(parents=True)
        (tmp_path / m / "trajectory_0001" / ".frames.done").write_text("x")
    assert am.trajectory_complete(tmp_path, "trajectory_0001")
    (tmp_path / "depth" / "trajectory_0001" / "frames.zip.part").write_text("x")
    assert not am.trajectory_complete(tmp_path, "trajectory_0001")
    assert not am.trajectory_complete(tmp_path, "trajectory_0002")
