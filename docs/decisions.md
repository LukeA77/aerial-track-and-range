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

## Phase 2 (Mid-Air): unknowns resolved (Section 7.3)

Evidence: `results/midair/unknowns.json`, from `scripts/midair_unknowns.py` on Kite_training/sunny trajectories 0 to 6, every 100th frame. These are exploration settings, used only to choose frames for inspection. Sources were read on 2026-10-19: the Mid-Air technical specifications, data organisation and FAQ pages (https://midair.ulg.ac.be), and the example scripts `hdf5-depth_viewer.py` and `tools/IMU-data_generator.py` (github.com/montefiore-ai/midair-dataset). The regression tests in `tests/test_midair_real.py` keep these checks in the suite. They skip when the data is absent.

**D-201 Depth is radial.** The FAQ says depth is "the Euclidean distance of the objects to the focal point". The test agrees. Water (class 8) is genuinely flat, and plane fits to back-projected water pixels over 84 frames give a median RMS residual of 0.0067 m for radial depth against 2.13 m for planar. Radial wins in 96 % of frames. Depth decoding (PNG bits reinterpreted as float16, in metres) follows the example script.

**D-202 Quaternion convention.** Hamilton, `wxyz` (the HDF5 attribute `axis_ordering` says `wxyz`, and the loader refuses anything else). It is an active body-to-world rotation (`R_wb`), as in the IMU generator script. On real data, the IMU specific force predicted as `R_wbᵀ (a_w − g)`, with gravity along +Down, matches the accelerometer with RMS 0.05 to 0.20 m/s² per trajectory. The opposite convention gives 2.4 to 6.0 m/s². This also confirms that the world frame is NED. The gravity value of 9.81 m/s² is the one the dataset's own generator uses.

**D-203 Camera mount.** The FAQ gives camera-to-body as `(x_b, y_b, z_b) = (z_c, y_c, x_c)`, with pixel rows on `x` and columns on `y`. In OpenCV terms that is `R_BC_FORWARD` with tilt 0 and no lever arm (the HDF5 lists `local_position` (0, 0, 0) for the left camera). Test: the water-plane normal rotated into the world has a median tilt from vertical of 0.06° (95th percentile 0.16°), so no systematic mount offset shows at that level. Section 7.3 says to fit small offsets on the development split only if residuals are systematic. That check is repeated on the development split once the split exists. Not checked: the half-pixel convention, i.e. whether pixel centres sit at integer or integer + 0.5 coordinates. The site gives `cx = w/2`, which is used as given. At 1024 pixels with fx = 512, half a pixel is about 0.056°.

**D-204 Intrinsics.** fx = cx = w/2 and fy = cy = h/2 (technical specifications page), with no distortion (rendered images). Depth and segmentation are 1024×1024.

**D-205 Sky.** Sky pixels hold the largest float16 value (65504), not infinity. That value marks sky; it is not a real depth. Over 7 trajectories, the sentinel and segmentation class 0 (undocumented on the site) agree on all but 3,078 of 39.1 million sky pixels.

**D-206 Normals.** The normals are stored at 512×512, half the depth resolution. The decoding is the one on the specifications page: red → body Y, blue → body X, green → −body Z, each scaled from [−1, 1] to [0, 1]. Over 84 frames, the frame-mean water normal rotated into the world is within a median 0.49° of vertical, consistent with 8-bit quantisation around 127.5. Individual pixels scatter, with a median tilt of 2.95°. Consequence for Section 7.6: slope must be estimated from normals averaged over a patch, not from single pixels, and the averaging window is a documented choice in the sampling step.

**D-207 Frame-to-ground-truth mapping.** Row = floor(100 k / 25) = 4k (data organisation page, example script). There are 4 × frames − 2 ground-truth rows (for example 2206 frames and 8822 rows), so every frame has a row.

**D-208 Mid-Air split.** By trajectory, seed 0, with 50 / 20 / 30 % for development, calibration and test (15 / 6 / 9 of the 30 Kite_training/sunny trajectories). Claude proposed it and Luke approved it on 2026-10-19. The split is in `results/splits.json`, and `scripts/make_splits.py` refuses to overwrite it with a different split. **Disclosure:** the convention checks behind D-201 to D-207 were first run on trajectories 0 to 6, before the split existed. That set includes test trajectories 0001 and 0005 and calibration trajectory 0000. Those checks fitted and tuned nothing; they confirmed conventions already stated in the dataset documentation. They were then rerun on development trajectories only (0002, 0003, 0004, 0006, 0008), and `results/midair/unknowns.json` now holds that development-only run. Its numbers supersede those quoted in D-201 to D-206. Water-plane residual: median 0.0059 m radial against 2.48 m planar (radial better in 93 % of 45 frames). Water-plane tilt: median 0.061°. Frame-mean normal tilt: median 0.49°. Per-pixel normal scatter: median 3.06°. Quaternion residuals: 0.05 to 0.15 m/s² against 1.9 to 6.0 m/s² for the opposite convention. Sky and class 0 disagree on 187 of 28.6 million pixels. The real-data regression tests use development trajectory 0002.

**D-209 Pixel sampling (Section 7.6).** Development values. They are revisited once all development trajectories are downloaded and the bins are populated.
- `frame_stride` = 25 (one frame per second); frames at 25 Hz are strongly correlated.
- `pix_per_frame` = 500 sampled pixels per frame, from ground classes 3, 4, 5, 10 and 11 plus water (8, reported separately).
- `depth_edge_rel` = 0.1 (new placeholder). A pixel counts as next to a discontinuity if a 4-neighbour's radial depth differs by more than 10 %. Measured on development frames: the histogram of neighbour jumps falls steadily and then flattens into a long tail near 10⁻¹. That tail is real edges (rocks, trees, terrain occlusion), and 0.1 sits above the 99th percentile of ground-to-ground jumps (0.053). Sky and non-ground classes also count as discontinuities.
- `edge_margin_px` = 3. Pixels within 3 px of a discontinuity or the image border are excluded, which clears anti-aliased edge pixels with margin. This is a judgement, not a measurement; a sensitivity check is planned.
- `normal_patch_px` = 9 (new placeholder). Slope comes from body normals averaged over a 9 × 9 patch of the half-resolution normals image, using sample-class pixels only, because single pixels scatter by about 3° (D-206). Sensitivity check planned.

**D-210 Oracle plane.** Section 7.5 asks for a robust plane fitted per frame. Because the deployed pipeline uses a horizontal plane, `oracle_plane` uses a horizontal plane at the median Down coordinate of the frame's sampled true ground points. The median is robust to outliers. A tilted per-frame plane belongs to the slope experiment (H4), not to this mode. `relative_altitude` fixes the plane at the first usable frame's oracle height.

**D-211 Plane diagnostics for H4 (Section 7.6).** Two diagnostics are compared with the deployed flat oracle plane, binned by local slope. (a) `tilted_plane`: one robust plane per frame through the true ground points. It is fitted by least squares, residuals beyond 3 scaled MADs (1.4826 × MAD) are trimmed, and the fit is repeated up to three times. That is a standard robust trimming rule; it is not tuned. (b) `local_slope`: one plane per sample, using the sample's patch-averaged true normal, anchored at the frame medoid. The medoid is the sampled true ground point nearest the coordinate-wise median, so the anchor lies on the terrain; a plain median of 3D points need not. Both use true geometry, so they show how much of the error the flat-ground assumption explains. They are not deployable methods. Tests: exact on synthetic single-plane terrain.

**D-212 Mid-Air sensor-noise sweep (`{{SENSOR_NOISE}}`).** Section 7.5 says to sweep and report. There are three levels (low, mid, high) in `configs/uncertainty.yaml`:
- pixel noise 0.5, 2 and 5 px;
- height noise 0.1, 0.5 and 2 m;
- roll, pitch and yaw noise 0.1°, 0.5° and 2° each;
- camera-tilt noise 0.1°, 0.5° and 2°;
- focal-length noise 0.25 %, 1 % and 4 %.

They span sub-degree to multi-degree attitude error. They are experimental design, not claims about any sensor. **No headline value is chosen here.** Section 8.5 derives data-driven altitude and attitude noise from AU-AIR hover segments; until then, Mid-Air results are reported per sweep level. Pixel noise is per pixel; all other noise is drawn once per frame, because a sensor error is shared by every pixel in that frame.

**D-213 Bin reporting rule.** A bin is reported only with at least 100 samples (`{{MIN_SAMPLES_PER_BIN}}`) and samples from at least 3 trajectories (new placeholder `{{MIN_GROUPS_PER_BIN}}`). At 100 samples, a 90th percentile rests on 10 samples above it. Intervals resample whole trajectories, so fewer than 3 gives no meaningful interval. Unreported bins stay in the CSV tables with `reported = false`. Bin edges are listed in `scripts/midair_analyse.py`: finer near the horizon, and roughly logarithmic in range.

**D-214 Noise-induced error as the H2 test.** The Mid-Air error is terrain error plus sensor-noise error. To test the error-propagation predictions themselves, H2 compares the *noise-induced* change in range (noisy estimate minus noise-free estimate) with the first-order and Monte Carlo predicted medians (0.6745 σ, the median absolute value of a zero-mean Gaussian). Total error, with terrain included, is reported separately, along with the calibration of the predicted σ against it (H3).

## Phase 3 preparation (VisDrone)

**D-301 Matching threshold.** IoU ≥ 0.5 (`{{IOU_MATCH}}`), the MOTChallenge convention. The citation (Milan et al., 2016) is to be verified before the brief.

**D-302 Evaluation groups and ignored regions.** As in Section 9.1: person = pedestrian and people (1, 2); vehicle = car, van, truck and bus (4, 5, 6, 9); "others" (11) is excluded. Predictions whose box centre lies inside an ignored region (category 0) of that frame are removed before scoring. Ground truth is written per group in MOTChallenge format by `scripts/visdrone_prep.py --mot`. Counts per split are in `results/visdrone/prep.json`.

**D-303 Detector training labels.** Ten classes, categories 1 to 10, become YOLO class ids 0 to 9. That keeps the original classes, as Section 9.1 allows, and they are mapped to the two groups at evaluation. Ignored regions and "others" are not written as labels. The image pixels inside ignored regions are left unchanged, so the detector may see unlabelled objects there as background. Masking those pixels is an alternative, considered for the fine-tuning ablation if it matters. Images are hard-linked, not copied. After removing ignored regions and "others", and after the leakage exclusion in D-308, the set has 6,414 train images (338,285 boxes) and 527 val images (37,135 boxes).

**D-304 Data layout.** Luke reorganised `Data/` into `VisDrone-MOT/` and `VisDrone-DET/` on 2026-10-19, and the config now has `visdrone_mot_subdir` and `visdrone_det_subdir`. `Data/annotations/` and `Data/images/` (1,610 files each) duplicate `VisDrone2019-DET-test-dev` by file name. They are unused and were left untouched for Luke to decide. DET test-dev is not needed by Section 4.1 and is not used.

**D-305 Matplotlib.** Version 3.11.2, under the Matplotlib licence (BSD-style, based on the PSF licence). Figures use the validated reference palette's first three categorical slots, which pass the colour-vision checks across all pairs. Each figure has a CSV table beside it.

**D-215 `{{N_BOOT}}` = 1000 and `{{N_MC}}` = 1000.** These come from the stability check in `results/midair/development/stability.json`.
- Bootstrap: the interval endpoints of the oracle-plane median absolute relative error move by at most 1 % of the interval width between 1000 and 2000 resamples (3.5 % at 250).
- Monte Carlo: the per-sample range sigma changes by a median 1.8 % between 1000 and 2000 draws (95th percentile 6.1 %), consistent with the theoretical 1/√(2n).
- With only 6 development trajectories the intervals themselves are wide, so the remaining downloads matter more than more resamples.

**D-306 py-motmetrics with NumPy 2.** py-motmetrics 1.4.0 `distances.iou_matrix` calls `np.asfarray`, which NumPy 2 removed. The library is not patched. `aerialrange.track.evaluate.iou_distance` computes the IoU distance instead (tested), and only motmetrics' accumulator and metrics are used. Ultralytics installed `lap` 0.5.13, its tracker assignment solver, at run time; it is now pinned. Ultralytics also depends on the full `opencv-python`, which coexists with `opencv-python-headless` at the same version. Lockfiles: `requirements-lock.txt` holds the core, analysis and dev closure that CI installs (no torch); `requirements-train-lock.txt` holds the full environment, with the PyTorch CPU index.

**D-307 Detector family, sizes and input sizes.** YOLO26 (`{{DETECTOR_FAMILY}}`) is the newest family documented in the installed Ultralytics 8.4.182, which also ships a P2 small-object variant (`yolo26-p2.yaml`). Sizes n and s (`{{DETECTOR_SIZES}}`), for the CPU budget. Input sizes 640, 960 and 1280 (`{{INPUT_SIZES}}`): the library default, a midpoint, and close to native MOT val width (1344 px). Trackers are the library's ByteTrack and BoT-SORT with their default parameters; tuning happens later on validation only (`{{TRACKER_GRID}}`). BoT-SORT has re-identification off by default (`with_reid: False`). Camera-motion compensation is compared as BoT-SORT `gmc_method: sparseOptFlow` (`configs/trackers/botsort_cmc.yaml`) against `none` (`botsort_nocmc.yaml`); ByteTrack has no compensation. Ultralytics is AGPL-3.0, consistent with this repository's licence (D-005, risk R8).

**D-308 VisDrone DET and MOT overlap: the claim in Section 4.1 does not hold.** Results are in `results/visdrone/overlap.json`, from `scripts/visdrone_overlap.py`.
- **Provenance.** Both naming schemes carry the source video number (DET `0000201_00182_d_…`, MOT `uav0000201_00000_v`). By that number, 57 DET-train images (videos 137, 182, 201, 297, 305 and 339) and 21 DET-val images (videos 86, 117 and 249) come from videos that also supply MOT val or test-dev clips. A further 448 train and 106 val DET images share videos with MOT train, which is harmless for MOT evaluation.
- **Content.** 64-bit average hashes of every DET image against every 5th MOT frame give 610 matches within 4 bits, but only 157 of them come from the same video. The hash alone is therefore unreliable. One same-video pair was inspected by eye (DET `0000201_00182_d_0000172` against test-dev `uav0000201_00000_v` frame 91): it is the same scene a moment apart. One different-video pair was also inspected (DET-val `0000276_02001_d_0000517` against MOT train `uav0000239_12336_v` frame 46): different places that share only a sky-over-road layout.
- **Action.** The 57 + 21 images are excluded from detector training and model selection, which is 1.1 % of DET train and val. MOT val and test-dev therefore share no source video with the detector's training or selection data. DET test-dev is not used anywhere.

**D-309 Detection AP.** Our own implementation (`aerialrange.detect.evaluate`, tested): COCO-style greedy matching and 101-point interpolated AP, per evaluation group, with size bins on box height. Out-of-bin ground truth and unmatched out-of-bin detections are ignored, as COCO does for area ranges. It is needed because the zero-shot COCO model (B0) and the fine-tuned VisDrone model (B2) have different class sets, so both are scored on the person and vehicle groups.

**D-310 Tiled inference (B3).** Square tiles with fractional overlap; the last tile in each row and column is aligned to the image edge; class-wise NMS merges duplicates. Tile size and overlap are new placeholders (`{{TILE_SIZE}}`, `{{TILE_OVERLAP}}`), chosen on validation when B3 runs.

**D-311 Flag operating point and usable limits (Section 7.7).** The flag threshold `{{REL_UNC_THRESHOLD}}` is chosen on the calibration split by maximum F1. That rule has no free parameter, which a target-recall rule would. `{{MIN_DEPRESSION_DEG}}` and `{{MAX_RANGE_M}}` use the same rule: the edge where the upper 95 % bound of the binned median absolute relative error (noisy mode, development split) reaches `{{ERR_THRESHOLD_FRAC}}`. One definition of "large error" therefore drives the flag, the limits and the precision/recall labels. `{{ERR_THRESHOLD_FRAC}}` is still to be chosen, from the sweep 0.05, 0.1, 0.2 and 0.5 (BLOCKED.md). Script: `scripts/midair_calibrate.py`.

**D-312 Detection size bins.** Box-height bins of 0–16, 16–32, 32–64, 64–128 and 128+ px. Each bin doubles the previous one; small objects dominate VisDrone, and Section 9.2 asks for AP by size. Detection AP on MOT frames uses every 10th frame of each sequence, because neighbouring frames are near-duplicates (`scripts/detect_eval.py`).

**D-313 Edge tooling.** onnx 1.23.2 (Apache-2.0), onnxruntime 1.31.0 (MIT) and onnxslim 0.1.98 (MIT), pinned in `requirements-train-lock.txt`. `scripts/export_onnx.py` always reports the actual maximum box and score differences and the detection agreement on a seeded sample of MOT val frames. It compares against `{{PARITY_TOL}}` only once that value is set with a justification.

## Luke's decisions, 2026-10-19

**D-314** (each item below is Luke's decision):
- (a) `{{ERR_THRESHOLD_FRAC}}` = 0.1. A range estimate more than 10 % wrong counts as a large error. This is a stated choice that can be changed, and the full curves for 5, 10, 20 and 50 % are always reported.
- (b) Detector fine-tuning (B2) runs on a cloud GPU: free Kaggle first, paid if needed. Luke uploads the package himself as a private dataset (`docs/gpu_training.md`, `gpu/train_b2_kaggle.py`). The package is `cache/gpu_package/visdrone_yolo.zip`, with its SHA-256 recorded in `manifest.json`.
- (c) The D-308 exclusion of 78 overlapping DET images is approved.
- (d) `{{MOT17_REPO_PATH}}` is https://github.com/LukeA77/MOT_Tracking at commit 455e702. Its `outputs/metrics.json` is copied to `results/mot17_reference/metrics.json` with provenance, for the domain-gap comparison. The repository holds no weights, so B1 needs Luke's trained `.pt` file if he still has it.
- (e) `Data/annotations/` and `Data/images/` were verified as byte-identical copies of DET test-dev (all 3,220 files), and Luke will delete them.
- (f) The uncertainty-model problem (H3) is **not** to be reported as a dead end. Find a solution; options are under discussion.

**D-315 Training schedule for B2 (`{{TRAIN_HYPERPARAMS}}`).** The library defaults (100 epochs, early-stopping patience 100) are changed to at most 50 epochs with patience 10, plus `cache="ram"`. Reasons:
- Fine-tuning from pretrained weights converges well before 100 epochs.
- Luke's GPU quota is 30 hours a week.
- Early stopping on DET val is allowed by Section 4.5.
- Luke's MOT17 run used 30 epochs.
- RAM caching only removes JPEG-decoding stalls; it does not change what is learned.

The first Kaggle attempt took about 1 hour per epoch, the same as the local CPU probe, which suggests the GPU was not active. The script now refuses to run without a GPU. Everything else stays at library defaults.

## Terrain-aware ranging (Luke's plan D + E + B + C, 2026-10-19)

This goes beyond build.md Section 6.3, at Luke's request (D-314 f). The flat-ground method stays as the baseline, so that "flat versus terrain-aware" is reported side by side.

**D-401 Terrain from motion (D).**
- Corners in frame k (Shi-Tomasi) are tracked to earlier frames k − g (pyramidal Lucas-Kanade, kept only if the forward-backward error is below 1 px).
- Each track is triangulated with the two known camera poses (midpoint method, `geometry/triangulation.py`, test-first, matching the stereo depth-sigma oracle).
- **Per-feature baseline choice.** Every corner is triangulated against each gap in (1, 2, 5, 10), and the estimate with the smallest total position variance (trace of the covariance) is kept. Exploration on development trajectory 0002 showed a single 5-frame gap loses near ground: fast image motion breaks tracking, the support radius grows to about 8 m, and steep views reach 8 % error, against 2 % with gaps of 1–2. Distant ground prefers longer gaps. Selecting by Down variance alone was rejected, because shallow rays hide their error along the nearly horizontal line of sight.
- Each target ray is intersected with a robust local plane height field fitted to its k = 30 nearest triangulated points (`geometry/terrain.py`). The neighbourhood size adapts to point density instead of using a fixed radius.
- The method uses only images and poses: no segmentation, depth or height above ground.
- Detector and tracker settings are common OpenCV values, not tuned (`configs/geometry.yaml`, `terrain_motion`).

**D-402 Tracking noise (`{{TERRAIN_SIGMA_PX}}`).** Measured on the development split (`scripts/measure_tracking_noise.py` → `results/midair/development/tracking_noise.json`). For each corner, the true 3D point (from radial depth, at locally smooth depth only) is projected into the earlier frame and compared with the tracked position. The robust sigma (mean of u and v, from 1.4826 × MAD) is used per gap. The tracker has a small core error with a heavy tail (90th-percentile errors are several times the core sigma). The core sigma drives the triangulation covariance; the tail is left to the conformal calibration (D-403), not hidden in a guessed number.

**D-403 Calibrated intervals (B).** Split conformal prediction (Vovk, Gammerman and Shafer, 2005; Lei et al., 2018), in `evaluate/conformal.py`. The score is |error| / sigma. The multiplier for level p is the ceil((n + 1) p)-th smallest calibration score, globally and per viewing-angle band ("Mondrian" conformal, with a global fallback for small bands). It is fitted on the calibration split and applied once to the test split. **Caveat:** samples within a trajectory are correlated, so the exchangeability guarantee is weaker than for independent samples. Coverage is therefore verified empirically on the test split, never assumed. References to be verified before the brief.

**D-404 Reliability flag (E).** L2-regularised logistic regression on a few interpretable per-estimate features (`evaluate/flag.py`), fitted on the calibration split only, with its coefficients reported. The L2 weight is a new placeholder (`{{FLAG_L2}}`), set before seeing test data.

**C (car-size cross-check)** is not built yet. Mid-Air has no vehicles, so it can only be evaluated on real footage (AU-AIR, not yet available).

**D-316 Detection cap (`max_det` = 1000).** The Kaggle training log reported VisDrone DET images with up to 902 objects (train) and 317 (val). The library default cap of 300 per image would cut recall in crowded frames, so every local inference (detection AP, tracking, pixel-noise fit) now uses 1000, set in `configs/detector.yaml`. B0 and B2 were re-scored with it, so they are compared under the same cap. B0 scores did not change: the zero-shot model never reached 300 detections.

**D-405 Image-space support for the terrain fit.** The development run with world-space k-nearest support (15 trajectories) showed a large-error tail: about 13 % of valid land estimates more than 50 % off. Almost all were large underestimates (median estimate/truth about 0.12), with support radius about 1.6 times the estimated range against 0.2 for good estimates. The iteration had locked onto a near, steep patch that the ray meets too early. Alternatives were compared on development trajectories 0003, 0016 and 0029, using every 4th evaluated frame (`cache/logs/neighbours_compare*.log`):
- **world** (k nearest in 3D around the ray): share of estimates more than 50 % off was 39 % / 3 % / 34 %, median 8.7 % / 1.2 % / 18 %.
- **image** (the k triangulated features nearest the target pixel, i.e. the patch the camera sees around the target): 13 % / 4 % / 14 %, median 6.1 % / 1.5 % / 5.6 %.
- **image then world** (image patch, then a world refinement): 9 % / 4 % / 19 %, median 4.7 % / 1.3 % / 11 %.

Image support is the most consistent: no trajectory fails badly. It is now the setting (`neighbours: image`). The refinement sometimes returns to the wrong patch and is not used. The full development rerun with image support replaces the earlier world-support numbers.

**D-317 Tiling with a full-frame pass (B3).** The first tile-only setting on MOT val (tile 480, overlap 0.2) raised small-object AP50 (vehicle 16–32 px: 0.345 against 0.266) but lowered overall AP50 (vehicle 0.477 against 0.587), because objects larger than a tile are split across tiles. `detect_tiled(..., include_full=True)` also detects the whole frame and merges it with the tiles through class-wise NMS, the usual remedy in sliced inference. It is tested with an object that no tile contains. Tile size and overlap are chosen on validation only, from the sweep in `cache/logs/overnight.log`.

**D-318 Tile merging by intersection over smaller area.** Tiled tracking (B3) on val was worse than untiled tracking (IDF1 vehicle 0.425 against 0.586), with precision falling from 0.69 to 0.52 and identity switches doubling. The cause: fragments of an object cut at a tile edge overlap the full detection with low IoU, so plain NMS keeps them. `nms(..., ios_thr)` also suppresses a lower-scoring box when at least `ios_thr` of the smaller box lies inside the kept box (intersection over smaller area, the merge criterion used by sliced-inference tools such as SAHI). It is tested on a tile-edge fragment and on adjacent separate objects. The threshold is chosen on val from {0.5, 0.8} (new placeholder `{{TILE_IOS}}`).
