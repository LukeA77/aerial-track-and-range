# Decision log

Each entry: what was decided, why, and the source. Newest last.

## Phase 0

**D-001 Python version.** Python 3.12 (`{{PYTHON_VERSION}}`). It is the installed interpreter (3.12.10), and every dependency installed so far has a 3.12 build. This is provisional: the train and edge extras (detector library, ONNX Runtime) are not installed yet, so 3.12 is re-checked when they are added in Phases 3 and 5. Exact versions are in `requirements-lock.txt` (from `pip freeze`, 2026-10-18).

**D-002 Config format.** Every entry in `configs/*.yaml` is `{value, placeholder, source}`. A `null` value is an unresolved `{{PLACEHOLDER}}`. `Config.require` raises `MissingParameterError` naming the placeholder. A test fails if any value is set without a source (R2).

**D-003 Data root.** `Data/` inside the repository, because that is where Luke's downloads are. It is git-ignored (R7), and the environment variable `AERIALRANGE_DATA_ROOT` overrides it. Waiting for Luke to confirm (BLOCKED.md item 4).

**D-004 Data check reads zips in place.** The VisDrone MOT sets are present as zips. `check_data.py` reads the listings and annotation text straight from each archive and never extracts or modifies data. Archive checksums (CRC) are not verified yet, because reading 11 GB takes a long time. Section 4 asks for checksums in `docs/data_cards.md`, so that is done when the data cards are written.

**D-005 Licence.** AGPL-3.0, chosen by Luke on 2026-10-18 after the trade-off in risk R8 (Ultralytics is AGPL-3.0). The `LICENSE` text was downloaded from `https://www.gnu.org/licenses/agpl-3.0.txt` on 2026-10-18. The "-only" or "-or-later" variant is still to be confirmed.

