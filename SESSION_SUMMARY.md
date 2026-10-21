# Session summary (updated 20 October 2026)

Plain-English status. All numbers are **development numbers**, from practice and validation data used while building. The real, reportable results come from the held-back test data, run **once** at the end.

---

## 1. What the project is

A drone camera spots people and cars, follows them, works out **how far away each one is and how sure we are**, and runs fast on an ordinary laptop. It has three parts:

1. **Tracking**: detect and follow objects (VisDrone dataset).
2. **Distance (ranging)**: how far away, with honest error bars (Mid-Air synthetic world now; AU-AIR real footage later).
3. **Speed**: real time on a CPU.

**Rule:** Claude never commits. You make every commit (section 6).

---

## 2. Where we are

| Part | Status |
|---|---|
| Phase 0–1: set-up and geometry | ✅ Done |
| Phase 2: distance on Mid-Air | ~85 %. Everything built and run on practice and calibration data; the final test run is left |
| Phase 3: tracking | ~80 %. All detectors scored and the tracker tuned; choosing between the two best detectors (decided by the Phase 5 speed test), the error gallery and the final test run are left |
| Phase 4: real footage (AU-AIR) | ~20 %. Data loaded, checked and split into 48 clips; **your labels done**; plan agreed (straight-down clips first, then tilt from motion); first look at the focal length |
| Phase 5: speed | ~20 %. Tools built; **target set: 30 fps** (stretch), with 10 fps also reported |
| Phase 6: write-up and video | ❌ Not started |

**Overall: a little over half way.** 303 automated tests pass.

---

## 3. Key results so far (development)

### Distance on Mid-Air (15 practice flights)

| Method | Valid | Median error |
|---|---|---|
| Flat ground + true height (unrealistic best case) | 88 % | 16 % |
| Flat ground + take-off altimeter (realistic) | 48 % | 253 % |
| **Terrain from motion (new, your plan D)** | **94 %** | **2.5 %** |

- The terrain method **doesn't get worse on slopes** (about 2–3 % from 0° to 45°) and **needs no height above ground**.
- **Honest error bars (plan B):** fitted on the calibration flights and checked on the practice flights:

  | Promised | 68 % | 90 % | 95 % | 99 % |
  |---|---|---|---|---|
  | Before | 60 % | 78 % | 83 % | 88 % |
  | **After** | **65 %** | **87 %** | **93 %** | **98 %** |
- **Warning light (plan E):** AUROC **0.77**, against about 0.60 for the old method. Bumpy local ground is its strongest clue.

### Tracking on VisDrone (validation videos)

**Detection** (how well each model finds objects, AP50):

| | Untrained (B0) | Old trained (n 640) | **New: n 960** | **New: s 640** | Old + tiles (B3) |
|---|---|---|---|---|---|
| People | 0.171 | 0.412 | **0.511** | 0.507 | 0.427 |
| Vehicles | 0.248 | 0.587 | 0.625 | **0.627** | 0.610 |
| Time per image (rough) | 0.11 s | 0.12 s | 0.13 s | 0.15 s | 1.64 s |

**Tracking** (BoT-SORT, mean IDF1 over people and vehicles; higher means fewer identity mix-ups):

| Detector | Library settings | **Tuned settings** |
|---|---|---|
| Old trained (n 640) | 0.489 | 0.540 |
| **n 960** | 0.559 | **0.620** |
| **s 640** | 0.551 | **0.613** |
| Tiles (B3) | 0.462 | 0.539 |

- **From where we started (0.489) to now (0.620) is a big step.** About half comes from the better detectors, half from tuning the tracker.
- **What the tuning does:** the tracker now needs more confidence before it starts a new track. That removes many false and broken tracks (identity switches for people fell from 626 to 168), but **it misses more people** (people found fell from 62 % to 52 %). That trade-off will be stated plainly in the write-up.
- **n 960 and s 640 are tied** on accuracy. **Your frames-per-second target decides** which one we keep. Until then n 960 is the default.
- Tiling is out: no better than the old model once both are tuned, and 7–13× slower.
- BoT-SORT beats ByteTrack in every case.
- The n 960 model was **still improving** when training stopped at 50 epochs. Longer training (optional, on Kaggle) could gain a little more.
- The detector's box noise is measured (about 9–11 % of box size for people, 4–5 % for vehicles). It feeds the distance error bars. (Measured on the old model; to be refreshed for the chosen one.)

