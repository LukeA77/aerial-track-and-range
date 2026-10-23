"""Build the demo video (build.md 11.3, D3): six scenes, H.264 MP4 within the release limits.

Usage: python scripts/make_video.py [--out cache/video/demo.mp4]

Scenes (storyboard 11.3): 1 title and claim; 2 VisDrone tracking, pretrained against
fine-tuned, on a validation sequence; 3 AU-AIR ranging overlay on a held-out oblique clip
(D-617), then the parked-vehicle repeatability chart; 4 Mid-Air estimated against true range with
the reliability flag; 5 the speed / accuracy chart against the 30 fps budget; 6 limits and
credits. Every number shown comes from results/headline.json or is computed here from saved
outputs, and is written to results/video/demo_video.json with its source (R1).

Inputs (all produced earlier by code in this repository):
- saved validation tracks, cache/visdrone/runs/{B0_yolo26n_640_botsort_cmc,B2_yolo26n_960_tuned}
- AU-AIR held-out clip 20 run with the accurate setting: scripts/auair_export_flight.py --clip 20,
  then pipeline.run on its first 158 frames with the 960 ONNX detector and detection on every
  frame (cache/runs/auair_clip20_acc); an oblique clip, not straight down (D-617)
- Mid-Air development flight frames and cache/midair/trajectory_0026{,.terrain}.npz, scored
  with the frozen terrain calibration and flag (results/midair/terrain_calibration_fit.json)
The video holds dataset imagery, so it is written to cache/ (not committed, D-323).
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from datetime import UTC, datetime

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from aerialrange.data.midair import WATER_CLASS  # noqa: E402
from aerialrange.evaluate.conformal import apply_conformal  # noqa: E402
from aerialrange.evaluate.flag import FlagModel  # noqa: E402
from aerialrange.pipeline.overlay import STATUS, draw_rings  # noqa: E402
from aerialrange.pipeline.ranging import CameraPose  # noqa: E402
from aerialrange.track.evaluate import accumulate, read_ignored, read_rows, summarise  # noqa: E402
from aerialrange.utils.config import REPO_ROOT, load_config  # noqa: E402
from aerialrange.viz import plots  # noqa: E402
from aerialrange.viz import video as v  # noqa: E402

sys.path.insert(0, str(REPO_ROOT / "scripts"))
from terrain_analyse import FIT, dep_band, flag_features, methods  # noqa: E402

VIS_SEQ = "uav0000305_00000_v"
VIS_RUNS = {
    "B0_yolo26n_640_botsort_cmc": "Pretrained detector (COCO), BoT-SORT",
    "B2_yolo26n_960_tuned": "Fine-tuned on VisDrone, tuned BoT-SORT",
}
AUAIR_CLIP, AUAIR_RUN = 20, "cache/runs/auair_clip20_acc"
AUAIR_FRAMES = (94, 158)  # 1-based, inclusive: 13 s, a tilt estimate on every frame (D-617)
MIDAIR_TRAJ = "trajectory_0026"
MIDAIR_KEYFRAMES, MIDAIR_POINTS = 32, 40
HEADER, GAP = 64, 16
# Track identity colours for scene 2 (categorical slots of the reference palette, fixed order;
# every box also carries its id as text, so colour never stands alone).
ID_COLOURS = [
    v.hex_bgr(h)
    for h in ("#2a78d6", "#eb6834", "#1baf7a", "#9b59d0", "#e0447c", "#3fb8c4", "#c9a227")
]
GOOD, WARN, CRIT = STATUS["reliable"], STATUS["uncertain"], STATUS["invalid"]
DARK = (24, 24, 24)
WHITE = (250, 250, 250)


def bgr_hex(c: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*c[::-1])


def header(img: np.ndarray, n: int, title: str) -> np.ndarray:
    img[:HEADER] = v.BG
    cv2.line(img, (0, HEADER - 1), (v.W, HEADER - 1), v.hex_bgr(plots.GRID), 1)
    return v.text(
        img,
        [
            (f"{n}", (24, HEADER // 2), 26, v.INK_2, True),
            (title, (60, HEADER // 2), 26, v.INK, True),
        ],
        anchor="lm",
    )


def caption(img: np.ndarray, lines: list[str], y: int, size: int = 19) -> np.ndarray:
    return v.text(
        img, [(s, (24, y + i * (size + 8)), size, v.INK_2, False) for i, s in enumerate(lines)]
    )


# ---------------------------------------------------------------- scene 1 and 6: cards
def title_card(hl: dict) -> np.ndarray:
    img = v.blank()
    m, e = hl["midair_test"], hl["edge"]
    claim = (
        f"Median range error {m['terrain_median']:.1%} on synthetic flights with exact ground "
        f"truth, with calibrated error bars, and {e['fast_fps']:.0f} frames per second sustained "
        "on a laptop CPU."
    )
    items = [
        ("Tracking and ranging from a drone camera", (80, 200), 44, v.INK, True),
        ("with honest uncertainty, on a laptop CPU", (80, 268), 36, v.INK_2, False),
    ]
    items += [
        (s, (80, 370 + 34 * i), 24, v.INK, False) for i, s in enumerate(v.wrap(claim, 24, 1100))
    ]
    items.append(("Luke Andrew", (80, 560), 24, v.INK_2, True))
    return v.text(img, items)


def limits_card(hl: dict) -> np.ndarray:
    img = header(v.blank(), 6, "Where it breaks, and credits")
    m, t, a, e = hl["midair_test"], hl["visdrone_test"], hl["auair"], hl["edge"]
    limits = [
        f"Small people: only {t['person_recall_16_32']:.0%} tracked at 16 to 32 pixels tall.",
        f"Range: one estimate in ten is more than {m['terrain_p90']:.0%} off (synthetic test).",
        f"Real footage: {a['vehicle_share_above_70']:.0%} of vehicle speeds are implausible "
        "(over 70 km/h).",
        "Speed: 30 fps in throughput only; each result arrives "
        f"{e['fast_latency_median_ms']:.0f} ms after capture.",
        "No real-sensor or thermal testing; camera model on real footage is inferred.",
    ]
    credits = [
        "VisDrone2019, Zhu et al. (2021): research evaluation only",
        "Mid-Air, Fonder and Van Droogenbroeck (2019): CC BY-NC-SA 4.0",
        "AU-AIR, Bozcan and Kayacan (2020): CC BY 4.0, used non-commercially",
        "Ultralytics YOLO26 and trackers: AGPL-3.0",
        "Code: AGPL-3.0-only. Numbers: results/ in the repository.",
    ]
    items = [("Where it breaks", (48, 100), 28, v.INK, True)]
    y = 150
    for s in limits:
        for j, line in enumerate(v.wrap(s, 22, 560)):
            items.append(((("•  " if j == 0 else "    ") + line), (48, y), 22, v.INK, False))
            y += 31
        y += 12
    items.append(("Credits", (680, 100), 28, v.INK, True))
    y = 150
    for s in credits:
        for line in v.wrap(s, 20, 560):
            items.append((line, (680, y), 20, v.INK_2, False))
            y += 29
        y += 12
    items.append(
        (
            "Every number in this video is computed by code in the repository from its "
            "results files.",
            (48, v.H - 48),
            18,
            v.INK_2,
            False,
        )
    )
    return v.text(img, items)


# ---------------------------------------------------------------- scene 2: VisDrone
def vis_rows(run: str) -> dict[int, list]:
    base = REPO_ROOT / "cache/visdrone/runs" / run / "val"
    out: dict[int, list] = {}
    for g in ("person", "vehicle"):
        rows = np.loadtxt(base / f"{VIS_SEQ}_{g}.txt", delimiter=",").reshape(-1, 7)
        for f, i, x, y, w, h, _ in rows:
            out.setdefault(int(f), []).append((int(i), x, y, w, h))
    return out


def vis_idf1(run: str) -> dict[str, float]:
    prep = REPO_ROOT / "cache/visdrone/mot/val" / VIS_SEQ
    res = {}
    for g in ("person", "vehicle"):
        rows = np.loadtxt(
            REPO_ROOT / "cache/visdrone/runs" / run / "val" / f"{VIS_SEQ}_{g}.txt", delimiter=","
        ).reshape(-1, 7)
        acc = accumulate(
            read_rows(prep / f"gt_{g}.txt", 6), rows, read_ignored(prep / "ignored.txt"), 0.5
        )
        res[g] = float(summarise({VIS_SEQ: acc})[VIS_SEQ]["idf1"])
    return res


def draw_ids(pane: np.ndarray, rows: list, s: float, ox: float, oy: float) -> None:
    for i, x, y, w, h in rows:
        c = ID_COLOURS[i % len(ID_COLOURS)]
        x1, y1 = int((x - ox) * s), int((y - oy) * s)
        x2, y2 = int((x + w - ox) * s), int((y + h - oy) * s)
        if x2 < 0 or y2 < 0 or x1 > pane.shape[1] or y1 > pane.shape[0]:
            continue
        cv2.rectangle(pane, (x1, y1), (x2, y2), c, 2, cv2.LINE_AA)
        lab = f"{i}"
        (tw, th), _ = cv2.getTextSize(lab, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
        cv2.rectangle(pane, (x1, y1 - th - 5), (x1 + tw + 4, y1), DARK, -1)
        cv2.putText(
            pane, lab, (x1 + 2, y1 - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.42, WHITE, 1, cv2.LINE_AA
        )


def scene_visdrone(wr: v.Writer, hl: dict, rec: dict) -> None:
    info = json.loads((REPO_ROOT / "cache/visdrone/mot/val" / VIS_SEQ / "seqinfo.json").read_text())
    frames = sorted((REPO_ROOT / info["frame_dir"]).glob("*.jpg"))
    runs = {r: vis_rows(r) for r in VIS_RUNS}
    idf1 = {r: vis_idf1(r) for r in VIS_RUNS}
    rec["visdrone"] = {"sequence": VIS_SEQ, "split": "val", "idf1_this_sequence": idf1}
    pw = (v.W - 3 * GAP) // 2
    ph = round(pw * info["height"] / info["width"])
    py = HEADER + 48
    val = hl["visdrone_val"]
    base = header(v.blank(), 2, "Detect and track: pretrained against fine-tuned (VisDrone)")
    for k, (r, name) in enumerate(VIS_RUNS.items()):
        x = GAP + k * (pw + GAP)
        i = idf1[r]
        v.text(
            base,
            [
                (name, (x, HEADER + 16), 20, v.INK, True),
                (
                    f"IDF1 on this clip: vehicles {i['vehicle']:.2f}, people {i['person']:.2f}",
                    (x, py + ph + 14),
                    19,
                    v.INK,
                    False,
                ),
            ],
        )
    caption(
        base,
        [
            "Same validation clip, same tracker family; numbers are identity F1 "
            "(IDF1, higher is better).",
            f"All 7 validation clips, mean IDF1: {val['b0_cmc_mean_idf1']:.2f} pretrained, "
            f"{val['b2_960_tuned']:.2f} fine-tuned and tuned.",
        ],
        py + ph + 64,
    )
    v.text(base, [("VisDrone2019 (Zhu et al. 2021)", (24, v.H - 22), 14, v.INK_2, False)])
    zoom_note = None
    for zoom in (1.0, 2.0):
        cw, ch = info["width"] / zoom, info["height"] / zoom
        ox, oy = (info["width"] - cw) / 2, (info["height"] - ch) / 2
        s = pw / cw
        for f, path in enumerate(frames, start=1):
            img = base.copy()
            src = cv2.imread(str(path))
            crop = src[int(oy) : int(oy + ch), int(ox) : int(ox + cw)]
            for k, r in enumerate(VIS_RUNS):
                pane = cv2.resize(crop, (pw, ph), interpolation=cv2.INTER_AREA)
                draw_ids(pane, runs[r].get(f, []), s, ox, oy)
                v.paste(img, pane, GAP + k * (pw + GAP), py)
            if zoom > 1:
                zoom_note = zoom_note or "Zoomed 2x on the centre"
                v.text(img, [(zoom_note, (v.W - 24, HEADER // 2), 18, v.INK_2, False)], anchor="rm")
            if f == 1:
                wr.crossfade(img)
            wr.write(img)


# ---------------------------------------------------------------- scene 3: AU-AIR
def auair_chart(hl: dict, rec: dict) -> np.ndarray:
    d = json.loads(
        (REPO_ROOT / "results/auair/repeatability_view_held_out_B2_yolo26n_960.json").read_text()
    )["results"]["by_depression_all_bottom_relative"]
    bands = [b for b in d if d[b].get("n", 0) > 0]
    med = [100 * d[b]["median_m"] for b in bands]
    lo = [100 * (d[b]["median_m"] - d[b]["ci95"][0]) for b in bands]
    hi = [100 * (d[b]["ci95"][1] - d[b]["median_m"]) for b in bands]
    rec["auair_repeatability_by_depression"] = {b: d[b] for b in bands}
    fig, ax = plt.subplots(figsize=(12.8, (v.H - HEADER - 120) / 100), dpi=100)
    fig.patch.set_facecolor(plots.SURFACE)
    ax.set_facecolor(plots.SURFACE)
    xs = np.arange(len(bands))
    ax.bar(xs, med, width=0.5, color=plots.SERIES[0], zorder=2)
    ax.errorbar(
        xs, med, yerr=[lo, hi], fmt="none", ecolor=plots.TEXT, elinewidth=1.5, capsize=6, zorder=3
    )
    for x, m, b, top in zip(xs, med, bands, hi, strict=True):
        ax.text(
            x,
            m + top + 0.5,
            f"{m:.1f} %  ({d[b]['n']} vehicles)",
            ha="center",
            va="bottom",
            fontsize=13,
            color=plots.TEXT,
        )
    ax.set_xticks(xs, [f"{b.replace('-', ' to ')} deg" for b in bands], fontsize=14)
    ax.set_xlabel("Line of sight below the horizon", fontsize=15, color=plots.TEXT_2)
    ax.set_ylabel("Spread of position, % of range", fontsize=15, color=plots.TEXT_2)
    ax.tick_params(colors=plots.TEXT_2, labelsize=13)
    ax.grid(axis="y", color=plots.GRID, zorder=0)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color(plots.GRID)
    ax.set_xlim(-0.6, len(bands) - 0.4)
    ax.set_ylim(0, max(m + h for m, h in zip(med, hi, strict=True)) * 1.12)
    fig.tight_layout()
    chart = v.figure_array(fig)
    img = header(v.blank(), 3, "Real footage: how far parked vehicles' positions wander (AU-AIR)")
    v.paste(img, chart[: v.H - HEADER - 120], 0, HEADER + 8)
    a = hl["auair"]
    return caption(
        img,
        [
            f"Held-out flights, {a['heldout_segments']} parked-vehicle segments: overall spread "
            f"{a['heldout_rel_all']:.1%} of range (95 % interval {a['heldout_rel_all_ci'][0]:.1%} "
            f"to {a['heldout_rel_all_ci'][1]:.1%}).",
            "There is no ground truth on real footage, so this is repeatability, not accuracy. "
            "Whiskers: 95 % intervals.",
        ],
        v.H - 100,
    )


def scene_auair(wr: v.Writer, hl: dict, rec: dict) -> None:
    cam = load_config("run").require("camera")
    flight = REPO_ROOT / "cache/auair/flights" / f"clip_{AUAIR_CLIP:02d}"
    meta = pd.read_csv(flight / "metadata.csv").set_index("frame")
    tracks = pd.read_csv(REPO_ROOT / AUAIR_RUN / "tracks.csv")
    by_frame = {f: g for f, g in tracks.groupby("frame")}
    frames = sorted((flight / "frames").iterdir())
    f0, f1 = AUAIR_FRAMES
    shown = tracks[tracks["frame"].between(f0, f1)]
    hs = meta.loc[f0:f1, "h_m"]
    rec["auair_clip"] = {
        "clip": AUAIR_CLIP,
        "frames": [f0, f1],
        "run": AUAIR_RUN,
        "rows_shown": len(shown),
        "tracks_shown": int(shown["track_id"].nunique()),
        "flags_shown": shown["flag"].value_counts().to_dict(),
        "height_m": [round(float(hs.min()), 1), round(float(hs.max()), 1)],
        "setting": "B2 YOLO26n ONNX 960, tuned BoT-SORT, detection every frame",
    }
    area_h = v.H - HEADER - 96
    base = header(v.blank(), 3, "Range with an error bar on real footage (AU-AIR, held-out flight)")
    caption(
        base,
        [
            f"Oblique camera, {hs.min():.0f} to {hs.max():.0f} m up. "
            "Label: range ± one standard deviation, "
            "from how much parked vehicles' positions repeat",
            "on calibration flights; it grows with distance. "
            "Green: reliable (σ under 10 % of range); "
            "amber: uncertain. Real time, 5 frames per second.",
        ],
        v.H - 84,
        17,
    )
    for k in range(f0, f1 + 1):
        src = cv2.imread(str(frames[k - 1]))
        m = meta.loc[k]
        pose = CameraPose(*(float(m[c]) for c in ("n_m", "e_m", "h_m", "yaw_rad", "tilt_deg")))
        draw_rings(
            src, pose, float(cam["focal_px"]), float(cam["cx"]), float(cam["cy"]), [10, 25, 50]
        )
        pic, s = v.fit(src, v.W - 2 * GAP, area_h)
        x0 = (v.W - pic.shape[1]) // 2
        labels, placed = [], []
        g = by_frame.get(k)
        if g is not None:
            # largest (nearest) boxes first; a label that would overlap one already placed is
            # dropped (the box stays), so distant clusters do not become unreadable
            for _, r in g.sort_values("height", ascending=False).iterrows():
                col = STATUS[r["flag"]]
                x1, y1 = int(r["left"] * s), int(r["top"] * s)
                x2, y2 = int((r["left"] + r["width"]) * s), int((r["top"] + r["height"]) * s)
                cv2.rectangle(pic, (x1, y1), (x2, y2), col, 3, cv2.LINE_AA)
                lab = (
                    f"{r['range_m']:.0f} ± {r['range_sigma_m']:.0f} m"
                    if r["flag"] != "invalid"
                    else f"no range ({str(r['reason']).replace('_', ' ')})"
                )
                lx, ly = x0 + x1, HEADER + 8 + max(22, y1 - 6)
                w_ = v.font(18, True).getlength(lab) + 8
                rect = (lx - 4, ly - 24, lx + w_, ly + 2)
                if any(
                    not (rect[2] < q[0] or q[2] < rect[0] or rect[3] < q[1] or q[3] < rect[1])
                    for q in placed
                ):
                    continue
                placed.append(rect)
                labels.append((lab, (lx, ly), 18, WHITE, True))
        img = base.copy()
        v.paste(img, pic, x0, HEADER + 8)
        v.text(img, labels, box=DARK, anchor="ld")
        legend = [("reliable", GOOD), ("uncertain", WARN), ("no range", CRIT)]
        for j, (_, col) in enumerate(legend):
            y = HEADER + 30 + 28 * j
            cv2.rectangle(img, (x0 + 14, y - 9), (x0 + 30, y + 7), col, -1)
        v.text(
            img,
            [
                (n, (x0 + 38, HEADER + 30 + 28 * j), 17, WHITE, False)
                for j, (n, _) in enumerate(legend)
            ],
            box=DARK,
            anchor="lm",
        )
        t = float(m["t_s"])
        v.text(
            img,
            [(f"t {t:4.1f} s", (x0 + pic.shape[1] - 14, HEADER + 30), 17, WHITE, False)],
            box=DARK,
            anchor="rm",
        )
        v.text(
            img,
            [
                (
                    "AU-AIR (Bozcan and Kayacan 2020), CC BY 4.0",
                    (x0 + 14, HEADER + 8 + pic.shape[0] - 14),
                    13,
                    WHITE,
                    False,
                )
            ],
            box=DARK,
            anchor="ld",
        )
        if k == f0:
            wr.crossfade(img)
        wr.write(img, round(v.FPS / 5))  # 5 fps source, real time
    chart = auair_chart(hl, rec)
    wr.crossfade(chart)
    wr.hold(chart, 6.5)


# ---------------------------------------------------------------- scene 4: Mid-Air
def midair_scores() -> dict[str, np.ndarray]:
    """Terrain-from-motion estimates of one development flight with the frozen calibration
    and flag (fitted on the calibration flights; the same code path as terrain_analyse)."""
    fit = json.loads(FIT.read_text())
    model = fit["conformal"]
    model["global"] = {float(k): float(x) for k, x in model["global"].items()}
    model["groups"] = {
        int(k): {(float(kk) if kk != "n" else kk): vv for kk, vv in g.items()}
        for k, g in model["groups"].items()
    }
    flag = FlagModel.from_dict(fit["flag_model"])
    cache = REPO_ROOT / "cache/midair"
    r = dict(np.load(cache / f"{MIDAIR_TRAJ}.npz"))
    r.update(np.load(cache / f"{MIDAIR_TRAJ}.terrain.npz"))
    m = methods(r)["terrain_motion"]
    ok = (r["cls"] != WATER_CLASS) & m["valid"] & np.isfinite(m["sigma"]) & (m["sigma"] > 0)
    s68 = np.full(len(ok), np.nan)
    s68[ok] = apply_conformal(m["sigma"][ok], model, 0.68, groups=dep_band(r)[ok])
    X = flag_features(r, s68)
    fin = ok & np.all(np.isfinite(X), axis=1)
    score = np.full(len(ok), np.nan)
    score[fin] = flag.score(X[fin])
    return {
        "frame": r["frame"],
        "u": r["u"],
        "v": r["v"],
        "ok": fin,
        "true": r["true_range_m"],
        "est": m["range"],
        "bad": np.abs(m["rel"]) > fit["err_threshold_frac"],
        "flag": score >= fit["flag_threshold"]["threshold"],
        "thr": fit["err_threshold_frac"],
    }


def midair_chart(
    d: dict, shown: np.ndarray, current: np.ndarray, w: int, h: int, lim: tuple
) -> np.ndarray:
    fig, ax = plt.subplots(figsize=(w / 100, h / 100), dpi=100)
    fig.patch.set_facecolor(plots.SURFACE)
    ax.set_facecolor(plots.SURFACE)
    x = np.geomspace(*lim, 50)
    ax.fill_between(x, x * (1 - d["thr"]), x * (1 + d["thr"]), color=plots.GRID, zorder=0, lw=0)
    ax.plot(x, x, color=plots.TEXT_2, lw=1, zorder=1)
    for sel, size, alpha in ((shown & ~current, 22, 0.45), (current, 46, 1.0)):
        for flagged, col in ((False, GOOD), (True, WARN)):
            for bad, marker in ((False, "o"), (True, "X")):
                j = sel & (d["flag"] == flagged) & (d["bad"] == bad)
                ax.scatter(
                    d["true"][j],
                    d["est"][j],
                    s=size,
                    marker=marker,
                    color=bgr_hex(col),
                    alpha=alpha,
                    edgecolor=plots.SURFACE,
                    linewidth=0.6,
                    zorder=3 if bad else 2,
                )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(*lim)
    ax.set_ylim(*lim)
    ax.set_xlabel("True range (m)", fontsize=14, color=plots.TEXT_2)
    ax.set_ylabel("Estimated range (m)", fontsize=14, color=plots.TEXT_2)
    ax.tick_params(colors=plots.TEXT_2, labelsize=12)
    ax.grid(color=plots.GRID, lw=0.8, zorder=0)
    for sp in ax.spines.values():
        sp.set_color(plots.GRID)
    nb = int((shown & d["bad"]).sum())
    nf = int((shown & d["bad"] & d["flag"]).sum())
    ax.set_title(
        f"{int(shown.sum())} estimates shown, {nb} more than 10 % off;\n"
        f"the flag is raised on {nf} of those {nb}",
        fontsize=14,
        color=plots.TEXT,
        loc="left",
    )
    ax.text(
        lim[1] / 1.15,
        lim[0] * 1.3,
        "line: perfect; grey band: within 10 %",
        ha="right",
        fontsize=12,
        color=plots.TEXT_2,
    )
    fig.tight_layout()
    return v.figure_array(fig)


def scene_midair(wr: v.Writer, hl: dict, rec: dict) -> None:
    data = load_config("data")
    root = REPO_ROOT / data.require("data_root") / data.require("midair_subdir")
    frames_dir = root / data.require("midair_climate") / "color_left" / MIDAIR_TRAJ
    d = midair_scores()
    keys = np.unique(d["frame"])
    start = (len(keys) - MIDAIR_KEYFRAMES) // 2
    keys = keys[start : start + MIDAIR_KEYFRAMES]
    rng = np.random.default_rng(load_config("project").require("seed"))
    pick = np.zeros(len(d["ok"]), bool)
    for f in keys:
        j = np.flatnonzero(d["ok"] & (d["frame"] == f))
        pick[rng.choice(j, min(MIDAIR_POINTS, len(j)), replace=False)] = True
    lim = (
        float(min(d["true"][pick].min(), d["est"][pick].min()) * 0.8),
        float(max(d["true"][pick].max(), d["est"][pick].max()) * 1.25),
    )
    allok = d["ok"]
    whole = {
        "estimates": int(allok.sum()),
        "bad_share": float((d["bad"] & allok).sum() / allok.sum()),
        "flag_recall": float(
            (d["bad"] & d["flag"] & allok).sum() / max((d["bad"] & allok).sum(), 1)
        ),
        "flag_precision": float(
            (d["bad"] & d["flag"] & allok).sum() / max((d["flag"] & allok).sum(), 1)
        ),
    }
    rec["midair"] = {
        "trajectory": MIDAIR_TRAJ,
        "split": "development (flag and calibration fitted on the calibration flights)",
        "keyframes": [int(k) for k in keys],
        "points_per_keyframe": MIDAIR_POINTS,
        "whole_flight": whole,
    }
    side = v.H - HEADER - 2 * GAP - 70
    cw = v.W - side - 3 * GAP
    base = header(v.blank(), 4, "Estimated against true range, with a reliability flag (Mid-Air)")
    m = hl["midair_test"]
    caption(
        base,
        [
            "Synthetic flight, exact truth; flag and error bars fitted on other flights. "
            "On the 9 test flights the "
            f"flag catches {m['flag_recall']:.0%}",
            f"of estimates more than 10 % off (AUROC {m['flag_auroc']:.2f}), "
            f"and {m['flag_precision']:.0%} of what it "
            "flags is that far off. Shown at 2x speed, one frame per second of flight.",
        ],
        v.H - 66,
        17,
    )
    leg = [("o  flag quiet", GOOD), ("o  flag raised", WARN)]
    shown = np.zeros(len(pick), bool)
    for n, f in enumerate(keys):
        cur = pick & (d["frame"] == f)
        shown |= cur
        src = cv2.imread(str(frames_dir / f"{int(f):06d}.JPEG"))
        pic, s = v.fit(src, side, side)
        for j in np.flatnonzero(cur):
            col = WARN if d["flag"][j] else GOOD
            c = (int(d["u"][j] * s), int(d["v"][j] * s))
            if d["bad"][j]:
                cv2.line(pic, (c[0] - 7, c[1] - 7), (c[0] + 7, c[1] + 7), DARK, 6, cv2.LINE_AA)
                cv2.line(pic, (c[0] - 7, c[1] + 7), (c[0] + 7, c[1] - 7), DARK, 6, cv2.LINE_AA)
                cv2.line(pic, (c[0] - 7, c[1] - 7), (c[0] + 7, c[1] + 7), col, 3, cv2.LINE_AA)
                cv2.line(pic, (c[0] - 7, c[1] + 7), (c[0] + 7, c[1] - 7), col, 3, cv2.LINE_AA)
            else:
                cv2.circle(pic, c, 6, DARK, -1, cv2.LINE_AA)
                cv2.circle(pic, c, 4, col, -1, cv2.LINE_AA)
        img = base.copy()
        v.paste(img, pic, GAP, HEADER + GAP)
        chart = midair_chart(d, shown, cur, cw, side, lim)
        v.paste(img, chart, 2 * GAP + side, HEADER + GAP)
        items = [
            (
                "circle: within 10 % of truth    cross: more than 10 % off",
                (GAP + 10, HEADER + GAP + 22),
                15,
                WHITE,
                False,
            )
        ]
        items += [
            (name[3:], (GAP + 34 + 150 * j, HEADER + GAP + 50), 15, WHITE, False)
            for j, (name, _) in enumerate(leg)
        ]
        v.text(img, items, box=DARK, anchor="lm")
        for j, (_, col) in enumerate(leg):
            cv2.circle(img, (GAP + 22 + 150 * j, HEADER + GAP + 50), 6, col, -1, cv2.LINE_AA)
        v.text(
            img,
            [
                (
                    "Mid-Air (Fonder and Van Droogenbroeck 2019), CC BY-NC-SA 4.0",
                    (GAP + 10, HEADER + GAP + side - 14),
                    13,
                    WHITE,
                    False,
                )
            ],
            box=DARK,
            anchor="ld",
        )
        if n == 0:
            wr.crossfade(img)
        wr.hold(img, 0.5)
    wr.hold(img, 3.5)


# ---------------------------------------------------------------- scene 5: speed
def scene_speed(wr: v.Writer, hl: dict, rec: dict) -> None:
    p = json.loads((REPO_ROOT / "results/edge/pareto.json").read_text())
    cfg = {c["config"]: c for c in p["configs"]}
    xs = np.array([c["ms_per_frame_sustained"] for c in p["configs"]])
    ys = np.array([c["mean_idf1"] for c in p["configs"]])
    front = [cfg[k] for k in p["frontier"]]
    e = hl["edge"]
    rec["speed"] = {"configs": len(xs), "frontier": p["frontier"], "budget_ms": p["budget_ms"]}
    h = v.H - HEADER - 100

    def chart(annotate: bool) -> np.ndarray:
        fig, ax = plt.subplots(figsize=(12.8, h / 100), dpi=100)
        fig.patch.set_facecolor(plots.SURFACE)
        ax.set_facecolor(plots.SURFACE)
        ax.scatter(
            xs,
            ys,
            s=60,
            color=plots.MUTED,
            edgecolor=plots.SURFACE,
            zorder=2,
            label="Other settings",
        )
        fx = [c["ms_per_frame_sustained"] for c in front]
        fy = [c["mean_idf1"] for c in front]
        ax.plot(
            fx,
            fy,
            "-o",
            color=plots.SERIES[0],
            lw=2,
            ms=8,
            mec=plots.SURFACE,
            zorder=3,
            label="Best trade-offs",
        )
        for ms, name in ((p["budget_ms"], "30 fps budget"), (p["reference_ms"], "10 fps")):
            ax.axvline(ms, color=plots.TEXT_2, ls="--", lw=1.2, zorder=1)
            ax.text(ms * 1.03, 0.623, name, fontsize=13, color=plots.TEXT_2, va="bottom")
        if annotate:
            for x, y, s, fx_, dy in (
                (
                    1000 / e["accurate_fps"],
                    e["accurate_idf1"],
                    f"Accurate: {e['accurate_fps']:.1f} fps, IDF1 {e['accurate_idf1']:.2f}\n"
                    "(960 input, every frame)",
                    1.9,
                    -0.025,
                ),
                (
                    1000 / e["fast_fps"],
                    e["fast_idf1"],
                    f"Fast: {e['fast_fps']:.1f} fps, IDF1 {e['fast_idf1']:.2f}\n"
                    "(640 input, detect every 2nd frame,\ndetection overlapped with tracking)",
                    1.75,
                    -0.022,
                ),
            ):
                ax.annotate(
                    s,
                    (x, y),
                    (x * fx_, y + dy),
                    fontsize=14,
                    color=plots.TEXT,
                    va="top",
                    arrowprops={"arrowstyle": "-", "color": plots.TEXT_2, "lw": 1.2},
                )
        ax.set_xscale("log")
        ax.set_xticks([20, 33, 50, 100, 200, 500], ["20", "33", "50", "100", "200", "500"])
        ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        ax.set_ylim(top=0.635)
        ax.set_xlabel("Time per frame, sustained (ms, log scale)", fontsize=15, color=plots.TEXT_2)
        ax.set_ylabel("Mean IDF1, VisDrone validation", fontsize=15, color=plots.TEXT_2)
        ax.tick_params(colors=plots.TEXT_2, labelsize=13)
        ax.grid(color=plots.GRID, zorder=0)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        for sp in ("left", "bottom"):
            ax.spines[sp].set_color(plots.GRID)
        ax.legend(loc="lower right", frameon=False, fontsize=13, labelcolor=plots.TEXT_2)
        fig.tight_layout()
        img = header(
            v.blank(), 5, f"Speed against accuracy on a laptop CPU ({e['cpu'].split(' with')[0]})"
        )
        v.paste(img, v.figure_array(fig)[:h], 0, HEADER + 8)
        return caption(
            img,
            [
                f"{len(xs)} settings measured. "
                f"30 fps is reached in throughput ({e['fast_fps']:.1f} fps), "
                f"but each frame's result arrives {e['fast_latency_median_ms']:.0f} ms",
                "after capture (median; "
                f"{e['fast_latency_p99_ms']:.0f} ms at the 99th percentile), "
                "above the 33 ms budget. Accuracy falls as speed rises.",
            ],
            v.H - 80,
            18,
        )

    a = chart(False)
    wr.crossfade(a)
    wr.hold(a, 3.5)
    b = chart(True)
    wr.crossfade(b)
    wr.hold(b, 5.5)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="cache/video/demo.mp4")
    args = ap.parse_args(argv)
    # the pretrained run found no people on the scene-2 clip: its track file is empty
    warnings.filterwarnings("ignore", message=".*input contained no data.*")
    rel = load_config("release")
    max_mb, max_s = float(rel.require("max_video_mb")), float(rel.require("video_length_s"))
    hl = json.loads((REPO_ROOT / "results/headline.json").read_text())
    out = REPO_ROOT / args.out
    master = out.with_name(out.stem + "_master.mp4")
    wr = v.Writer(master)
    rec: dict = {}
    scenes = []

    def mark(name: str) -> None:
        scenes.append({"scene": name, "end_s": round(wr.seconds, 2)})
        print(f"{name}: ends at {wr.seconds:.1f} s", flush=True)

    t = title_card(hl)
    wr.write(t)
    wr.hold(t, 5)
    mark("1 title")
    scene_visdrone(wr, hl, rec)
    mark("2 VisDrone tracking")
    scene_auair(wr, hl, rec)
    mark("3 AU-AIR ranging and repeatability")
    scene_midair(wr, hl, rec)
    mark("4 Mid-Air flag")
    scene_speed(wr, hl, rec)
    mark("5 speed")
    c = limits_card(hl)
    wr.crossfade(c)
    wr.hold(c, 9.5)
    mark("6 limits and credits")
    wr.close()
    seconds = wr.seconds
    if seconds > max_s:
        print(f"video is {seconds:.1f} s, over the {max_s:.0f} s limit")
        return 1
    kbps = v.encode_to_size(master, out, max_mb, seconds)
    size_mb = out.stat().st_size / 1e6
    record = {
        "generated_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "file": args.out,
        "seconds": round(seconds, 2),
        "size_mb": round(size_mb, 2),
        "limits": {
            "max_video_mb": max_mb,
            "video_length_s": max_s,
            "source": "configs/release.yaml (D-615)",
        },
        "within_limits": bool(size_mb <= max_mb and seconds <= max_s),
        "encoding": {
            "codec": "H.264 (libx264, two-pass)",
            "kbps": kbps,
            "size": f"{v.W}x{v.H}",
            "fps": v.FPS,
        },
        "scenes": scenes,
        "numbers_from": "results/headline.json plus the values below, computed by this script",
        "computed": rec,
    }
    dest = REPO_ROOT / "results/video/demo_video.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(record, indent=1, default=float) + "\n")
    print(json.dumps({k: record[k] for k in ("seconds", "size_mb", "within_limits")}))
    return 0 if record["within_limits"] else 1


if __name__ == "__main__":
    sys.exit(main())
