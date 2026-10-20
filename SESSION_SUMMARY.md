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
| Phase 3: tracking | ~60 %. Three trained detectors; tracker tuning and the final test run are left |
| Phase 4: real footage (AU-AIR) | ❌ Not started; dataset still not found |
| Phase 5: speed | ~20 %. Tools built |
| Phase 6: write-up and video | ❌ Not started |

**Overall: roughly half way.** 291 automated tests pass.

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

| | Untrained (B0) | **Trained (B2)** | Trained + tiles (B3) |
|---|---|---|---|
| Person detection AP50 | 0.171 | 0.412 | **0.427** |
| Vehicle detection AP50 | 0.248 | 0.587 | **0.610** |
| Small vehicles (16–32 px) | 0.051 | 0.266 | **0.376** |
| Vehicle tracking IDF1 (BoT-SORT) | 0.385 | **0.586** | 0.573 |
| Time per frame (laptop, rough) | | **0.21 s** | 1.48 s |

- Trained-detector score on DET val: mAP50 0.303 (all 10 classes), the normal range for this size of model (a published comparable figure is 0.334).
- Tiling finds more small objects but adds false detections and is about 7× slower, so **B2 stays the default** for now.
- The detector's box noise is measured (about 9–11 % of box size for people, 4–5 % for vehicles). It feeds the distance error bars.

### Problems found and fixed along the way
- VisDrone's claim that its image set doesn't overlap its videos is false; 78 overlapping images were removed (your approval).
- A crash on frames with too few ground points; an analysis-stage crash; a wrong selection rule in the terrain method; the Drive-move resume bug; camera-motion compensation silently off in tiled tracking. All were fixed with tests, and invalid results are kept and labelled.

---

## 4. Data and storage
- **Mid-Air:** all 30 flights downloaded. The 9 **test** flights are on Google Drive (`G:\My Drive\aerial-track-and-range-data`), every file verified. The practice and calibration flights are on the laptop.
- **VisDrone:** tracking train and test-dev, and DET test-dev, are on Drive. The rest is on the laptop.
- **Trained models** (in `cache\train\`, never committed):
  - `B2_yolo26n_640`: scored.
  - `B2_yolo26n_960`: **not scored yet**.
  - `B2_yolo26s_640`: **not scored yet**.
- Laptop free space: about 22–24 GB.

---

## 5. What's next

**Claude, next session**
1. Score the two new models (960 and "s") on validation: detection and tracking.
2. Tune the tracker's confidence threshold on validation (with and without tiling).
3. Final Mid-Air test-split run, **once**: restore the test flights from Drive, download their colour images, run, and report. It needs settings frozen first.
4. Phase 5 (speed): needs your frames-per-second target.

**You**
1. **Commit** (section 6).
2. Keep looking for **AU-AIR** (real drone footage; needed for Phase 4 and plan C).
3. Optional: your MOT17 trained `.pt` file (for baseline B1).
4. Later: frames-per-second target, a writing sample, demo video limits, licence variant ("-only" or "-or-later").

---

## 6. How to commit

```powershell
cd C:\Users\27622\Documents\Projects\aerial-track-and-range
git status
git add .
git commit -m "phase-2/3: terrain-aware ranging with calibration and flag; trained detector, tiling and tracking"
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
