# Items that need Luke

Last updated: 2026-10-19.

## Decisions needed now (Phases 2 and 3)

1. **`{{ERR_THRESHOLD_FRAC}}`: what counts as a "large" ranging error?** This one value sets the reliability flag's labels and the usable depression-angle and range limits (D-311). The swept candidates are 5 %, 10 %, 20 % and 50 % relative range error. I suggest deciding once the development curves are complete.
2. **Detector training compute (baseline B2).** This machine has no NVIDIA GPU. CPU fine-tuning works but is slow, and I will measure one epoch's time before proposing a schedule. The alternative is a free notebook GPU (Colab or Kaggle), which means you upload VisDrone DET there (about 1.5 GB) under the dataset's terms. That is your call; I will not upload anything.
3. **VisDrone overlap finding (D-308).** Some DET images come from the same source videos as MOT val and test-dev clips, which contradicts the claim in build.md Section 4.1. I excluded those 78 images (1.1 %) from training and model selection to avoid leakage. Tell me if you would rather handle it differently.

4. **Uncertainty model scope (H3), from the development run.** The propagated sigma covers sensor noise only. On Mid-Air the terrain error dominates, so intervals are badly over-confident and heavy-tailed: at the mid noise level the z spread is about 22, against a robust spread of about 3. One recalibration scalar (Section 7.7) cannot fix that shape. Options:
   - (a) Keep the model as specified, report H3 as not supported on rough terrain, and show the scalar's effect honestly.
   - (b) Add an explicit terrain-relief term to the input covariance, fitted on the development split only. That is a model change beyond Section 6.3.
   - (c) Report calibration separately for flat ground (low slope) and rough ground.

   I recommend (a) plus (c): it stays within the spec, is honest, and is informative. (b) is a reasonable later extension.

## Data (Section 4)

5. **Mid-Air: downloading** (`scripts/download_midair.py`, started 2026-10-18 at your request). Kite_training/sunny without colour images, about 2.8 GB per trajectory. 39 archives failed during an internet outage on 2026-10-19 and will be retried when the current pass ends. It stops if free disk space falls below 10 GB, and it resumes if rerun. Progress is in `Data/midair/download_log.txt`. Delete `Data/midair/Kite_training/` when we are done with it.
6. **AU-AIR: not downloaded** (the dataset site's links are broken). Needed from Phase 4 only. When you have it, set `auair_subdir` in `configs/data.yaml`.
7. **Stray files.** `Data/annotations/` and `Data/images/` (1,610 files each) duplicate VisDrone DET test-dev and are unused. Delete them if you agree; I have not touched them.
8. **Confirm the data root.** I use `Data/` inside this repository, which is git-ignored. Tell me if you want a different location.
9. **Mid-Air second climate (optional, Section 7.1).** A few trajectories of one PLE climate would give the one-line climate-invariance check. Not downloaded, to save disk space.

Resolved: VisDrone DET train and val are present and valid (2026-10-19).

## Paths and decisions (Section 3)

10. **`{{MOT17_REPO_PATH}}` and `{{MOT17_WEIGHTS_PATH}}`**: not provided. Without the weights, baseline B1 is skipped (Section 9.2). Without the repo, Phase 3 cannot quote your MOT17 numbers. You mentioned a link; it did not come through.
11. **`{{TARGET_FPS}}`**: you chose "decide later". Needed in Phase 5.
12. **Licence variant**: you chose AGPL-3.0. Do you want "AGPL-3.0-only" (currently in `pyproject.toml`) or "AGPL-3.0-or-later"?
13. **`{{VOICE_SAMPLE}}`**: a sample of your writing in `docs/voice_sample.md`. Needed in Phase 6.
14. **`{{MAX_VIDEO_MB}}`, `{{VIDEO_LENGTH_S}}`**: demo video limits. Needed in Phase 6.

## Placeholders I introduced (no action needed unless you want to set them)

- `{{NONLINEAR_RATIO_TOL}}`: when first order and Monte Carlo "disagree materially" (Section 6.3). I will propose a value from the Phase 2 curves.
- `{{DEPTH_EDGE_REL}}`, `{{NORMAL_PATCH_PX}}`, `{{MIN_GROUPS_PER_BIN}}`: set from data or with a stated reason (D-209, D-213).
- `{{TILE_SIZE}}`, `{{TILE_OVERLAP}}`: chosen on validation when B3 runs (D-310).

## Later (not needed yet)

15. Label AU-AIR clip tilt categories from contact sheets (Section 8.2, Phase 4).
16. Optional: landmark distances for `[EXTRA]` E3.

## Tooling

17. **GNU Make is not installed**, so `make` targets cannot run as written. I run the same commands directly. To get it: `winget install ezwinports.make`. CI on Linux has `make`.
