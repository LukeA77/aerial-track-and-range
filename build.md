# BUILD.md: aerial tracking and ranging showcase

**Status:** version 1.0, written 18 October 2026.
**Reader:** Claude, working as an autonomous build agent.
**Owner:** Luke (human, final decision-maker).

---

## 0. How to work from this file

Read this whole file before writing any code. Then:

1. Create `PROGRESS.md` (running log of what was done and measured), `BLOCKED.md` (items that need Luke) and a task list that mirrors Section 12.
2. Work through the phases in Section 12 in order. Each phase has exit criteria. Do not start a later phase until the exit criteria of the earlier one are met, unless a phase is marked parallelisable.
3. Commit after every milestone with a message in the form `phase-N: short imperative summary`.
4. Never push to a public remote, publish anything, or contact anyone. Prepare everything locally and tell Luke what is ready.
5. When a phase depends on something only Luke can supply (a dataset download, a file path, a decision), write it into `BLOCKED.md`, then carry on with every task that does not depend on it. Use synthetic data and mocks to keep working, and label them clearly as synthetic.

### Non-negotiable rules

| ID | Rule |
|----|------|
| R1 | **No invented numbers.** Every figure in a README, brief, figure caption or video comes from a results file produced by code in this repository. If a value has not been computed, show a placeholder, never an estimate. |
| R2 | **No invented parameters.** When a value is unknown, resolve it in this order: (a) measure it from data; (b) read it from a primary source and record the citation next to the value in the config; (c) ask Luke through `BLOCKED.md`. Unresolved values appear as `{{PLACEHOLDER}}` (Section 3). |
| R3 | **Public data only.** No confidential, personal or proprietary material. No faces, no biometric identification, no re-identification of individuals across scenes. People and vehicles are tracked as bounding boxes only. |
| R4 | **Tests first for geometry.** The geometry package (Section 6) is built test-first. Frame conventions and signs are pinned by tests, not by comments. |
| R5 | **No tuning on test data.** Follow the split table in Section 4.5. The final test run happens once, after all configuration is frozen. |
| R6 | **Report limits as prominently as results.** Failure cases, invalid estimates and untested regimes go in the brief, not only in an appendix. |
| R7 | **Data and model weights are never committed.** They are listed in `.gitignore`. Small results files (JavaScript Object Notation, JSON; comma-separated values, CSV; and figures) are committed. |
| R8 | **Scope discipline.** Only the three pillars in Section 2 are in scope. Items tagged `[EXTRA]` are optional and may be started only after the exit criteria of every phase up to Phase 5 are met. Items in Section 15 ("Out of scope") are not to be built. |
| R9 | **No weapons framing.** This is a perception and measurement project. Do not use targeting, engagement or fire-control language in code, docs or the video. |
| R10 | **Writing standards in Section 13.1 apply to all prose** (README, docs, brief, comments in documents, cover note). |

---

## 1. Purpose, audience and positioning

Luke is a recent MSc graduate (computer vision, robotics, machine learning) with no professional work experience. He met an engineer from a UK defence electro-optical tracking company at a careers fair. The company has no vacancy, but the engineer said that showing relevant work might earn him a chance. This repository is that work: a portfolio project that shows he can build, evaluate and honestly report a perception system of the kind such a company builds.

**Audience for the finished repository:** senior engineers who build Electro-Optical (EO) and Infrared (IR) surveillance and tracking systems. They are technical and time-poor. They value honest evaluation, failure analysis, reproducibility, real-time performance on modest hardware, and clear statements of assumptions. They are unimpressed by leaderboard numbers on their own.

**Positioning sentence** (use this idea, in your own wording, in the README and brief): *Tracking from a drone that reports where things are, how far to trust that, and does it in real time on a Central Processing Unit (CPU).*

**Public repository hygiene:** do not name the company in any repository file except `docs/cover_note.md` (a draft message for Luke to edit). Do not use the company's name, logos or product names anywhere else, and do not imply endorsement.

---

## 2. What we are building: three pillars

**Pillar A: aerial Multi-Object Tracking (MOT) baseline** on the VisDrone benchmark. Detect and track people and vehicles in Unmanned Aerial Vehicle (UAV) footage. This is the foundation, and the part closest to what the employer showed Luke. Used as a yardstick, not as the point of the project.

**Pillar B: ground-plane ranging with honest uncertainty.** For each tracked object, estimate range and bearing from the drone using the camera geometry and flight metadata, with an error bar. Validate accuracy against ground truth in the synthetic Mid-Air dataset, then run on real AU-AIR footage with consistency checks. This is the headline contribution.

**Pillar C: edge latency budget.** Export to Open Neural Network Exchange (ONNX) format, quantise, and report per-stage latency on a CPU against a stated real-time budget. Shows the whole pipeline is deployable.

### Pipeline

```
video frame ─► detector ─► tracker ─► ground-plane ranging ─► ground-plane Kalman filter ─► track table + overlay
                             ▲                 ▲
                             │                 └── flight metadata: altitude, attitude, position, camera model
                             └── camera-motion compensation
```

### Hypotheses to test (report the outcome whichever way it goes)

| ID | Hypothesis | How it is falsified |
|----|-----------|---------------------|
| H1 | Off-the-shelf detector and tracker degrade on aerial footage; fine-tuning, tiled inference and camera-motion compensation recover part of the loss. | Compare baselines B0 to B3 (Section 9.2) on VisDrone validation and test-dev. |
| H2 | Ground-plane ranging error grows with range and with shallower depression angle, as error propagation predicts. | Binned error curves on Mid-Air versus first-order and Monte Carlo predictions. |
| H3 | The propagated uncertainty is calibrated, or can be made so with one scalar, and a reliability flag catches the worst errors. | Coverage, z-score spread and flag precision/recall on held-out Mid-Air trajectories. |
| H4 | The flat-ground assumption breaks on sloped terrain, and error grows with local slope. | Error binned by local surface slope in Mid-Air. |
| H5 | The full pipeline meets the real-time budget on a CPU at an operating point with a small accuracy cost. | Latency and accuracy Pareto study (Section 10). |

---

## 3. Placeholders and unknowns

Every `{{NAME}}` below must live in a `configs/*.yaml` file as `null` until resolved. The config loader must raise a clear error if a required value is `null` when a command needs it. Record the source and date of each resolved value next to it. Do not guess defaults.

