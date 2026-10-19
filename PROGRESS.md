# Progress log

## 2026-10-18: Phase 0 (bootstrap)

**Built:** repository layout as in build.md Section 5; `pyproject.toml` (package `aerialrange`, extras `dev`, `train`, `edge`); `requirements-lock.txt`; Makefile; CI workflow; `.gitignore`; configs with `null` placeholders and a loader (`aerialrange.utils.config`); `scripts/env_report.py`; `scripts/check_data.py` (logic in `aerialrange.data.check`); a CLI stub (`aerialrange data-check`, `aerialrange env`); AGPL-3.0 `LICENSE`.

**Checks run** (the Makefile's `lint` and `test` commands, run directly because `make` is not installed, BLOCKED.md item 12):
- `ruff check` and `ruff format --check`: clean.
- `pytest`: 33 passed (config loader, and data checks on synthetic fixtures).
- `results/env.json`: produced (AMD Ryzen 7 5700U, 16 logical cores, 15.38 GB, no NVIDIA GPU detected).

**Data check** (`results/data_check.json`, 3 of 10 components ok):
- VisDrone MOT train: 56 sequences, 24,201 frames, 1,169,359 annotation rows. Schema ok.
- VisDrone MOT val: 7 sequences, 2,846 frames, 118,127 rows. Schema ok.
- VisDrone MOT test-dev: 17 sequences, 6,635 frames, 333,700 rows. Schema ok.
- All three: 10 integer columns, categories 0 to 11 all seen. Read from zips; archive CRC not verified.
- VisDrone DET train and val: missing.
- Mid-Air: only the download URL list is present (four climates, 102 trajectories); no data.
- AU-AIR: missing (expected).

## 2026-10-18: Phase 1 (geometry core)

**Built (test-first; tests written and seen failing before the code):** `aerialrange.geometry`
- `frames.py`: elementary rotations, yaw-pitch-roll, heading, camera mount and tilt, Hamilton quaternions, exact WGS 84 conversion from GPS to local NED.
- `camera.py`: `Camera` (K, R_bc, t_bc, Brown-Conrady distortion), `Pose`, `pixel_to_world_ray`, `project_world_point`, distort and undistort.
- `ranging.py`: `RangeEstimate`, horizontal and general plane intersection, validity reason codes, contact-point rules (`bottom_centre`, `centre_with_height`), `estimate_range`.
- `uncertainty.py`: parameter covariance (with optional correlations), numerical Jacobian, first-order and Monte Carlo propagation, nonlinearity ratio, reliability flags.
- `kalman.py`: world-frame constant-velocity filter, two-point initialisation, Joseph update, predict-only on misses, speed and heading with sigmas.

**Checks run:**
- `ruff check` and `ruff format --check`: clean.
- `pytest`: 150 passed (about 70 s; the Monte Carlo and NEES tests take most of it).
- Coverage: 100 % of statements in all five geometry modules; 94 % for the package overall.
- Required convention tests (Section 6.1) all pass: tilt 0 puts the optical axis along body forward; tilt 90° along body down; the principal point of a nadir camera on a level drone gives world ray (0, 0, 1).
- Analytic oracles (Section 6.3) for ∂X/∂h, ∂X/∂u, ∂X/∂fx, ∂X/∂cx and ∂N/∂v: the numerical Jacobian matches to a relative 1e-6.
- First order and Monte Carlo agree in a near-linear nadir case. In a near-horizon case (about 3° depression) the Monte Carlo range distribution is right-skewed and first order underestimates the spread, as expected.
- NEES of a simulated moving target is consistent; a stationary target seen from a moving drone gives velocity consistent with zero.

**Fixed during the phase:** one test was wrong, not the code. It assumed an east offset has zero north component, but the ellipsoid gives a micrometre poleward term. The test now asserts that term.

**Open:** see `TASKS.md` (carried-forward items) and `docs/decisions.md` (D-102, D-104, D-110 and the reference check).

## 2026-10-19: Phase 2 started (Mid-Air), on the 7 trajectories downloaded so far

- `scripts/download_midair.py`: resumable downloader. Kite_training/sunny, without colour images. Running; trajectories 0 to 6 complete at the time of writing.
- `aerialrange.data.midair`: loader (depth, segmentation, normals, intrinsics, poses, back-projection to world). 12 synthetic-fixture tests.
- `aerialrange.evaluate.midair_unknowns` and `scripts/midair_unknowns.py`: Section 7.3 unknowns, resolved by test on real data. Results in `results/midair/unknowns.json`, decisions D-201 to D-207. Depth is radial; the quaternion is wxyz and body-to-world; the mount is the level forward mount; sky is the float16 maximum; normals decode correctly on average but scatter about 3° per pixel.
- `tests/test_midair_real.py`: 5 real-data regression tests (skipped without data).
- Lint clean; `pytest` 167 passed.
- Split fixed (D-208): `results/splits.json`, 15 / 6 / 9 trajectories.
- Batch ranging and first-order propagation (`estimate_range_batch`, `propagate_batch`), test-first, matching the scalar versions.
- `aerialrange.evaluate.midair_ranging` and `scripts/midair_eval.py`: sampling, ground truth, and the `oracle_plane` and `relative_altitude` modes (D-209, D-210). First development run on the 5 downloaded development trajectories (223,000 samples): `results/midair/development/accuracy.json`. Development observations only, not results: error falls steeply with depression angle and is near zero on flat ground (slope below 5°); about 12 % of ground samples lie above the camera and cannot be ranged with a horizontal plane.
- Lint clean; `pytest` 180 passed.

## 2026-10-19: preparation while downloads run (Phases 2, 3 and 5)

**Mid-Air (Phase 2) pipeline, ready for the full data:**
- `evaluate/stats.py`: trajectory-bootstrap intervals, binned statistics with the reporting rule, coverage, the recalibration scalar, AUROC, precision/recall, the max-F1 operating point, usable limits, and the stability check. All tested on synthetic data with known answers.
- `evaluate/midair_analysis.py`: everything recomputed from the cache, with no image re-reads. Noisy-inputs mode, first-order and Monte Carlo predicted sigma, the sensitivity tornado, and the tilted-plane and local-slope diagnostics. The key end-to-end test is that injected noise against propagated sigma gives z with unit spread on flat ground. Writing that test found a real bug in `propagate_batch` (a rounding-level negative under a square root gave NaN); it is fixed, with a regression test.
- Scripts: `midair_stability.py` (set N_BOOT = N_MC = 1000, D-215); `midair_analyse.py` (every Section 7.7 output and figure for a split); `midair_calibrate.py` (fit on calibration, apply to test once).
- Figures follow the dataviz rules, with the validated palette slots and a CSV beside each figure.
- `docs/runbook.md`: the exact commands to finish.

**VisDrone (Phase 3) preparation:**
- Data reorganised by Luke; the config was updated and the data check passes for MOT train, val and test-dev and DET train and val.
- `data/visdrone.py`: parser with schema errors, groups, the ignored-region filter, MOTChallenge conversion, YOLO labels and average hashing. MOT ground truth converted for all splits; YOLO set built.
- **Finding (D-308):** DET images share source videos with MOT val and test-dev, contrary to build.md Section 4.1. 78 images were excluded from training and selection.
- `track/evaluate.py` (motmetrics with our own IoU distance, D-306), `track/runner.py`, `detect/evaluate.py` (AP by group and size), `detect/tiling.py` (B3).
- **B0 run on val** (YOLO26n at 640, ByteTrack, library defaults, zero-shot COCO), from `results/visdrone/val/B0_yolo26n_640_bytetrack.json`: person MOTA 0.143, IDF1 0.215; vehicle MOTA 0.212, IDF1 0.330. Development numbers only, not reportable.
- `scripts/train_detector.py` for B2 is ready; the compute decision is in BLOCKED.md.

**Phase 5 and 6 tools:** `edge/benchmark.py` (per-stage percentiles; refuses a budget verdict without TARGET_FPS) and `scripts/fill_docs.py` ({{RESULT:...}} tokens and the release check).

**Environment:** torch 2.14.1 (CPU), ultralytics 8.4.182 (AGPL-3.0), opencv 5.0.0.93, motmetrics 1.4.0, pandas 3.0.6, matplotlib 3.11.2, lap 0.5.13. The lockfiles are split (D-306).

**Checks:** lint clean; `pytest` 243 passed.

## 2026-10-19: development analysis complete (6 of 15 development trajectories)

Development observations only, from `results/midair/development/*.json`. These are not results. The final numbers come from the test split once.
- H2: above 5 degrees of depression, the noise-induced range error matches the first-order and Monte Carlo predictions closely (MC/FO median ratio about 1.0). Below 2 degrees, MC exceeds first order by about 10 times, the nonlinear regime (`propagation.json`).
- H3: the propagated sigma models sensor noise only; terrain error dominates on Mid-Air, so z is heavy-tailed and over-dispersed at every sweep level (`sweep.json`). A single scalar cannot fix the shape. Decision needed (BLOCKED.md item 4).
- H4: the flat-plane error grows with local slope; the tilted-plane and local-slope diagnostics explain part of it on gentle slopes (`slope.json`). Water (flat) errors are about 0.15 % (`summary.json`).
- Flag AUROC is about 0.6 for every large-error definition: weak (`flag.json`).
- Sensitivity: height above plane dominates, then pitch and tilt (`sensitivity.json`).
- Fixes found by this run: a crash in `robust_plane` on frames with too few points (fixed and tested); the analysis now saves each stage as it finishes; a 12-second end-to-end smoke test was added; figure labels no longer collide.
