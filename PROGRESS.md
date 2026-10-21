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

## 2026-10-19: queued model runs (development, VisDrone val)

- B0 tracker comparison, YOLO26n at 640, zero-shot (from `results/visdrone/val/*.json`): BoT-SORT with camera-motion compensation scored best (person MOTA 0.157 / IDF1 0.246; vehicle 0.236 / 0.385), ahead of BoT-SORT without it (0.147 / 0.225; 0.217 / 0.336) and ByteTrack (0.143 / 0.215; 0.212 / 0.330). Development numbers only.
- ONNX export parity (`results/edge/parity_yolo26n_640.json`): agreement 98 % from the original's side and 91 % from the ONNX side; the ONNX model returns more detections (462 against 431 on 50 frames). The largest box difference is 21 px and the largest score difference 0.18. That is more than numerical noise, so it needs investigating (likely a difference in post-processing) before any parity claim.
- CPU training probe (`results/visdrone/train/probe_yolo26n_640_e1_f0.1/`): 41 batches of 16 images in 347 s (8.5 s per batch), so a full epoch over 6,414 images takes about 1 hour for YOLO26n at 640. The library default of 100 epochs is about 4 days of continuous CPU time.
- Bug found and fixed: detection AP crashed on images without ground truth in a size bin (regression test added). Detection AP rerunning.
- B0 detection AP on val (`results/visdrone/val/detect_B0_yolo26n_640.json`, every 10th frame): person AP50 0.171, vehicle AP50 0.248. By box height, AP50 is near zero below 32 px (person 0.0 and 0.0; vehicle 0.0 and 0.051) and rises to 0.278 (person) and 0.810 (vehicle) above 128 px. This is the small-object gap that fine-tuning (B2) and tiling (B3) target. Development numbers only.

## 2026-10-19: terrain from motion (plan D), first evidence

Luke's decisions: D + E + B + C. A fixed bumpiness value (plan A) was rejected as hedging rather than solving. F (terrain map) is out.
- `geometry/triangulation.py`: two-view and batch triangulation with first-order covariance (pixel and pose noise), written test-first. It matches the textbook stereo depth-sigma oracle within 2 %, and Monte Carlo within 10 % (11 tests).
- `geometry/terrain.py`: robust local plane height field (k-nearest or radius), ray intersection, and an uncertainty built from the fit covariance plus measured local roughness. Tests include coverage of about 68 % on synthetic bumpy ground (8 tests).
- `evaluate/terrain_motion.py`: Lucas-Kanade tracking with a forward-backward check, triangulation with known poses, and per-target terrain ranging. It does not use segmentation or depth (deployable).
- First look (development trajectory 0002, every 4th evaluated frame, untuned settings; development only, not a result): median |relative error| on land is 0.056 for terrain-from-motion, which needs no height, against 0.068 for the flat oracle (which uses the true height) and 0.851 for the relative-altitude mode. Near the horizon (0-5 degrees) it is 0.119 against 1.295 for the flat oracle. Uncertainty: robust z spread about 1.7, against about 22 for the flat sensor-only model. Weak spot: steep views (40-90 degrees), 0.080 against 0.033 for the flat oracle. The likely cause is that fast near-ground image motion defeats tracking at a 5-frame gap; to investigate.
- Also: `scripts/archive_midair.py` (verified moves to Google Drive, authorised by Luke). An early run was stopped by a wrong cache measurement and fixed, with no data lost (all 2,205 frames of the partly moved flight accounted for).
- Per-feature baseline selection (gaps 1, 2, 5, 10, chosen by total covariance), D-401. On the trajectory 0002 probe, the median error went from 0.056 to 0.028 and steep views from 0.080 to 0.020.
- Tracking noise measured on 4 development trajectories (`results/midair/development/tracking_noise.json`): robust sigma 0.125 to 0.23 px by gap, with heavy tails. Recorded as `{{TERRAIN_SIGMA_PX}}` (D-402).
- `evaluate/conformal.py` (B, D-403), `evaluate/flag.py` (E, D-404), `scripts/terrain_analyse.py` (compare, fit on calibration, apply to test once), with an end-to-end smoke test. 283 tests pass.

## 2026-10-20 (overnight): B2 detector, terrain on all development trajectories