| Placeholder | Meaning | How to resolve | Who |
|-------------|---------|----------------|-----|
| `{{REPO_NAME}}` | Repository and package name | Suggest `aerial-track-and-range`; package `aerialrange`. Avoid names that imply target recognition or weapons. | Luke confirms |
| `{{PYTHON_VERSION}}` | Python version | Latest stable version supported by every dependency at build time | Claude |
| `{{LICENCE}}` | Licence for Luke's code | See risk R8 in Section 14 (Ultralytics is under the GNU Affero General Public License, AGPL-3.0). Present the options; Luke decides. | Luke |
| `{{DATA_ROOT}}` | Directory holding downloaded datasets | Config or environment variable | Luke |
| `{{MOT17_REPO_PATH}}` | Local path to Luke's earlier MOT17 pipeline repository | Read its README for his published numbers; reuse code where sensible | Luke |
| `{{MOT17_WEIGHTS_PATH}}` | Optional weights from that pipeline | If absent, skip baseline B1 | Luke |
| `{{COMPUTE_PROFILE}}` | CPU model, core count, memory, Graphics Processing Unit (GPU) if any | `scripts/env_report.py` writes it to `results/env.json` | Claude |
| `{{TARGET_FPS}}` | Real-time target in frames per second | Propose options (for example the source frame rate of each dataset) and ask Luke to choose | Luke |
| `{{LATENCY_BUDGET_MS}}` | Per-frame budget | `1000 / {{TARGET_FPS}}` | Claude |
| `{{DETECTOR_FAMILY}}`, `{{DETECTOR_SIZES}}` | Detector model family and size variants | Choose from the library's documented options; record versions | Claude |
| `{{INPUT_SIZES}}` | Detector input resolutions to test | Choose a sensible spread; record why | Claude |
| `{{TRAIN_HYPERPARAMS}}` | Epochs, batch size, learning-rate schedule | Start from library defaults; record all changes and reasons | Claude |
| `{{TRACKER_GRID}}` | Tracker hyperparameter grid | Small grid around library defaults, tuned on validation only | Claude |
| `{{IOU_MATCH}}` | Intersection over Union (IoU) threshold for matching | Use the benchmark's standard convention; record it | Claude |
| `{{SIGMA_PIX_MODEL}}` | Box-to-pixel noise model parameters (`κ_u`, `κ_v`) | Fit from detector versus ground-truth box errors on VisDrone validation (Section 6.3) | Claude |
| `{{SENSOR_NOISE}}` | Altitude, attitude, camera-tilt and focal-length noise (`σ_h`, `σ_att`, `σ_tilt`, `σ_f`) | AU-AIR: estimate from hover segments (Section 8.5). Mid-Air: sweep and report; headline values must be justified in `docs/decisions.md`. | Claude |
| `{{FOCAL_PX_AUAIR}}`, `{{DIST_COEFFS_AUAIR}}` | AU-AIR camera intrinsics and lens distortion | Section 8.3 (specification lookup plus self-calibration), with uncertainty | Claude |
| `{{CAMERA_TILT_DEG_BY_CLIP}}` | Camera tilt per AU-AIR clip | Section 8.2 (contact sheets, Luke labels) and 8.3 | Luke + Claude |
| `{{OBJ_HEIGHT_M_BY_CLASS}}` | Reference object heights for the height-aware contact point | Cite a public source per class; sensitivity analysis required | Claude |
| `{{CAR_LENGTH_PRIOR_SOURCE}}` | Source for a vehicle-length prior (a distribution, not one number) | Cite a public source; used only for AU-AIR scale self-calibration | Claude |
| `{{MIDAIR_CLIMATE}}` | Mid-Air climate subset to download | One climate is enough for geometry validation (Section 7.1) | Claude proposes, Luke downloads |
| `{{N_TRAJ_MIDAIR}}` | Number of Mid-Air trajectories | As many as time and disk allow; split by trajectory (Section 4.5) | Claude |
| `{{MIDAIR_SPLIT}}` | Trajectory split proportions (development, calibration, test) | Propose and document in `docs/decisions.md` | Claude |
| `{{PIX_PER_FRAME}}`, `{{FRAME_STRIDE}}`, `{{EDGE_MARGIN_PX}}` | Mid-Air pixel sampling parameters | Choose so strata have enough samples; document | Claude |
| `{{MIN_SAMPLES_PER_BIN}}` | Minimum samples for a reported stratum | Choose with a justification; apply everywhere | Claude |
| `{{MIN_DEPRESSION_DEG}}`, `{{MAX_RANGE_M}}` | Validity limits for ranging | Derive from where error propagation becomes unusable (Section 7.7); do not pre-set | Claude |
| `{{REL_UNC_THRESHOLD}}`, `{{ERR_THRESHOLD_FRAC}}` | Reliability-flag threshold and "large error" definition | Sweep and report the full precision/recall curve, then fix one operating point on the calibration split | Claude |
| `{{NADIR_THRESHOLD_DEG}}` | Tilt above which the straight-down contact-point rule is used | Derive from the contact-point analysis (Section 6.2) | Claude |
| `{{CENTRAL_FRACTION}}` | Central image region trusted on AU-AIR (lens distortion) | From the distortion analysis (Section 8.3) | Claude |
| `{{AUAIR_CALIB_CLIPS}}` | AU-AIR clips used for camera-model calibration (the rest are held out) | Choose before looking at held-out results; record | Claude |
| `{{STATIONARY_PX_THRESHOLD}}`, `{{STATIONARY_MIN_S}}` | Definition of a stationary target | Set from the noise level of the camera-motion estimate; document | Claude |
| `{{HOVER_SPEED_MS}}`, `{{HOVER_MIN_S}}` | Definition of a hover segment | Set from the flight-data noise level; document | Claude |
| `{{N_MC}}`, `{{N_BOOT}}` | Monte Carlo draws and bootstrap resamples | Large enough that results are stable to the reported precision; show the check | Claude |
| `{{KALMAN_Q}}` | Process noise for the ground-plane filter | Tune on the development split only | Claude |
| `{{N_TIMED_FRAMES}}`, `{{N_WARMUP}}`, `{{N_REPEATS}}`, `{{THREADS_SET}}` | Benchmark protocol sizes | Choose to give stable percentiles; document | Claude |
| `{{PARITY_TOL}}` | Tolerance for ONNX versus original numerical parity | Choose, justify, and report the actual difference | Claude |
| `{{VOICE_SAMPLE}}` | Path to a sample of Luke's own writing | `docs/voice_sample.md` | Luke |
| `{{MAX_VIDEO_MB}}`, `{{VIDEO_LENGTH_S}}` | Demo video limits | Ask Luke; target 60 to 90 seconds | Luke |
| `{{ABSTRACT_WORDS}}` | Abstract length limit | Fixed by the two-page limit; set once the layout is known | Claude |
| `{{N_LANDMARKS}}` | Number of landmark pairs for the optional scale check | Only for `[EXTRA]` E3 | Luke |
| `{{RESULT:name}}` | A value inserted into documents from a results file | Filled by `scripts/fill_docs.py`; the release check fails if any remain | Claude |

### Items that need Luke (write these into `BLOCKED.md` at the start)

1. Download the datasets (Section 4) into `{{DATA_ROOT}}`. The shell in Claude's workspace may not reach the dataset hosts; if a download fails, say so plainly, do not retry with workarounds, and ask Luke to download manually.
2. Provide `{{MOT17_REPO_PATH}}` (and optionally `{{MOT17_WEIGHTS_PATH}}`).
3. Choose `{{TARGET_FPS}}`, `{{LICENCE}}` and `{{REPO_NAME}}`.
4. Provide a writing sample for voice matching.
5. Label AU-AIR clip tilt categories from contact sheets (Section 8.2). This takes minutes.
6. Optional: measure landmark distances on a public map for `[EXTRA]` E3.

---

## 4. Datasets

Download only what is needed. Never commit data (R7). Record file names, sizes and checksums in `docs/data_cards.md`. Check licences and terms yourself on each dataset page at build time and record what you find.

### 4.1 VisDrone (Pillar A)

- **What:** drone-captured benchmark; the official repository describes 288 video clips (261,908 frames) and 10,209 static images from 14 Chinese cities, with more than 2.6 million bounding boxes (pedestrians, cars, bicycles, tricycles and others).
- **Where:** official repository `https://github.com/VisDrone/VisDrone-Dataset` (links to Google Drive and Baidu).
- **Needed:** the multi-object tracking set (training, validation, test-dev with ground truth) and the image detection set (training, validation). Per the VisDrone papers, the static images do not overlap with the video clips; verify this claim by checking for duplicate content or file provenance, and record the result.
- **Do not use** the challenge test sets (annotations withheld).
- **Annotation format (from memory, verify against the real files):** one text file per sequence with comma-separated columns: frame index, target identifier, box left, box top, box width, box height, score, object category, truncation, occlusion. Object category 0 marks ignored regions. Categories 1 to 11 are pedestrian, people, bicycle, car, van, truck, tricycle, awning-tricycle, bus, motor, others. Write a schema check that fails loudly if the real files differ.
- **Licence and terms:** not stated in the repository page I read. Check the terms and do not redistribute the data.

