# Task list (mirrors build.md Section 12)

## Phase 0: bootstrap
- [x] Repository layout, `pyproject.toml`, Makefile, ruff and pytest setup
- [x] CI workflow (`.github/workflows/ci.yml`)
- [x] `.gitignore` (data, weights, venv, Mid-Air download token)
- [x] `PROGRESS.md`, `BLOCKED.md`, this task list
- [x] Configs with `null` placeholders and a loader that refuses unresolved values
- [x] `scripts/env_report.py` → `results/env.json`
- [x] `scripts/check_data.py` → `results/data_check.json`
- [x] Exit: lint and tests pass; CI file present; `results/env.json` produced (see PROGRESS.md for the `make` caveat)

## Phase 1: geometry core (test-first)
- [x] 6.1 frames and conventions, pinned by tests
- [x] 6.2 ray and plane intersection, contact-point rules, general plane
- [x] 6.3 uncertainty: numerical Jacobian vs analytic oracles, first order vs Monte Carlo
- [x] 6.4 ground-plane Kalman filter with NEES test
- [x] Exit: all geometry tests pass; coverage of every public function; decisions.md entries
- [ ] Carried forward: AU-AIR body-frame figure check (Phase 4); verify cited section numbers (Phase 6)

## Phase 2: Mid-Air validation (needs data)
- [x] 7.2 loader with synthetic tests
- [x] 7.3 unknowns resolved by test (depth radial, quaternion, mount) on trajectories 0 to 6
- [ ] Download complete (running)
- [x] Trajectory split (`{{MIDAIR_SPLIT}}`), approved by Luke 2026-10-19
- [ ] Mount-offset check on the development split
- [x] 7.6 sampling (development values, D-209); oracle_plane and relative_altitude modes
- [x] 7.5 noisy_inputs mode and sweep design (D-212); headline noise from AU-AIR later
- [x] 7.7 binned curves with trajectory bootstrap, first order vs Monte Carlo overlay (code; N_BOOT, N_MC set, D-215)
- [x] 7.7 calibration, recalibration scalar, flag, tornado (code); needs `{{ERR_THRESHOLD_FRAC}}` from Luke
- [x] H4 tilted-plane and local-slope diagnostics (code, D-211)
- [x] 7.8 figures and CSV tables (code)
- [ ] Sensitivity of edge margin and normal patch (after full download)
- [ ] Full development and calibration runs (after full download)
- [ ] Final test-split run, once, after freezing

## Phase 3: tracking baseline
- [x] Data check, MOT ground-truth conversion, YOLO set, DET/MOT overlap check and leakage exclusion (D-308)
- [x] Tracking evaluation (motmetrics), detection AP by size, tiling, runner, training script
- [x] B0 (YOLO26n, 640, ByteTrack) on val
- [ ] B0 variants (sizes, BoT-SORT with and without camera-motion compensation), detection AP for B0
- [ ] B2 fine-tuning (compute decision needed)
- [ ] B3 tiling; tracker grid on val; pixel-noise fit `{{SIGMA_PIX_MODEL}}`; failure gallery
- [ ] Test-dev once; H1 table

## Phase 4: AU-AIR and integration (needs AU-AIR)
- [ ] Section 8 and 11.1

## Phase 5: edge budget
- [x] Benchmark harness (per-stage percentiles, budget verdict)
- [ ] ONNX export and parity, quantisation, protocol runs, Pareto (needs TARGET_FPS)

## Phase 6: deliverables and polish
- [ ] Section 13 and the release checklist (Section 16)