- B2 (YOLO26n at 640, fine-tuned on Kaggle T4, 50 epochs, `results/visdrone/train/B2_yolo26n_640/`): final DET-val mAP50 0.303 (all 10 classes). Published reference for a comparable model: YOLOv8n at 640 scores 0.334 on the same validation set (Sensors 2023 table), so this is the expected range for a nano model. MOT-val vehicle AP50 0.587 against 0.248 for B0 (development).
- Detection cap raised to 1000 per image (D-316). Overnight queue: re-score B0 and B2, tracking with both trackers, pixel-noise fit, tiling sweep, then calibration (`cache/overnight.sh`, `cache/logs/overnight.log`).
- Terrain from motion on all 15 development trajectories (world support), from `results/midair/development/terrain/`: land median |relative error| 0.021 [0.016, 0.028] (78 % valid), against 0.161 for a flat plane at the true height and 2.53 for the altimeter. The terrain error stays at about 0.02-0.03 across slopes of 0-45 degrees. Tail: about 13 % of estimates more than 50 % off, nearly all underestimates; diagnosed and addressed by image-space support (D-405); full rerun in progress.
- Bug fixed: the archive resume decided "already moved" from the depth marker only (trajectory 0017 had been interrupted mid-normals). It now requires every modality. Calibration flights kept local (archive restricted to test).
- Terrain with image-space support, all 15 development trajectories (D-405): 94.1 % valid (was 77.8 %), median 0.0249 [0.0207, 0.030], 90th percentile 0.417 (was 0.727), 68 % coverage before calibration 0.60 (was 0.52).
- VisDrone val (development), max_det 1000: B2 against B0. Detection AP50 person 0.412 against 0.171, vehicle 0.587 against 0.248. Tracking (BoT-SORT with camera-motion compensation) IDF1 person 0.392 against 0.246, vehicle 0.586 against 0.385. B2 BoT-SORT with compensation beats B2 ByteTrack for both groups.
- B3 first tiling setting (tile 480, overlap 0.2): small-object AP50 rises (vehicle 16-32 px: 0.345 against 0.266) but overall AP50 falls (vehicle 0.477), because large objects split across tiles. Next: merge full-frame and tile detections.
- Pixel noise (`results/visdrone/val/pixel_noise.json`): kappa_u / kappa_v person 0.109 / 0.086, vehicle 0.039 / 0.052, recorded as `{{SIGMA_PIX_MODEL}}`.
- Overnight queue completed (all steps exit 0; `cache/logs/overnight.log`).
- Calibration split: terrain with image support, 95-97 % valid per trajectory. Conformal (B) and flag (E) fitted on calibration (`results/midair/terrain_calibration_fit.json`). Conformal global multipliers: 1.10 at 68 %, 2.61 at 90 %, 5.83 at 95 %, 141.6 at 99 %, a heavy tail.
- Applied to development (held out from the fit): coverage at 50 / 68 / 90 / 95 / 99 % was 0.466 / 0.646 / 0.872 / 0.928 / 0.981 calibrated, against 0.45 / 0.603 / 0.783 / 0.828 / 0.878 raw. Flag AUROC 0.767, precision 0.50, recall 0.60, 28.5 % flagged. Largest coefficient: roughness relative to range.
- B3 sweep on val: tile-only lowers overall AP50 but raises small-object AP50 (tile 640, overlap 0.3: vehicle 16-32 px 0.394 against 0.266). Tile 480 plus full frame recovers most of the overall AP50 (person 0.392, vehicle 0.574) at about 3.2 s/image against 0.12 s (wall time, not the benchmark protocol). Tile 640 plus full frame still running.
- B3 selected on val: tile 640, overlap 0.2, plus full-frame pass. AP50 person 0.427 / vehicle 0.610 against B2 0.412 / 0.587; 16-32 px AP50 person 0.073 / vehicle 0.376 against 0.040 / 0.266; about 1.6 s/image wall time against 0.12 s. Recorded in `configs/detector.yaml` (`tiling`). Tracking with tiled detection still needs a tracker loop fed by custom detections (next session).
- Tiled tracking: `track/runner.py` gains `DetSet`, `make_tracker` and `run_sequence_custom`, which feed any detection function to the library trackers (tested: a steadily moving box keeps one identity under ByteTrack and BoT-SORT). `scripts/track_eval.py --tiled` uses the D-317 tiling setting. Full B3 BoT-SORT run on val in progress. 288 tests pass.
- B3 tracking on val (BoT-SORT with camera-motion compensation, tiling D-317) is **worse** than B2 despite higher detection AP. IDF1 person 0.322 against 0.392, vehicle 0.425 against 0.586. Identity switches 1425 / 938 against 663 / 307. Precision 0.51 / 0.52 against 0.62 / 0.69; recall slightly higher. Tiling adds fragmentary and duplicate boxes at tile edges (class-wise IoU-NMS does not merge partial boxes), which the tracker turns into identity switches. Next: intersection-over-smaller merging (as in SAHI) and a confidence threshold tuned on val; until then B2 is the better tracking configuration.
- **Bug found and fixed (tiled tracking):** BoT-SORT's camera-motion compensation reads `xyxy` from the detections, and the `DetSet` wrapper only had `xywh`. GMC therefore fell back to identity ("GMC failed" warnings in the logs), so every tiled tracking run so far had compensation off and was not comparable with B2. Fixed (`DetSet.xyxy`, regression test). The invalid results are kept, renamed `*__INVALID_gmc_off.json`. Within those runs, IoS merging (D-318) improved vehicle IDF1 from 0.425 to 0.499 (IoS 0.5) and 0.476 (IoS 0.8). B3 with IoS 0.5 is being rerun with GMC working.
- B3 with GMC fixed and IoS 0.5 merging (val, BoT-SORT with compensation): IDF1 person 0.390 / vehicle 0.573 against B2 0.392 / 0.586, so about equal. Recall higher (0.522 / 0.694 against 0.490 / 0.633), precision lower (0.507 / 0.576 against 0.622 / 0.690), MOTA lower, wall time about 7 times longer (1.48 s against 0.21 s per frame). B2 stays the default tracking configuration; the extra low-confidence detections are a case for the val confidence-threshold grid (`{{TRACKER_GRID}}`).