**D-006 Dependency licences** (each read from the package's own metadata, 2026-10-18):

| Package | Version | Licence |
|---|---|---|
| numpy | 2.5.4 | BSD-3-Clause (bundled parts: 0BSD, MIT, Zlib, CC0-1.0) |
| scipy | 1.18.1 | BSD |
| PyYAML | 6.0.3 | MIT |
| h5py | 3.16.0 | BSD-3-Clause |
| Pillow | 13.0.0 | MIT-CMU |
| typer | 0.27.3 | MIT |
| pytest, pytest-cov, ruff | 9.1.1, 7.1.0, 0.17.1 | MIT |

Ultralytics (AGPL-3.0, risk R8) is not installed yet. It is added in Phase 3.

## Phase 1 (geometry core)

Every convention below is pinned by a test. The test names are given so a reviewer can check each one.

**D-101 Frames.** World is North, East, Down (NED); body is forward, right, down (FRD); camera follows OpenCV (x right, y down, z forward). `R_ab` maps frame b into frame a (`v_a = R_ab v_b`). Tests: `tests/test_frames.py`, `tests/test_camera.py`.

**D-102 Attitude.** Aerospace yaw-pitch-roll, `R_wb = Rz(yaw) Ry(pitch) Rx(roll)`. Positive pitch is nose up, positive roll is right wing down, and yaw is the heading clockwise from North (`test_ypr_sequence_is_yaw_then_pitch_then_roll`, `test_positive_pitch_is_nose_up`, `test_positive_roll_is_right_wing_down`, `test_yaw_90_points_body_forward_east`). The check against AU-AIR's body-frame figure (Section 6.1) is **not done yet**, because the paper was not opened in this session. It happens in Phase 4, before any AU-AIR result. The paper's sample attitude (roll 0.011, pitch 0, yaw 1.26 rad) is used only as a heading round-trip test here.

**D-103 Camera mount and tilt sign.** Default mount `R_BC_FORWARD`: camera z to body forward, x to right, y to down. Tilt `δ` (depression) is applied as `R_bc = Ry(−δ) R_BC_FORWARD`. The minus sign follows from positive rotation about body right being nose up. The tests decide it: `δ = 0` puts the optical axis along body forward, and `δ = 90°` puts it along body down. One consequence is pinned by `test_nadir_mount_keeps_image_right_as_body_right_and_image_top_forward`: at nadir, the image top points to body forward and image right stays body right. The same rotation is used to perturb tilt in the uncertainty model.

**D-104 Quaternions.** Hamilton convention, active rotation, default component order `wxyz`, with `xyzw` available. Mid-Air's order and active/passive convention are still unknown (Section 4.3). They are pinned in Phase 2 from the dataset's example scripts, with a known-orientation test.

**D-105 GPS to local NED.** Exact WGS 84 conversion through Earth-centred, Earth-fixed coordinates, instead of a tangent-plane approximation, so the approximation's validity never has to be argued. Constants: a = 6378137.0 m, f = 1/298.257223563 (NIMA TR8350.2, Table 3.1; EPSG:7030). Tests compare small offsets with the meridian and prime-vertical radii. They also check the second-order poleward term that a 6 m east offset produces (about E² tan φ / 2N, a few micrometres), which shows that the conversion is ellipsoidal rather than flat.

**D-106 Validity.** An estimate is invalid when the ray is at or above the horizon (Down component ≤ 0, reason `ray_at_or_above_horizon`), or when the camera is not above the plane (`camera_not_above_plane`). No numerical margin is added. Where the ray is valid but unusable (near the horizon), that is handled by the uncertainty model and the `{{MIN_DEPRESSION_DEG}}` reliability flag, which Phase 2 derives from data. The general plane adds `ray_parallel_to_plane` and `plane_behind_camera`.

**D-107 Height-aware contact point.** In `centre_with_height` mode, the ray is intersected with a plane raised by the object height. The returned point is the ground contact directly below that intersection, and `range_m` is measured to the ground contact, so both modes report the same physical quantity. `depression_deg` is the depression of the ray. Test: `test_centre_with_height_recovers_object_ground_position_at_nadir`.

**D-108 Lens distortion.** Brown-Conrady with five coefficients (k1, k2, p1, p2, k3, in OpenCV's order), implemented directly because OpenCV is not a dependency yet. Undistortion uses fixed-point iteration. The iteration cap and tolerance are numerical settings, checked by a round-trip test. With no coefficients, the pinhole model is assumed.

**D-109 First-order propagation.** Noise is modelled as perturbations about the nominal inputs. Attitude noise acts on the Euler angles (the form AU-AIR logs). Tilt noise is an extra rotation about body right. The Jacobian is of the 3D ground point, by central differences with step `ε^(1/3) · max(|θ_i|, σ_i)` (Nocedal and Wright, 2006, Numerical Optimization, 2nd edn, Section 8.1). Then `Σ_P = J Σ_θ Jᵀ`, and range, ground-distance and bearing sigmas come from the gradients of those quantities with respect to P (Section 6.3). Parameters with σ = 0 are skipped. Bearing sigma is undefined (NaN) for a point within rounding error of directly below. Correlated altitude and pitch are supported through a correlation map.

**D-110 Monte Carlo.** Draws use an eigen-decomposition square root, which handles singular (fully correlated) covariances. Invalid draws are dropped, counted and flagged (`mc_invalid_draws`). Range percentiles cover the 50, 68.27, 90, 95 and 99 per cent central intervals, and the azimuth spread uses wrapped differences. `nonlinearity_ratio` is the Monte Carlo range sigma divided by the first-order one. Section 6.3 says "disagree materially" but gives no threshold, so that threshold is a new placeholder, `{{NONLINEAR_RATIO_TOL}}` in `configs/uncertainty.yaml`, to be set in Phase 2. The number of draws, `{{N_MC}}`, must be passed explicitly; there is no default.

**D-111 Kalman filter.** State `[N, E, vN, vE]` in the world frame, with a constant-velocity model and continuous white-noise acceleration of spectral density `{{KALMAN_Q}}` (m²/s³). Two-point initialisation means no initial-velocity variance has to be invented. Updates use the Joseph form. Missed detections are predict-only. Heading is clockwise from North. Reference: Bar-Shalom, Li and Kirubarajan (2001), Estimation with Applications to Tracking and Navigation.

**D-112 Test tolerances.** The NEES test runs 200 seeded runs of 60 steps. It requires the run-averaged NEES to fall inside the two-sided 99 per cent chi-squared interval at no fewer than 96 per cent of time steps, and the time-averaged NEES to be within 10 per cent of 4. The first-order and Monte Carlo agreement test uses 20,000 draws and a tolerance of 5 per cent of the largest variance. All camera and noise values in the tests are synthetic fixtures. None of them is a dataset parameter.

**Reference check outstanding.** The section and table numbers cited in D-105, D-109 and D-111 are from memory. Verify them against the primary sources before they appear in the brief (R10).
