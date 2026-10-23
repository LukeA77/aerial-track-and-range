# aerial-track-and-range

**DRAFT.** Numbers are filled from `results/` by `scripts/build_docs.py`; text awaits Luke's review.

Tracking people and vehicles from a drone camera, estimating how far away each one is with an honest error bar, and running on a laptop Central Processing Unit (CPU). Every number below comes from a results file produced by code in this repository; test splits were run once, after settings were frozen.

## Headline results

| Pillar | Result (held-out test data) |
|---|---|
| Distance, Mid-Air (synthetic, {{RESULT:headline.json#midair_test.n_test_flights|d}} test flights) | Terrain from motion: median distance error {{RESULT:headline.json#midair_test.terrain_median|.1%}} (95 % interval {{RESULT:headline.json#midair_test.terrain_median_ci.0|.1%}} to {{RESULT:headline.json#midair_test.terrain_median_ci.1|.1%}}), {{RESULT:headline.json#midair_test.terrain_valid|.0%}} of estimates valid. Flat ground with a take-off altimeter: {{RESULT:headline.json#midair_test.flat_alt_median|.0%}}. |
| Honest error bars | Nominal 90 % intervals contain the truth {{RESULT:headline.json#midair_test.cov_cal_90|.0%}} of the time after calibration ({{RESULT:headline.json#midair_test.cov_raw_90|.0%}} before). |
| Tracking, VisDrone test-dev | Identity F1 (IDF1) {{RESULT:headline.json#visdrone_test.vehicle_idf1|.3f}} for vehicles and {{RESULT:headline.json#visdrone_test.person_idf1|.3f}} for people; small people are the weak point ({{RESULT:headline.json#visdrone_test.person_recall_16_32|.0%}} found at 16 to 32 pixels tall). |
| Real footage, AU-AIR (held-out flights) | Positions of stationary vehicles repeat to {{RESULT:headline.json#auair.heldout_rel_all|.1%}} of their distance ({{RESULT:headline.json#auair.heldout_segments|d}} stretches). Repeatability, not accuracy: AU-AIR has no ground-truth positions. |
| Speed, laptop CPU ({{RESULT:headline.json#edge.cpu|s}}) | {{RESULT:headline.json#edge.fast_fps|.1f}} frames per second sustained with detection on every second frame (IDF1 on validation {{RESULT:headline.json#edge.fast_idf1|.3f}}); the most accurate setting runs at {{RESULT:headline.json#edge.accurate_fps|.1f}} (IDF1 {{RESULT:headline.json#edge.accurate_idf1|.3f}}). |

The limits matter as much as the results: see [docs/limitations.md](docs/limitations.md).

## Quickstart

```
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-lock.txt     # .venv/bin/python on Linux or macOS
.venv/Scripts/python -m pip install -e . --no-deps
.venv/Scripts/python -m pytest                                   # tests
.venv/Scripts/aerialrange demo --out cache/demo                  # whole pipeline on a synthetic flight, no datasets
```

The demo writes `cache/demo/run/tracks.csv`, `annotated.mp4` and `timing.json`, and checks distances and speeds against the synthetic truth.

On a real flight (a video or a folder of frames, plus a flight-data CSV with position, true height, heading and camera tilt per frame):

```
.venv/Scripts/aerialrange run --source <frames-or-video> --metadata <flight.csv> --out cache/run
```

`scripts/auair_export_flight.py --clip N` builds those inputs for an AU-AIR clip. Settings are in `configs/run.yaml`.

## Repository map

| Path | Contents |
|---|---|
| `src/aerialrange/geometry/` | Camera model, ground-plane ranging, uncertainty propagation, triangulation, terrain fitting, Kalman filter (built test-first) |
| `src/aerialrange/track/`, `detect/` | Tracker running, evaluation, tiling, saved-detection replay |
| `src/aerialrange/evaluate/` | Mid-Air and AU-AIR evaluations, calibration, reliability flag, statistics |
| `src/aerialrange/pipeline/` | The end-to-end `aerialrange run` and `demo` |
| `src/aerialrange/edge/` | Latency benchmark harness |
| `scripts/` | Every experiment, one script each |
| `configs/` | Every setting, each with its source |
| `results/` | Every number and figure in the documents |
| `docs/` | Decisions, limitations, data and model cards, reviewer questions, brief |

## Datasets and licences

No data or model weights are in this repository. See [docs/data_cards.md](docs/data_cards.md).

- **VisDrone2019** (Zhu et al., 2021): tracking and detection. No licence is stated; used for research evaluation only.
- **Mid-Air** (Fonder and Van Droogenbroeck, 2019): synthetic flights with ground-truth depth. Creative Commons Attribution-NonCommercial-ShareAlike 4.0.
- **AU-AIR** (Bozcan and Kayacan, 2020): real drone footage with flight data. Used under the stricter of two stated licences (non-commercial, attributed).

## Scope, ethics and limits

This is a perception and measurement project: detection, tracking, distance and speed estimation from public research datasets. People and vehicles are tracked as boxes only; there is no face analysis and no matching of individuals by appearance. Distances are estimates under stated assumptions (flat ground or terrain from motion, a known camera, known camera pose) and are not claimed beyond the tested conditions: low altitude ({{RESULT:headline.json#auair.alt_min_m|.0f}} to {{RESULT:headline.json#auair.alt_max_m|.0f}} m on real footage), short ranges, one drone and one site for real footage.

## Reproducing the results

`docs/runbook.md` lists the commands for each result, in order. Decisions and their reasons are in `docs/decisions.md`. Test splits run once: the scripts refuse a test run without `--final`, and `scripts/freeze.py` checks that settings have not changed since freezing.

## Licence

GNU Affero General Public License v3.0 only (AGPL-3.0-only), matching the detector library (Ultralytics). See `LICENSE`.
