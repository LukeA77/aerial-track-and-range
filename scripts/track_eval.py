"""Run a detector + tracker on VisDrone MOT and score it (build.md Sections 9.2 to 9.4).

Usage: python scripts/track_eval.py --run B0_yolo26n_640_bytetrack --weights weights/yolo26n.pt
       --class-map coco --imgsz 640 --tracker configs/trackers/bytetrack.yaml [--split val]
       [--sequences N]

Predictions go to cache/visdrone/runs/<run>/<split>/; metrics per group to
results/visdrone/<split>/<run>.json. The test-dev split runs once, with --final (R5).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from aerialrange.track.evaluate import accumulate, read_ignored, read_rows, summarise
from aerialrange.track.runner import run_sequence
from aerialrange.utils.config import REPO_ROOT, load_config

PREP = REPO_ROOT / "cache" / "visdrone" / "mot"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--weights", required=True)
    ap.add_argument("--class-map", required=True)
    ap.add_argument("--imgsz", type=int, required=True)
    ap.add_argument("--tracker", required=True)
    ap.add_argument("--split", default="val", choices=["val", "test-dev"])
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--sequences", type=int, default=None, help="limit (smoke tests only)")
    args = ap.parse_args(argv)
    if args.split == "test-dev" and not args.final:
        print("test-dev runs once, after all settings are frozen (R5). Use --final.")
        return 1
    from ultralytics import YOLO

    det = load_config("detector")
    iou = det.require("iou_match")
    cmap = {int(k): v for k, v in det.require("class_maps")[args.class_map].items()}
    groups = sorted(set(cmap.values()))
    model = YOLO(args.weights)
    seqs = sorted(p for p in (PREP / args.split).iterdir() if p.is_dir())[: args.sequences]
    pred_dir = REPO_ROOT / "cache" / "visdrone" / "runs" / args.run / args.split
    pred_dir.mkdir(parents=True, exist_ok=True)
    accs = {g: {} for g in groups}
    timing = {"track_seconds": 0.0, "frames": 0}
    for seq in seqs:
        info = json.loads((seq / "seqinfo.json").read_text())
        frames = sorted((REPO_ROOT / info["frame_dir"]).glob("*.jpg"))
        rows, t = run_sequence(model, frames, str(REPO_ROOT / args.tracker), args.imgsz, cmap)
        timing = {k: timing[k] + t[k] for k in timing}
        ign = read_ignored(seq / "ignored.txt")
        for g in groups:
            np.savetxt(pred_dir / f"{seq.name}_{g}.txt", rows[g], fmt="%.2f", delimiter=",")
            accs[g][seq.name] = accumulate(read_rows(seq / f"gt_{g}.txt", 6), rows[g], ign, iou)
        print(f"{seq.name}: {len(frames)} frames, {t['track_seconds']:.0f} s", flush=True)
    metrics = {g: summarise(accs[g]) for g in groups}
    try:
        commit = (
            subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            ).stdout.strip()
            or None
        )
    except OSError:
        commit = None
    import ultralytics

    out = {
        "generated_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "git_commit": commit,
        "run": args.run,
        "split": args.split,
        "weights": Path(args.weights).name,
        "imgsz": args.imgsz,
        "tracker": Path(args.tracker).name,
        "class_map": args.class_map,
        "iou_match": iou,
        "ultralytics": ultralytics.__version__,
        "sequences": [s.name for s in seqs],
        "timing_note": "Wall time of detector+tracker calls; not a latency benchmark "
        "(Section 10.4 protocol not applied).",
        "timing": timing,
        "metrics": metrics,
    }
    dest = REPO_ROOT / "results" / "visdrone" / args.split / f"{args.run}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=1) + "\n")
    for g in groups:
        o = metrics[g]["OVERALL"]
        print(f"{g}: MOTA {o['mota']:.3f} IDF1 {o['idf1']:.3f} IDSW {o['num_switches']:.0f}")
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