### 4.2 AU-AIR (Pillar B, real footage)

- **What (verified from the paper and dataset page):** Parrot Bebop 2 quadrotor; 1920×1080 video at 30 frames per second; eight clips (about two hours) recorded at one junction in Aarhus, Denmark; frames extracted at five per second giving 32,823 labelled frames and 132,034 object instances; eight classes (person, car, van, truck, motorbike, bike, bus, trailer). Flight altitude between 5 and 30 metres (mostly 10, 20 and 30), camera angle between 45 and 90 degrees (90 is straight down). Sensor data logged every 20 milliseconds.
- **Per-frame flight data:** date, time stamp, latitude, longitude (Global Positioning System, GPS), altitude (from an altimeter, stated in **millimetres**), roll, pitch and yaw from the Inertial Measurement Unit (IMU, in radians), and velocities along three axes (metres per second).
- **Where:** `https://bozcani.github.io/auairdataset` (frames about 2.2 GB, annotations about 3.9 MB). A Python helper package is linked from the page; the repository URL I tried returned an error, so search for it, and do not depend on it. Write your own loader.
- **Licence:** Creative Commons Attribution (CC BY). Credit the authors: Bozcan and Kayacan (2020), AU-AIR, IEEE International Conference on Robotics and Automation.
- **Known gaps (important):**
  - No camera intrinsics are listed.
  - The logged angles are the drone body's, not the camera's tilt. The tilt was set per recording and is not a per-frame field.
  - I believe the Bebop 2 camera has a wide-angle lens with digital stabilisation. This is unverified and affects the geometry (Section 8.3).
  - Annotations are bounding boxes and class labels. No track identities, and no true distance to objects.
  - The annotation JSON schema was not inspected. Write a schema-discovery script first (Section 8.1) and do not assume field names.
- **Frame rate note:** frames are extracted at five per second, so inter-frame motion is large. Configure trackers accordingly.

### 4.3 Mid-Air (Pillar B, ground truth)

- **What (verified from the dataset pages):** synthetic low-altitude drone flights; 54 trajectories (79 minutes), more than 420,000 frames, rendered in several climates (four weather setups, three seasons) over three maps.
- **Sensors:** three red-green-blue (RGB) cameras (left, right, down) at 25 Hz. Per-pixel ground truth for the **left** camera only: depth (metres, 16-bit float stored in single-channel Portable Network Graphics, PNG), surface normals (expressed in the body frame), semantic segmentation, stereo disparity and occlusion. All cameras share one intrinsic matrix: `fx = cx = w/2`, `fy = cy = h/2`, which is a 90-degree field of view.
- **Frames:** North, East, Down (NED) convention. World frame origin is the trajectory start with yaw zero. Body frame origin is the IMU and GPS position. Units are metres, radians, seconds, rotations as quaternions.
- **Positioning data:** ground-truth position, velocity, acceleration and attitude (quaternion) at 100 Hz in the world frame; angular velocity in the body frame; IMU at 100 Hz; GPS at 1 Hz, **given in metres in the world frame** (not latitude and longitude).
- **Storage:** images in per-climate directories (`color_left`, `depth`, `segmentation`, `normals` and others, each with `trajectory_i/j.ext`), plus one `sensor_records.hdf5` per climate (Hierarchical Data Format 5, HDF5). Inside, one group per trajectory with `camera_data` (frame paths, index `floor(25 t)`), `gps`, `groundtruth` (index `floor(100 t)`) and `imu`.
- **Segmentation classes:** 1 animals, 2 trees, 3 dirt ground, 4 ground vegetation, 5 rocky ground, 6 boulders, 8 water plane, 9 man-made construction, 10 road, 11 train track, 12 road sign, 13 other man-made objects.
- **Where:** `https://midair.ulg.ac.be` (download page has a selective downloader; example scripts at `https://github.com/montefiore-ai/midair-dataset`).
- **Licence:** Creative Commons Attribution-NonCommercial-ShareAlike 4.0 (CC BY-NC-SA 4.0). Attribute, cite Fonder and Van Droogenbroeck (2019), do not redistribute the data, and do not publish derived datasets under an incompatible licence. Publishing code, metrics and figures is fine.
- **Known unknowns (resolve by test, Section 7.3):** the camera mounting orientation relative to the body; whether depth is planar (distance along the optical axis) or radial (distance from the camera centre); the quaternion component order and convention. Read the example scripts first.
- **Limitation:** no people or vehicles. Mid-Air validates the **geometry**, using ground pixels, not the detector or tracker.

### 4.4 Data policy

Place data under `{{DATA_ROOT}}`. Write `scripts/check_data.py` that verifies presence, counts and schemas of each dataset and prints a clear report. Every loader must work on a small synthetic fixture so that tests run without the real datasets.

### 4.5 Splits (no leakage)

| Dataset | Use | Split |
|---------|-----|-------|
| VisDrone detection | Train detector | Official training set |
| VisDrone detection | Choose detector settings, early stopping | Official validation set |
| VisDrone MOT | Tune tracker, fit pixel-noise model | Official validation set |
| VisDrone MOT | Final reported numbers | Test-dev, run **once** after freezing |
| Mid-Air | Choose sampling parameters, camera mounting offsets, filter noise | Development trajectories |
| Mid-Air | Fit the single recalibration scalar | Calibration trajectories |
| Mid-Air | Final accuracy and calibration results | Test trajectories |
| AU-AIR | Camera-model calibration (Section 8.3) | `{{AUAIR_CALIB_CLIPS}}` |
| AU-AIR | Repeatability results | All other clips (held out) |

Split Mid-Air **by trajectory** (all climates of one trajectory go in the same split), using a fixed seed and the proportions in `{{MIDAIR_SPLIT}}`. Write the split to `results/splits.json`. Because Mid-Air frames within a trajectory are strongly correlated, every confidence interval must use a bootstrap that resamples whole trajectories.

---

## 5. Engineering standards

- **Language and packaging:** Python `{{PYTHON_VERSION}}`, `pyproject.toml`, package `src/aerialrange/`. Extras: `dev`, `train`, `edge`. Pin dependency versions in a lockfile chosen at build time; do not rely on version numbers remembered from training data.
- **Suggested libraries (verify availability and licences):** NumPy, SciPy, OpenCV (headless), pandas, h5py, Matplotlib, PyYAML, Typer (command-line interface, CLI), tqdm, pytest, ruff, ONNX, ONNX Runtime, Ultralytics (detector and trackers), py-motmetrics and, if time allows, TrackEval (for Higher Order Tracking Accuracy, HOTA). Implement the Kalman filter yourself (small and testable).
- **Quality gates:** ruff clean; type hints on public functions; every public geometry function has unit tests; tests run in continuous integration (CI) on synthetic data only (no datasets, no GPU).
- **Style:** pure functions for geometry (no file input or output). Name frames explicitly in variables: `p_w` (position in world), `R_wb` (rotation from body to world), `R_bc` (camera to body). Every function that takes or returns a physical quantity states the unit in its docstring. No magic numbers; constants live in configs with a source.
- **Determinism:** fixed seeds, recorded in every results file together with the git commit and a config hash.
- **Configuration:** YAML Ain't Markup Language (YAML) files in `configs/`, loaded into typed dataclasses. One command-line entry point `aerialrange` with sub-commands matching the Makefile targets below.
- **Logging:** structured logs; every long-running command prints progress and writes a results JSON with the inputs, versions and timings.
- **Licences of dependencies:** record them in `docs/decisions.md`. Flag the Ultralytics AGPL-3.0 licence (risk R8).