## 2026-10-20: new detectors scored; tracker grid (development, VisDrone val)

- **Detection, new B2 models** (MOT val, every 10th frame, score floor 0.25 as for B0 to B3; `results/visdrone/val/detect_B2_yolo26n_960.json`, `detect_B2_yolo26s_640.json`):

  | | B2 n 640 | **B2 n 960** | **B2 s 640** | B3 (n 640, tiled) |
  |---|---|---|---|---|
  | Person AP50 / AP50:95 | 0.412 / 0.149 | 0.511 / 0.204 | 0.507 / 0.201 | 0.427 / 0.157 |
  | Vehicle AP50 / AP50:95 | 0.587 / 0.352 | 0.625 / 0.377 | 0.627 / 0.371 | 0.610 / 0.343 |
  | Person 16-32 px AP50 | 0.040 | 0.089 | 0.090 | 0.073 |
  | Vehicle 16-32 px AP50 | 0.266 | 0.333 | 0.330 | 0.376 |
  | Wall time per image (rough) | 0.12 s | 0.13 s | 0.15 s | 1.64 s |

  Both new models beat B2 n 640 and B3 on overall AP, and are close to each other. The wall times are not the Section 10.4 benchmark; 960 against 640 needs that benchmark before any speed claim. DET-val mAP50 (all 10 classes, training curves): n 640 0.308, n 960 0.415, s 640 0.399. **n 960 peaked at its last epoch (50), so it had not converged**; s 640 stopped early at epoch 49 (best 39).
- Tracker grid set up (D-319): `track/detcache.py`, `scripts/cache_detections.py` and `scripts/track_grid.py`; `make_tracker` and `run_sequence_custom` accept overrides, with unknown keys refused. Tests: replay matches live detection, overrides take effect, and frames of the wrong size are refused. 296 tests pass; lint clean.
- **Finding:** tiled tracking (B3) used a score floor of 0.25, whereas live tracking uses 0.1, so earlier B3 tracking was not like-for-like (D-319). The cached grid uses 0.1 for every detector.
- Validation detections cached for n 640 (202 s), n 960 and s 640; B3 tiled cache running.
- First grid attempt ran out of memory: 5 workers at about 1.0-1.35 GB each, beside the B3 cache job, on 15.4 GB of RAM, so the machine swapped and one worker failed. No results were lost (none had finished). Restarted with 3 workers.
- **Tracker grid complete** (D-319 to D-321; `results/visdrone/val/grid_summary.json` and `.csv`, from `scripts/grid_summary.py`). Replay check: the B2 n 640 default point reproduces the live run exactly (IDF1 0.392 / 0.586, MOTA 0.180 / 0.341). BoT-SORT with compensation, mean IDF1 over person and vehicle, default → tuned:

  | Detector | Default | Tuned (high / new) | Person IDF1 | Vehicle IDF1 | Person / vehicle IDSW |
  |---|---|---|---|---|---|
  | B2 n 640 | 0.489 | 0.540 (0.45 / 0.45) | 0.422 | 0.657 | 213 / 102 |
  | **B2 n 960** | 0.559 | **0.620** (0.05 / 0.55) | **0.548** | 0.693 | 168 / 68 |
  | **B2 s 640** | 0.551 | **0.613** (0.25 / 0.65) | 0.530 | **0.695** | 108 / 46 |
  | B3 (n 640 tiled) | 0.462 | 0.539 (0.15 / 0.65) | 0.439 | 0.639 | 156 / 101 |

  ByteTrack, tuned: 0.473 / 0.537 / 0.546 / 0.483, below BoT-SORT in every case. Tuning raises precision and cuts identity switches but lowers recall (n 960 person recall 0.623 → 0.517). n 960 against s 640 is a tie on accuracy; the latency benchmark decides (needs `{{TARGET_FPS}}`). Provisional default: n 960, BoT-SORT with compensation, 0.05 / 0.55 (`configs/tracker.yaml`).
