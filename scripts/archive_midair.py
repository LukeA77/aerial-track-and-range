"""Move Mid-Air trajectories between the laptop and Google Drive, verified file by file.

Usage:
  python scripts/archive_midair.py --to-drive --splits test calibration
  python scripts/archive_midair.py --restore --splits test

--to-drive: for each COMPLETE trajectory of the given splits (all three modality markers
present, no partial downloads), copy every frame of each modality folder to Drive, check size
and SHA-256 of the copy against the original, then delete the local frame. The small
`.frames.done` markers stay on the laptop so the downloader does not fetch the data again; an
`.archived` marker records where the frames went. Pauses while Drive's local upload cache is
growing (backlog above its starting size), so the laptop disk cannot fill up.
--restore: copy archived frames back, verified the same way, and remove the `.archived` marker
(the Drive copy is kept).
Luke authorised writing to the Drive folder on 2026-10-19 (BLOCKED.md, memory).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from aerialrange.utils.config import REPO_ROOT, load_config

DRIVE_ROOT = Path("G:/My Drive/aerial-track-and-range-data/midair")
MODALITIES = ("depth", "segmentation", "normals", "color_left")
REQUIRED = ("depth", "segmentation", "normals")
LOG = REPO_ROOT / "cache" / "midair_archive_log.json"
CHUNK = 1 << 20


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        while b := f.read(CHUNK):
            h.update(b)
    return h.hexdigest()


def drive_cache_gb() -> float:
    root = Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "DriveFS"
    if not root.exists():
        return 0.0
    return sum(f.stat().st_size for f in root.rglob("*") if f.is_file()) / 2**30


def wait_for_drive(baseline_gb: float, max_growth_gb: float, min_free_gb: float) -> None:
    """Pause while Drive's local cache has grown more than `max_growth_gb` above its size when
    this run started (a real upload backlog; Drive also keeps already-uploaded files cached),
    or while the laptop has less than `min_free_gb` free."""
    while True:
        growth = drive_cache_gb() - baseline_gb
        free = shutil.disk_usage(REPO_ROOT).free / 2**30
        if growth <= max_growth_gb and free >= min_free_gb:
            return
        print(
            f"  waiting for Drive upload: backlog {growth:.1f} GB, laptop free {free:.1f} GB",
            flush=True,
        )
        time.sleep(60)


def move_verified(src: Path, dst: Path) -> None:
    """Copy src to dst, verify size and SHA-256, then delete src."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    if dst.stat().st_size != src.stat().st_size or sha256(dst) != sha256(src):
        dst.unlink(missing_ok=True)
        raise RuntimeError(f"verification failed for {src}")
    src.unlink()


def trajectory_complete(local: Path, name: str) -> bool:
    for m in REQUIRED:
        d = local / m / name
        if not (d / ".frames.done").exists() or any(d.glob("*.part")):
            return False
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--to-drive", action="store_true")
    g.add_argument("--restore", action="store_true")
    ap.add_argument(
        "--splits", nargs="+", required=True, choices=["development", "calibration", "test"]
    )
    ap.add_argument("--max-backlog-gb", type=float, default=6.0)
    ap.add_argument("--min-free-gb", type=float, default=8.0)
    args = ap.parse_args(argv)

    data = load_config("data")
    climate = data.require("midair_climate")
    local = REPO_ROOT / data.require("data_root") / data.require("midair_subdir") / climate
    remote = DRIVE_ROOT / climate
    if not DRIVE_ROOT.parent.exists():
        print(f"Drive folder not found: {DRIVE_ROOT.parent}")
        return 1
    splits = json.loads((REPO_ROOT / "results" / "splits.json").read_text())["midair"]["splits"]
    names = [n for s in args.splits for n in splits[s]]
    log = json.loads(LOG.read_text()) if LOG.exists() else []
    baseline = drive_cache_gb()
    print(f"Drive cache at start: {baseline:.1f} GB (already-uploaded files, not a backlog)")

    for name in names:
        present = [m for m in MODALITIES if (local / m / name).is_dir()]
        marked = [m for m in present if (local / m / name / ".archived").exists()]
        archived = bool(marked)  # at least partly on Drive (restore brings back what is there)
        if args.to_drive:
            # Done only when EVERY modality folder is marked; a run interrupted between
            # modalities resumes with the rest instead of skipping the trajectory.
            if present and len(marked) == len(present):
                print(f"{name}: already on Drive")
                continue
            if not trajectory_complete(local, name):
                print(f"{name}: not completely downloaded yet, skipped")
                continue
        elif not archived:
            print(f"{name}: not archived, nothing to restore")
            continue
        n_files = n_bytes = 0
        for m in MODALITIES:
            a, b = (
                (local / m / name, remote / m / name)
                if args.to_drive
                else (remote / m / name, local / m / name)
            )
            if not a.is_dir():
                continue
            if args.to_drive:
                wait_for_drive(baseline, args.max_backlog_gb, args.min_free_gb)
            files = [f for f in sorted(a.iterdir()) if f.is_file() and not f.name.startswith(".")]
            for f in files:
                n_bytes += f.stat().st_size
                if args.to_drive:
                    move_verified(f, b / f.name)
                else:
                    b.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, b / f.name)
                    if (b / f.name).stat().st_size != f.stat().st_size or sha256(
                        b / f.name
                    ) != sha256(f):
                        raise RuntimeError(f"verification failed restoring {f}")
                n_files += 1
            marker = local / m / name / ".archived"
            if args.to_drive:
                marker.write_text(str(b) + "\n")
            else:
                marker.unlink(missing_ok=True)
        action = "to_drive" if args.to_drive else "restored"
        log.append(
            {
                "utc": datetime.now(UTC).isoformat(timespec="seconds"),
                "trajectory": name,
                "action": action,
                "files": n_files,
                "gb": round(n_bytes / 2**30, 3),
            }
        )
        LOG.write_text(json.dumps(log, indent=1) + "\n")
        print(f"{name}: {action}, {n_files} files, {n_bytes / 2**30:.2f} GB verified", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