### Repository layout

```
{{REPO_NAME}}/
├── README.md
├── LICENSE
├── pyproject.toml
├── Makefile
├── PROGRESS.md            # agent working log (may be removed before release)
├── BLOCKED.md             # items needing Luke
├── configs/               # data, detector, tracker, geometry, uncertainty, edge
├── src/aerialrange/
│   ├── data/              # visdrone.py, auair.py, midair.py, splits.py, synthetic.py
│   ├── detect/            # train.py, infer.py, tiling.py, export_onnx.py
│   ├── track/             # runner.py, convert_mot.py, evaluate.py
│   ├── geometry/          # frames.py, camera.py, ranging.py, uncertainty.py, kalman.py, calibration.py
│   ├── evaluate/          # midair_ranging.py, calibration_metrics.py, repeatability.py, sensitivity.py
│   ├── edge/              # quantise.py, benchmark.py, pareto.py
│   ├── viz/               # overlay.py, video.py, gallery.py, plots.py
│   └── utils/             # config.py, logging.py, seeds.py, env_report.py
├── scripts/               # check_data.py, env_report.py, fill_docs.py, contact_sheets.py
├── tests/                 # unit tests; fixtures are synthetic
├── docs/
│   ├── brief/             # two-page technical brief (source and Portable Document Format, PDF)
│   ├── decisions.md       # decision log with reasons and sources
│   ├── data_cards.md
│   ├── model_card.md
│   ├── limitations.md
│   ├── faq_for_reviewers.md
│   ├── auair_camera_model.md
│   ├── auair_clip_notes.md
│   ├── cover_note.md      # draft message for Luke only
│   └── voice_sample.md    # Luke supplies
├── results/               # committed: small JSON, CSV, figures
└── .github/workflows/ci.yml
```

### Makefile targets

`setup`, `lint`, `test`, `data-check`, `midair-eval`, `auair-prep`, `auair-eval`, `visdrone-prep`, `train`, `track-eval`, `export`, `bench`, `demo`, `docs`, `all-results`.

---

## 6. Geometry and ranging specification (Pillar B core)

Build this first (Phase 1), as pure mathematics, with tests on synthetic cases whose answers are known.

### 6.1 Frames and conventions

- **World (W):** North, East, Down (NED). For AU-AIR, build a local NED frame from GPS with the origin at the first fix of each clip. Use a local tangent-plane approximation (state its validity at this scale) or a proper projection library; test it.
- **Body (B):** forward, right, down (FRD), fixed to the drone.
- **Camera (C):** OpenCV convention: x right, y down, z forward along the optical axis.
- `R_ab` rotates a vector from frame b into frame a: `v_a = R_ab v_b`.
- **Default camera mount** (forward-looking, level): camera z maps to body forward, camera x to body right, camera y to body down. Tilt `δ` is the camera depression below the horizon.
- **Pin conventions with tests, not comments.** Required tests: with a level drone, `δ = 0` puts the optical axis along body forward; `δ = 90°` puts it along body down; the principal-point pixel of a nadir camera on a level drone gives a world ray `(0, 0, 1)`. Derive the sign of the tilt rotation yourself and let the tests decide.
- **Attitude:** AU-AIR gives roll, pitch, yaw; assume the aerospace yaw-pitch-roll sequence (rotate by yaw, then pitch, then roll) and verify against the AU-AIR paper's body-frame figure and its worked example (the paper's Figure 1 gives one sample: altitude 22 m, roll 0.011 rad, pitch 0, yaw 1.26 rad). Mid-Air gives quaternions: read the example scripts for component order and active or passive convention, then pin it with a test.

### 6.2 Ray and plane intersection

Inputs: pixel `(u, v)`, intrinsic matrix `K` (and lens distortion if known), camera mount `R_bc` (and lever arm `t_bc`, default zero), drone pose (`p_w`, `R_wb`), ground-plane height.

1. Remove lens distortion if coefficients are known, otherwise state that the pinhole model is assumed.
2. Camera-frame ray: `d_c = K⁻¹ [u, v, 1]ᵀ`.
3. World-frame ray: `d_w = R_wb R_bc d_c`.
4. Camera centre in world: `C_w = p_w + R_wb t_bc`.
5. Horizontal ground plane at down-coordinate `z_g`. Height above plane `h = z_g − C_w,z` (positive when above the plane).
6. If `d_w,z` is not sufficiently positive (ray at or above the horizon), the estimate is **invalid**. Otherwise `λ = h / d_w,z` and the ground point is `P_w = C_w + λ d_w`.
7. Outputs: range `r = λ ‖d_w‖`; horizontal ground distance from the point below the drone; world azimuth (clockwise from North); azimuth relative to the drone's heading; depression angle of the ray; validity flag with a reason code.

**Contact-point rules** (which pixel represents the object on the ground):

- `bottom_centre`: bottom-centre of the bounding box. Use for oblique views.
- `centre_with_height`: for steep or straight-down views, the box centre sees the top of the object, not its ground contact. Intersect with a plane raised by the reference object height (`{{OBJ_HEIGHT_M_BY_CLASS}}`, cited per class). Choose between the two modes using `{{NADIR_THRESHOLD_DEG}}`, and show the effect of the choice in an ablation.
- Implement a general plane (normal and offset) as well, for the slope experiments in Section 7.6 only. The deployed pipeline uses the horizontal plane.

### 6.3 Uncertainty model

Parameter vector `θ`: pixel coordinates, height above plane, roll, pitch, yaw, camera tilt, focal lengths, principal point, and (for the height-aware mode) object height. Use a covariance `Σ_θ` (diagonal by default, with an option for correlated altitude and pitch).

- **Per-frame pixel noise:** model as proportional to the box size (`σ_u = κ_u · box width`, `σ_v = κ_v · box height`). Fit `κ_u`, `κ_v` from detector-versus-ground-truth errors on VisDrone validation (stored as `{{SIGMA_PIX_MODEL}}`). For Mid-Air (no boxes), sweep a fixed pixel noise and document the values.
- **First-order propagation:** `Σ_P = J Σ_θ Jᵀ` with a numerical Jacobian (central differences with parameter-scaled steps). Derive range, ground-distance and bearing uncertainty from `Σ_P`.
- **Monte Carlo cross-check:** `{{N_MC}}` draws from `Σ_θ`; report percentile intervals. Where first-order and Monte Carlo disagree materially (near the horizon), mark the regime as nonlinear and use the Monte Carlo interval.
- **Analytic test oracles** (nadir pinhole, level drone): ground offset `X = (u − cx) h / fx`; `∂X/∂h = (u − cx)/fx`; `∂X/∂u = h/fx`; `∂X/∂fx = −(u − cx) h / fx²`. The numerical Jacobian must match these.
- **Reliability flag:** a target estimate is flagged unreliable if it is invalid, if the relative range uncertainty exceeds `{{REL_UNC_THRESHOLD}}`, or if the ray is below `{{MIN_DEPRESSION_DEG}}`.

### 6.4 Ground-plane Kalman filter