- Grid edges: the s 640 optimum is interior after the extension; for n 960 the 0.05 edge is below the 0.1 floor, where all values are equivalent. B3 is not extended (0.08 behind, 7-13 times slower).
- **AU-AIR (Phase 4 data) found by Luke**: copied to `Data/AU-AIR` (32,824 files, 2.283 GB, 0 failed), `configs/data.yaml` set. Licence CC BY 4.0 (Luke). Annotations: 32,823 frames at 1920 × 1080, 8 classes, per-frame GPS, altitude and attitude.
- AU-AIR verified (every image decoded): 32,823 frames, all 1920 × 1080; 0 missing, extra, duplicated or unreadable; every frame has boxes. Boxes per class: Car 102,619; Van 9,995; Truck 9,545; Human 5,158; Trailer 2,538; Bicycle 1,128; Bus 729; Motorbike 319. People are scarce, so AU-AIR person results will rest on few objects. **Licence conflict** (BLOCKED.md item 6): Luke reports CC BY 4.0; the file's `licenses` field lists CC BY-NC-SA 2.0 and CC BY-NC 2.0.
- Checks: 296 tests pass; lint clean.

## 2026-10-20 (afternoon): frame-rate target set; Phase 4 started

- **`{{TARGET_FPS}}` = 30** (Luke, D-322): a stretch target, with 10 fps reported as a reference point. Budget 33.3 ms per frame, derived by the loader; the config test now checks the derived budget and still checks that an unset target is refused.
- AU-AIR licence (D-323): the CC BY 4.0 statement comes from a third-party index; the authors' file says CC BY-NC. The restrictive reading is adopted (non-commercial, attributed, no AU-AIR images in the repository).
- **Phase 4, Section 8.1:** `scripts/inspect_auair.py` → `results/auair/schema.json` (schema read from the file). Findings (D-501): 5 fps (200 ms steps); `time.ms` is milliseconds since recording start; `hour/min/sec` are the recording start, not per-frame; `_xx` files continue `_x`; altitude in mm; angles in radians. Totals: frames 32,823 (paper 32,823), instances 132,031 (paper 132,034).
- `data/auair.py` (name parsing, clip segmentation, frame table with metres and local NED), test-first: 4 tests. `configs/auair.yaml` (frame interval, measured; clip gap 6 s, derived, D-502). `scripts/auair_frames.py` → 48 clips in 8 recordings (`results/auair/clips.csv`, `totals.json`).
- **Section 8.2:** `scripts/contact_sheets.py` → 48 sheets (`cache/auair/contact_sheets/`, not committed) and `docs/auair_clip_notes.md` with label columns for Luke. **Finding (D-503):** the camera is mostly oblique and its tilt changes within clips, and AU-AIR does not record the camera tilt (only body angles of a few degrees). Estimating per-frame tilt from the images becomes the central Phase 4 problem.
- Checks: 303 tests pass; lint clean.
- Release-check item: `results/midair/development/flag.json`, `results/visdrone/train/probe_yolo26n_640_e1_f0.1/args.yaml` and `results/visdrone/val/grid_B2_yolo26n_640__bytetrack.json` contain absolute local paths (user folder). Strip them to repository-relative paths before any public release. New AU-AIR outputs already use relative paths.
- **Luke's clip labels** (D-504, `results/auair/clip_labels.csv` via `scripts/auair_labels.py`): straight down 18 clips / 3,027 frames (9 %; all of recording 20190829091111); oblique 21 / 19,573 (60 %); mixed 9 / 10,223 (31 %); no visible curvature. Views of 5-30° contradict the paper's stated 45-90° range; reported.
- **Camera-tilt plan** (Luke, D-505): straight-down clips first (Sections 8.3 to 8.5 as written), then per-frame tilt from ground motion between frames, which must give about 90° on the straight-down clips.
- First look at scale on straight-down clips (development observation, not a result): ground-truth car boxes not touching the border (3,566), median long side × altitude = 6,010 / 7,151 / 6,250 / 6,436 px·m at 15 / 21 / 26 / 29 m. This is f × L; at a car length of about 4.5 m it suggests f ≈ 1,400 px (about 69° horizontal field of view). Still needed: aligned boxes only (box aspect ratios peak at 1.8 to 2.2), an altitude-offset term (the take-off level is unknown), a cited car-length distribution (`{{CAR_LENGTH_PRIOR_SOURCE}}`), and the Bebop 2 specification prior.