### Problems found and fixed along the way
- VisDrone's claim that its image set doesn't overlap its videos is false; 78 overlapping images were removed (your approval).
- A crash on frames with too few ground points; an analysis-stage crash; a wrong selection rule in the terrain method; the Drive-move resume bug; camera-motion compensation silently off in tiled tracking. All were fixed with tests, and invalid results are kept and labelled.
- (20 Oct) Tiled tracking had been given fewer low-confidence boxes than normal tracking, so the earlier comparison was unequal. All setups now get the same boxes.
- (20 Oct) Running 5 tuning jobs at once ran the laptop out of memory (15 GB). Now 3 at a time; nothing was lost.

---

## 4. Data and storage
- **Mid-Air:** all 30 flights downloaded. The 9 **test** flights are on Google Drive (`G:\My Drive\aerial-track-and-range-data`), every file verified. The practice and calibration flights are on the laptop.
- **VisDrone:** tracking train and test-dev, and DET test-dev, are on Drive. The rest is on the laptop.
- **AU-AIR:** found by you. On Drive (`AU-AIR`) and copied to the laptop (`Data\AU-AIR`, 2.3 GB, 32,823 frames). Every image checked: all present and readable. 5 frames per second; 8 recordings, 48 clips; heights 2.8–30.6 m. **Licence:** your link (a third-party index) says CC BY 4.0, but the authors' own file says non-commercial, so we follow the stricter one: credit the authors, non-commercial use, and no AU-AIR images in the repository (D-323).
- **Trained models** (in `cache\train\`, never committed): `B2_yolo26n_640`, `B2_yolo26n_960`, `B2_yolo26s_640`, all scored.
- Saved detections for tracker tuning: `cache\visdrone\dets\` (19 MB; can be deleted any time and rebuilt).
- Laptop free space: about 23 GB (after the AU-AIR copy).

---

## 5. What's next

**Done this session (20 Oct):** both new models scored, and the tracker tuned on validation (sections 3 and D-319 to D-321 in `docs/decisions.md`). AU-AIR copied in.

**Claude, next session**
1. **AU-AIR focal length** (straight-down clips): find a published car-length distribution and the Bebop 2 camera specification, then fit properly. A first look suggests about 1,400 pixels.
2. Phase 4 continued: run the detector and tracker on AU-AIR, find parked cars for the repeatability test, then build tilt-from-motion for the oblique clips (it must read about 90° on the straight-down clips).
3. **Phase 5 (speed), aiming at 30 fps:** formal benchmark, ONNX export (fix the parity gap first), INT8, and the accuracy-against-speed chart. This also picks between n 960 and s 640.
4. Phase 3 leftovers: error gallery; refresh the box-noise fit for the chosen detector.
5. Final Mid-Air test-split run, **once**, after settings are frozen.

**You**
1. **Commit** (section 6).
2. Optional: retrain n 960 for longer on Kaggle (it hadn't finished improving); your MOT17 `.pt` file (baseline B1).
3. Later: a writing sample, demo video limits, licence variant ("-only" or "-or-later").

---

## 6. How to commit

```powershell
cd C:\Users\27622\Documents\Projects\aerial-track-and-range
git status
git add .
git commit -m "phase-4: clip labels, camera-tilt plan, first scale look"
```

Check that `git status` doesn't list `Data\`, `cache\`, `.venv\` or any `.pt` file. They're ignored automatically.

### Putting it on GitHub (optional, private)
build.md says not to publish yet, so make the repository **private**:
1. Go to https://github.com/new, name it `aerial-track-and-range`, choose **Private**, and **don't** add a README, licence or .gitignore (the project already has them). Click **Create repository**.
2. Then, in PowerShell:
   ```powershell
   git remote add origin https://github.com/LukeA77/aerial-track-and-range.git
   git branch -M main
   git push -u origin main
   ```
3. Each later commit is then followed by `git push`.

Note: `build.md` and `CLAUDE.md` are in the repository. That's fine while it's private. Decide before making it public whether you want them there; they describe your personal situation and my instructions.

---

## 7. Where to look

| File | What it is |
|---|---|
| `BLOCKED.md` | Everything waiting on you |
| `PROGRESS.md` | Full technical log |
| `docs/decisions.md` | Every choice, with reasons and sources |
| `docs/runbook.md` | Exact commands to finish each part |
| `docs/gpu_training.md` | Kaggle step by step |
| `results/` | All measured numbers and figures |