State `[north, east, v_north, v_east]` in world coordinates, constant-velocity model, process noise `{{KALMAN_Q}}`. Measurements are the per-frame ground points with their own covariance from Section 6.3 (heteroscedastic). Work in world coordinates so the drone's own motion does not leak into target velocity. Predict-only on missed detections. Outputs: smoothed position, speed and heading with covariance. Tests: simulated target with known motion and noise gives a consistent Normalised Estimation Error Squared (NEES, a chi-squared statistic) within its confidence bounds; a stationary target gives speed consistent with zero.

### 6.5 Public application programming interface (API) (signatures to implement, adapt as needed)

```python
@dataclass(frozen=True)
class Camera:            # intrinsics K, optional distortion, mount R_bc, lever arm t_bc
    ...

@dataclass(frozen=True)
class Pose:              # position p_w (NED, metres), rotation R_wb
    ...

@dataclass(frozen=True)
class RangeEstimate:     # point_w, range_m, ground_dist_m, azimuth_deg, rel_azimuth_deg,
    ...                  # depression_deg, valid, reason, cov_ne (2x2), range_sigma_m, flags

def pixel_to_world_ray(cam: Camera, pose: Pose, uv) -> tuple[np.ndarray, np.ndarray]: ...
def intersect_horizontal_plane(origin, direction, z_plane) -> RangeEstimate: ...
def estimate_range(cam, pose, uv, h_above_plane, mode, obj_height_m=None) -> RangeEstimate: ...
def propagate_uncertainty(cam, pose, uv, h, sigmas, method="first_order"|"monte_carlo") -> RangeEstimate: ...
```

---

## 7. Mid-Air validation (accuracy against ground truth)

### 7.1 Scope and data volume

Geometry validation samples **ground-truth pixels**, so it does not depend on image appearance. One climate (`{{MIDAIR_CLIMATE}}`) is therefore enough. Download only `color_left` (optional), `depth`, `segmentation`, `normals` and `sensor_records.hdf5` for `{{N_TRAJ_MIDAIR}}` trajectories. As a one-line check, repeat the evaluation on a second climate for a few trajectories to confirm that results are climate-invariant; if they are not, investigate and report.

### 7.2 Loader

Read HDF5 with `h5py`. Map a frame at time `t = k / 25` seconds to ground-truth row `floor(100 t)` (equivalently `4k`), but **verify with the `camera_data` list and the example scripts**. Decode depth by reading the 16-bit single-channel PNG and reinterpreting the bits as 16-bit float; confirm against the example script and sanity-check values (plausible metres, no infinities except sky). Write loader tests with a tiny synthetic HDF5 and PNG fixture.

### 7.3 Resolve the unknowns by test

1. **Depth meaning:** for a handful of frames, back-project ground pixels using both interpretations (planar and radial) and fit a plane to each point set. The interpretation that gives the smaller plane residual on flat ground is the right one. Record the evidence in `docs/decisions.md`.
2. **Quaternion convention:** pin with a known-orientation test from the example scripts.
3. **Camera mounting `R_bc`:** start with identity (optical axis along body forward). Use the oracle-plane mode (Section 7.5) to check; if residuals are systematic, fit small mounting offsets on the **development split only**, store them with provenance, and report the fitted values. Also try viewing the sensor-position figure on the website.

### 7.4 Ground truth for a pixel

For pixel `(u, v)` with depth `d`: camera-frame point `X_c = d · K⁻¹[u, v, 1]ᵀ` (planar) or `d · unit(K⁻¹[u, v, 1]ᵀ)` (radial), whichever Section 7.3 confirms. World point `X_w = p_w + R_wb (R_bc X_c + t_bc)`. Ground-truth range is `‖X_w − C_w‖`.

### 7.5 Estimation modes

| Mode | Height above plane comes from | Purpose |
|------|-------------------------------|---------|
| `oracle_plane` | A plane fitted per frame to the ground-truth 3D ground points (robust fit) | Upper bound: tests the pinhole and pose mathematics. Remaining error comes from terrain not being a plane. |
| `relative_altitude` | Height fitted on the first frame of the trajectory, then updated by ground-truth vertical motion | Simulates a take-off-relative altimeter. Error grows when terrain height changes. |
| `noisy_inputs` | Either of the above, plus Gaussian noise on altitude, attitude, camera tilt, focal length and pixels with documented standard deviations (`{{SENSOR_NOISE}}`) | Realistic case; the headline numbers. |

### 7.6 Sampling and strata

Sample `{{PIX_PER_FRAME}}` pixels per frame every `{{FRAME_STRIDE}}` frames from **ground classes** only (dirt ground, ground vegetation, rocky ground, road, train track; report water plane separately, since it is genuinely flat). Exclude pixels within `{{EDGE_MARGIN_PX}}` of depth discontinuities. Compute the local surface slope from the normals map (rotate the body-frame normal into the world frame with the attitude, take the angle from vertical).

Report errors stratified by: depression angle, ground-truth range, height above plane, local slope, surface class, trajectory, and (for the one-line check) climate. Do not report a bin with fewer than `{{MIN_SAMPLES_PER_BIN}}` samples.

An additional experiment: use the general-plane implementation with a slope-aware plane (from the ground-truth normals) to show how much of the error the flat-ground assumption explains (tests H4).

### 7.7 Metrics

- **Accuracy:** signed and absolute range error, relative range error, horizontal ground-position error. Report median, mean, root-mean-square error (RMSE), 90th and 95th percentiles, and the **valid fraction** (how often an estimate exists).
- **Error versus range and depression angle:** binned curves, with first-order and Monte Carlo predictions overlaid (tests H2). Use trajectory-level bootstrap intervals (`{{N_BOOT}}` resamples).
- **Where the method becomes unusable:** use these curves to set `{{MIN_DEPRESSION_DEG}}` and `{{MAX_RANGE_M}}`; do not pre-set them.
- **Calibration of uncertainty (tests H3):** standardised error `z = (estimate − truth) / σ_estimate`. Report the standard deviation of `z` (ideal: 1), empirical coverage of the nominal 50, 68, 90, 95 and 99 per cent intervals, a reliability plot (nominal versus empirical coverage), and mean interval width (sharpness).
- **Recalibration:** fit one scalar multiplier on `σ` using the calibration split (maximum likelihood), apply it to the test split, and show before and after.
- **Reliability flag:** treat "large error" (relative error above `{{ERR_THRESHOLD_FRAC}}`) as the positive class and the flag as the predictor. Report the precision-recall curve and area under the receiver operating characteristic curve (AUROC); fix an operating point on the calibration split and report it on the test split.
- **Sensitivity (tornado chart):** error contribution from each input (altitude, each attitude angle, tilt, focal length, pixel noise) over a stated range. Say what this implies for where a sensor budget is best spent.

### 7.8 Outputs

`results/midair/{accuracy,calibration,flag,sensitivity}.json`, binned CSVs, and figures: error versus range, error versus depression angle, error versus slope, reliability plot, precision-recall curve, tornado chart.

---

## 8. AU-AIR real-footage evaluation

No ground-truth range exists, so claims here are about **plausibility and repeatability**, not accuracy. State this in every figure caption.

### 8.1 Loader and integrity checks

1. Write `scripts/inspect_auair.py` to discover the annotation JSON schema (keys, types, units, class list) and print it. Do not assume field names.
2. Build a canonical table `results/auair_frames.csv`: clip identifier, frame index, image path, time (ms), latitude, longitude, altitude in **metres** (convert from millimetres), roll, pitch, yaw, velocities, and the box list.
3. Segment clips by time-stamp gaps and file-name patterns. Verify totals against the paper (32,823 frames, 132,034 instances, eight classes); log any differences instead of hiding them.
4. Convert GPS to a local NED frame per clip.

### 8.2 Clip notes and tilt labelling

