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