Generate contact sheets (a grid of frames per clip at different altitudes) with `scripts/contact_sheets.py`, and write `docs/auair_clip_notes.md` listing for each clip the altitude profile and attitude statistics. Ask Luke (via `BLOCKED.md`) to label each clip as straight-down (nadir) or oblique, and to note any visible lens curvature. Use straight-down clips for the main analysis; treat oblique clips as an extension with a sensitivity analysis.

### 8.3 Camera model (resolve with evidence, record uncertainty)

1. **Specification lookup:** find the manufacturer's camera specification for the Parrot Bebop 2; record the exact source and access date. Treat it as a prior, not a fact, because the recorded video is probably cropped and stabilised.
2. **Scale self-calibration (straight-down frames):** pixel size of vehicles scales with `f / h`. Using the 10, 20 and 30 metre passes, fit apparent vehicle length (in pixels, from well-aligned boxes) against `1/h`. The slope is `f · L`. Separate `f` from vehicle length `L` using a published length **distribution** (`{{CAR_LENGTH_PRIOR_SOURCE}}`), and report `f` with its uncertainty. Compare with the specification prior; a disagreement beyond the uncertainty points to cropping or distortion.
3. **Distortion:** inspect straight road markings in contact sheets and look for a signature of distortion in how ranging results vary with distance from the image centre. If present, restrict analysis to `{{CENTRAL_FRACTION}}` of the image and say so.
4. **Orientation hypothesis test:** H-rigid (camera follows the drone body, with fixed mount tilt) versus H-stabilised (roll and pitch digitally removed, fixed tilt relative to the horizon). Choose by which gives lower repeatability spread (Section 8.5) on the **calibration clips** only; confirm on held-out clips.
5. Write everything in `docs/auair_camera_model.md`, with the resolved `{{FOCAL_PX_AUAIR}}`, `{{DIST_COEFFS_AUAIR}}` and `{{CAMERA_TILT_DEG_BY_CLIP}}`, including what remains uncertain. Every AU-AIR result must state the camera-model assumptions.

### 8.4 Stationary-target discovery (independent of flight metadata)

Estimate camera motion from background features (feature tracking with a robust homography, with detections masked out), stabilise, and measure residual motion of box centres. A track is stationary if its residual displacement stays below `{{STATIONARY_PX_THRESHOLD}}` for at least `{{STATIONARY_MIN_S}}` seconds. This does not use altitude or GPS, so it does not make the repeatability test circular.

### 8.5 Repeatability metric

For each stationary track, compute the world ground position from every frame and report the spread (root-mean-square distance about the track mean, in metres). Restrict to **hover segments** (speed below `{{HOVER_SPEED_MS}}` for at least `{{HOVER_MIN_S}}` seconds), where GPS drift is nearly constant, so spread reflects ranging noise rather than GPS error; also report the all-flight version and say it includes GPS error. Break down by altitude, image radius, camera-model hypothesis, and contact-point mode. Use bootstrap intervals over tracks. The same hover segments give data-driven estimates of altitude and attitude noise for `{{SENSOR_NOISE}}`.

### 8.6 Moving targets

Run the detector and tracker on AU-AIR frames (five frames per second), attach ranging and the Kalman filter, and export `tracks_with_range.csv`. Plot speed distributions per class as a **plausibility** check only. Make no accuracy claim.

### 8.7 `[EXTRA]` E3: real-footage scale check with map measurements

Build a small landmark-clicking tool (OpenCV window) so Luke can mark `{{N_LANDMARKS}}` pairs of fixed landmarks (for example painted road markings) in frames from different altitudes. Luke measures the real separation of each pair on a public, openly licensed map and records only the numbers (do not copy or redistribute map imagery). Compare in-frame ranging distances with the map distances. This is independent of GPS and gives real-footage evidence of scale accuracy. Build the tool only if the earlier phases are done.

### 8.8 Limits to state

Single junction; low altitude (5 to 30 metres); one drone model; short ranges compared with long-range surveillance; camera model partly inferred.

---

## 9. Pillar A: aerial tracking baseline (VisDrone)

### 9.1 Data preparation

- Parse annotations with a schema check (Section 4.1). Map categories to two evaluation groups via config: **person** (pedestrian, people) and **vehicle** (car, van, truck, bus). Exclude "others" and drop ignored regions (category 0): detections whose centres fall in an ignored region are removed before scoring.
- Build a detector training set in the detector library's format from the VisDrone detection training and validation images. Keep the original 10 classes for training if that helps, and map to the two groups at evaluation time. Record the choice.
- Convert tracking ground truth and predictions to the MOTChallenge text format for the evaluation tools.

### 9.2 Detector baselines

| ID | Detector | Notes |
|----|----------|-------|
| B0 | Pretrained on a general dataset, zero-shot | Shows the aerial domain gap |
| B1 | Luke's MOT17-trained detector (`{{MOT17_WEIGHTS_PATH}}`) if available | Skip if absent |
| B2 | Fine-tuned on VisDrone detection training (`{{TRAIN_HYPERPARAMS}}`) | Main model |
| B3 | B2 with tiled inference (overlapping tiles, merged detections) | Small-object recovery; record the latency cost |

Detector family, sizes and input resolutions come from `{{DETECTOR_FAMILY}}`, `{{DETECTOR_SIZES}}` and `{{INPUT_SIZES}}`. Report detection mean Average Precision on the detection validation set and on frames from the MOT validation set, split by object size bin (box height in pixels). Training must be resumable and write curves. If no GPU is available, note it, use a smaller model or a free notebook service, and say so in the results.

### 9.3 Trackers

Evaluate ByteTrack-style and BoT-SORT-style association (as provided by the detector library), each with and without camera-motion compensation where supported. **Disable appearance re-identification by default** (motion and overlap only), as a stated design choice about not matching individuals by appearance. An optional ablation may enable it for vehicles only. Tune a small grid (`{{TRACKER_GRID}}`) on validation only.

### 9.4 Evaluation

- Metrics: Multi-Object Tracking Accuracy (MOTA), Identity F1 score (IDF1), HOTA if TrackEval is installed, identity switches, fragmentations, per-class (person and vehicle). Matching threshold `{{IOU_MATCH}}`.
- Breakdowns: object size bin, crowd density (objects per frame), and camera-motion magnitude (from the stabilisation homography in Section 8.4).
- **Reference to Luke's earlier work:** read his published MOT17 numbers from the README in `{{MOT17_REPO_PATH}}`, do not type them from this file, and present the aerial domain gap against them with a clear caveat that the benchmarks differ.
- Run validation during development; run test-dev **once** at the end.

### 9.5 Error analysis

Auto-generate a failure gallery: the worst identity-switch sequences and the most-missed small objects, with frame thumbnails and one-line causes where identifiable (small size, occlusion, camera motion). Save to `results/failures/`.

---

## 10. Pillar C: edge latency budget

### 10.1 Stages to time

Decode and read, preprocess, inference, post-processing (decode and non-maximum suppression), tracking update, ranging plus Kalman filter. Overlay drawing is reported separately and excluded from the budget.

### 10.2 Export and parity

Export the chosen detector to ONNX. Compare outputs with the original model on a fixed sample; report the actual maximum difference and detection-level agreement against `{{PARITY_TOL}}`. Report mean Average Precision parity on the validation set.

### 10.3 Quantisation

Compare 32-bit floating point (FP32) with 8-bit integer (INT8) quantisation (dynamic and static, using ONNX Runtime). Use a calibration set drawn from validation frames not used for any reported test. Report the accuracy cost directly (detection mAP, and MOTA and IDF1 on the tracking validation sequences).

### 10.4 Benchmark protocol

- Warm-up (`{{N_WARMUP}}` iterations), then `{{N_TIMED_FRAMES}}` timed frames, `{{N_REPEATS}}` repeats, thread settings `{{THREADS_SET}}`.
- Report median and the 95th and 99th percentiles for each stage and end to end, throughput in frames per second, and peak memory.
- Record CPU model, core count, operating system, library versions and power or thermal notes (`results/env.json`, which is `{{COMPUTE_PROFILE}}`). Do not run other heavy processes during timing; say what else was running.
- State `{{TARGET_FPS}}` and `{{LATENCY_BUDGET_MS}}` and whether the pipeline meets them at each operating point, using the 99th percentile as well as the median.

### 10.5 Pareto study

Models × input sizes × tiling on or off × precision. Plot accuracy against latency, mark the operating point that meets the budget, and report what that point costs in accuracy relative to the best configuration. Include ranging and Kalman cost to show it is negligible (or not).

### 10.6 `[EXTRA]` second hardware

Only if Luke has access to another device (a small single-board computer or a GPU board). Otherwise do not run, and make no claims about other hardware.

---

## 11. Integration, outputs and demo

### 11.1 End-to-end command

`aerialrange run --source <video-or-frames> --metadata <flight data> --config <config>` writes:

- `tracks.csv`: frame, track identifier, class, box, range, range sigma, azimuth, relative azimuth, depression angle, speed, speed sigma, validity, reason, reliability flag.
- An annotated video.
- A timing summary.

### 11.2 Overlay design

Colour boxes by reliability (reliable, uncertain, invalid), show `range ± σ` and relative bearing as text, draw faint ground-plane distance rings around the point below the drone, and include a legend and a frame timer. No faces, no blurring needed for public benchmark footage, but keep any original dataset credits visible in the video's final caption.

### 11.3 Demo video storyboard (60 to 90 seconds, `{{VIDEO_LENGTH_S}}`, `{{MAX_VIDEO_MB}}`)

1. Title and one-line claim (5 s).
2. VisDrone sequence: tracking with identities; the baseline versus fine-tuned comparison (15 s).
3. AU-AIR straight-down clip: ranging overlay with uncertainty; stationary-target repeatability plot (20 s).
4. Mid-Air: estimated versus true range, with the reliability flag firing on bad cases (20 s).
5. Latency chart against the budget (10 s).
6. Limits and credits (10 s).

Export H.264 video in an MPEG-4 (MP4) container with `ffmpeg` if available; no audio required.

---

## 12. Phases, tasks and exit criteria

### Phase 0: bootstrap
Create the repository layout, packaging, Makefile, lint and test setup, CI, `.gitignore`, `PROGRESS.md`, `BLOCKED.md`, configs with `null` placeholders, `scripts/env_report.py`, `scripts/check_data.py`. Write the initial `BLOCKED.md` from Section 3.
**Exit:** `make lint test` passes on an empty-but-structured repo; CI file present; `results/env.json` produced.

### Phase 1: geometry core (test-first, no datasets needed)
Implement Sections 6.1 to 6.4 with synthetic fixtures and the analytic oracles. Include the first-order versus Monte Carlo comparison and the NEES test.
**Exit:** all geometry tests pass; conventions pinned by tests; coverage of every public function; a short `docs/decisions.md` entry on every convention choice.

### Phase 2: Mid-Air validation (needs data; parallelisable with Phase 3 data preparation)
Implement Section 7. Resolve the unknowns by test, fit the camera mount on the development split, run all three modes, produce all outputs and figures.
**Exit:** results files and figures for H2, H3, H4 exist; limitations written; if data is missing, loaders and evaluation code pass on a synthetic Mid-Air-like fixture and the missing step is in `BLOCKED.md`.

### Phase 3: tracking baseline (needs data; GPU helpful)
Implement Section 9: conversion, baselines B0 to B3, tracker grid, evaluation, failure gallery, pixel-noise model fit (feeds Section 6.3).
**Exit:** validation results for all baselines; the test-dev run done once with frozen configs; `κ_u`, `κ_v` fitted and stored; H1 table produced.

### Phase 4: AU-AIR and integration
Implement Section 8 and the integration in Section 11.1. Camera-model investigation, repeatability results, tracks with range and the Kalman filter.
**Exit:** `docs/auair_camera_model.md` complete with uncertainties; repeatability results on held-out clips; end-to-end run produces `tracks.csv` and a video on at least one AU-AIR clip.

### Phase 5: edge budget
Implement Section 10.
**Exit:** ONNX parity report, quantisation accuracy report, benchmark results with percentiles, Pareto figure, budget verdict (H5).

### Phase 6: deliverables and polish
Write the brief, README, model card, data cards, limitations, reviewer questions and answers (FAQ), cover note; build the demo video; run the release checklist (Section 16).
**Exit:** every item in Section 16 is ticked.

### Fallback order if time runs short (cut from the bottom)
1. `[EXTRA]` items.
2. Section 10.6 and the INT8 static-quantisation variant.
3. The Kalman speed plausibility plots (keep the position filter).
4. The BoT-SORT versus ByteTrack comparison (keep one tracker).
5. Oblique AU-AIR clips.

**Minimum viable deliverable:** Phase 1 and Phase 2 complete; a single fine-tuned detector and tracker on VisDrone validation; ONNX CPU benchmark of the detector; AU-AIR straight-down repeatability on at least two held-out clips; brief and README.

---

## 13. Deliverables

| ID | Deliverable | Notes |
|----|-------------|-------|
| D1 | Repository | Reproducible; README quickstart tested on a clean clone |
| D2 | Two-page technical brief | Section 13.2 |
| D3 | Demo video | Section 11.3 |
| D4 | Results bundle | `results/` JSON, CSV, figures; every number traceable |
| D5 | Data cards, model card, limitations | `docs/` |
| D6 | Reviewer FAQ | `docs/faq_for_reviewers.md` (Section 13.4) |
| D7 | Cover note draft | `docs/cover_note.md`, for Luke to edit and send himself |

### 13.1 Writing standards (all prose)

- **Discipline and audience:** state at the top of the brief: discipline is computer vision and robotics perception engineering; audience is senior engineers at an electro-optical tracking company.
- **UK spelling** (metres, colour, normalise, analyse, licence as a noun).
- **Abbreviations:** define on first mention as the full term followed by the abbreviation in brackets, then use the abbreviation exclusively. Define again at first use in each separate document.
- **Referencing:** Harvard (author-date in text, alphabetical reference list). Verify every reference (authors, year, venue) from its primary source before citing. Likely references: Bozcan and Kayacan (2020, AU-AIR); Fonder and Van Droogenbroeck (2019, Mid-Air); Zhu et al. (2021, VisDrone); the CLEAR MOT metrics paper (Bernardin and Stiefelhagen, 2008); the identity-metrics paper (Ristani et al., 2016); the HOTA paper (Luiten et al., 2021); the ByteTrack and BoT-SORT papers. Confirm details before use.
- **Banned filler:** do not use phrases such as "delve", "in today's rapidly evolving", "it is important to note", "leverage", "cutting-edge", "seamless", "game-changer", "robust solution", "in conclusion", "furthermore", "moreover", "state-of-the-art" without a specific comparison, or any marketing tone. Prefer short, concrete sentences with numbers from results files.
- **Voice:** match the sample in `{{VOICE_SAMPLE}}` (sentence length, directness, first person where natural). If no sample exists, write plainly and flag it in `BLOCKED.md`.
- **Process:** write the brief **subsection by subsection**. When Luke is available, show each subsection for approval before moving on. When he is not, mark drafts `DRAFT` at the top.
- **Numbers:** insert from results files via `{{RESULT:name}}` and `scripts/fill_docs.py`. No hand-typed results. The release check fails if any `{{...}}` remains in a published document.
- **Tone on claims:** say "estimated", "in this dataset", "under these assumptions". Do not write "accurate to X" without the test that supports it. Do not claim long-range performance.

### 13.2 Technical brief (two pages)

1. Title, discipline and audience line.
2. Abstract (limit `{{ABSTRACT_WORDS}}`).
3. Problem and motivation (why range with uncertainty from a moving camera matters; passive sensing; assumptions).
4. Method: pipeline figure; geometry in five lines; uncertainty model.
5. Experiments: A (tracking), B (ranging on Mid-Air and AU-AIR), C (latency).
6. Results: one table and one figure per pillar, hypotheses H1 to H5 each marked supported, partly supported or not supported.
7. Failure analysis: where it breaks (near-horizon, slopes, small objects, camera model uncertainty).
8. Limitations, and what would change with real sensors (terrain models, laser rangefinder or radar fusion, calibrated lens, thermal footage, hardware-in-the-loop timing).
9. References (Harvard). Dataset attributions and licences.

Put extended material in `docs/technical_report.md` rather than exceeding two pages.

### 13.3 README structure

Positioning sentence; headline results table (auto-filled); quickstart (setup, data check, one-command demo on synthetic data, full commands); repository map; datasets and licences with attributions; scope, ethics and limitations; how to reproduce each result; citation; licence statement.

### 13.4 Reviewer FAQ (answer each in one paragraph with a pointer to the evidence)

How accurate is the range, and at what distances? What happens near the horizon? Does it work on slopes? Is the uncertainty honest, and how do you know? What does the reliability flag catch and miss? What assumptions does the camera model make on real footage? What latency, on what hardware, at what percentile? How was test data kept separate from tuning? Why not use a laser rangefinder or radar, and how would this combine with one? What would you do differently with real sensor telemetry? What is the weakest part of this work?

### 13.5 Cover note

`docs/cover_note.md`: a draft message from Luke to the engineer he met, no more than about 120 words, plain tone, links to the repository and video, one concrete sentence on what was built and one on what he would do next. Mark `DRAFT FOR LUKE TO EDIT`. Do not send.

---

## 14. Risks and mitigations

| ID | Risk | Mitigation |
|----|------|-----------|
| R1 | AU-AIR camera model cannot be resolved | Restrict claims to repeatability with stated assumptions; lean on Mid-Air for accuracy; show sensitivity to the unknowns |
| R2 | Depth planar versus radial confusion in Mid-Air | Resolve by plane-fit test (Section 7.3); keep the test in the suite |
| R3 | Quaternion or frame sign errors | Pin by tests; cross-check with Mid-Air example scripts and AU-AIR worked example |
| R4 | Downloads blocked or slow | Manual download by Luke; subsets; synthetic fixtures keep other work moving |
| R5 | No GPU or limited compute | Smaller detector; fewer epochs; free notebook service; report honestly |
| R6 | Small objects at altitude undetected | Tiled inference; size-binned reporting; report the limit |
| R7 | Uncertainty is not calibrated | Report it; show recalibration; the flag is still evaluated on its own merits |
| R8 | Licence conflict: Ultralytics is AGPL-3.0, which requires combined works to be released under the same terms when distributed | Present options to Luke (release under AGPL-3.0, or use a permissively licensed detector); this is not legal advice; decide before the first public release |
| R9 | Mid-Air share-alike licence | Publish code and metrics only; do not publish derived data; attribute |
| R10 | Time overrun | Fallback order in Section 12; minimum viable deliverable |
| R11 | Overclaiming | Release checklist (Section 16) and reviewer FAQ |

---

## 15. Optional extras and out of scope

### Extras `[EXTRA]` (only after Phase 5 exit criteria)

- **E1** Failure gallery refinements (already core in Section 9.5; extend to ranging failures).
- **E2** Mid-Air second-climate invariance check at larger scale.
- **E3** Landmark scale check on AU-AIR (Section 8.7).
- **E4** Slope-aware plane study beyond Section 7.6.
- **E5** Correlated noise model for altitude and pitch.
- **E6** A Dockerfile and a `make reproduce` target that rebuilds all figures from results files.

### Out of scope (do not build)

Cue-driven target acquisition tests; thermal or tiny-drone studies on anti-UAV datasets; synthetic weather or degradation robustness curves (Mid-Air climates give a small by-product only); any weapons, engagement or targeting functionality; face recognition or re-identification of individuals; long-range or ground-based drone ranging claims.

---

## 16. Release checklist (definition of done)

- [ ] `make lint test` passes on a clean clone; CI is green.
- [ ] `make all-results` regenerates every figure and results file from raw data (with data present).
- [ ] Every number in the README, brief, cover note and video traces to a results file; no `{{...}}` remains in published documents.
- [ ] Test-dev was run once; Mid-Air test trajectories were not used for tuning; AU-AIR held-out clips were not used for calibration.
- [ ] Each of H1 to H5 is reported as supported, partly supported or not supported, with the evidence.
- [ ] `docs/limitations.md`, `docs/data_cards.md`, `docs/model_card.md`, `docs/faq_for_reviewers.md` complete.
- [ ] Dataset attributions and licences correct; no data or weights in the repository; secret scan clean.
- [ ] Licence decision recorded (risk R8).
- [ ] Brief is two pages, in UK spelling, Harvard referenced, abbreviations defined at first use, no banned phrases, written in Luke's voice.
- [ ] Demo video within `{{MAX_VIDEO_MB}}` and `{{VIDEO_LENGTH_S}}`.
- [ ] No company name outside `docs/cover_note.md`; no weapons language anywhere.
- [ ] `PROGRESS.md` summarised; `BLOCKED.md` empty or explained; Luke told exactly what to review, edit and publish.

---

## 17. Abbreviations used in this file

Each was defined in full at first use above; this list is for lookup only.
AGPL: GNU Affero General Public License. AUROC: area under the receiver operating characteristic curve. CC BY: Creative Commons Attribution. CI: continuous integration. CLI: command-line interface. CPU: Central Processing Unit. EO: Electro-Optical. FP32: 32-bit floating point. FRD: forward, right, down. GPS: Global Positioning System. GPU: Graphics Processing Unit. HDF5: Hierarchical Data Format 5. HOTA: Higher Order Tracking Accuracy. IDF1: Identity F1 score. IMU: Inertial Measurement Unit. INT8: 8-bit integer. IoU: Intersection over Union. IR: Infrared. MOT: Multi-Object Tracking. MOTA: Multi-Object Tracking Accuracy. NED: North, East, Down. NEES: Normalised Estimation Error Squared. ONNX: Open Neural Network Exchange. PNG: Portable Network Graphics. RGB: red, green, blue. RMSE: root-mean-square error. UAV: Unmanned Aerial Vehicle. YAML: YAML Ain't Markup Language. API: application programming interface. CSV: comma-separated values. FAQ: frequently asked questions. JSON: JavaScript Object Notation. MP4: MPEG-4 container format. PDF: Portable Document Format.

### Source pages checked while writing this file

- AU-AIR paper: `https://arxiv.org/pdf/2001.11737` and dataset page `https://bozcani.github.io/auairdataset`
- Mid-Air: `https://midair.ulg.ac.be/` (home, technical specifications, data organisation pages)
- VisDrone: `https://github.com/VisDrone/VisDrone-Dataset`
