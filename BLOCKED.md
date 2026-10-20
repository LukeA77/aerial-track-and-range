# Items that need Luke

Last updated: 2026-10-20.

## Decisions needed now

1. **AU-AIR tilt labels.** Open the 48 contact sheets in `cache/auair/contact_sheets/` and fill the View and Curvature columns of `docs/auair_clip_notes.md` (instructions at the top of that file). Expect `mixed` often: the camera tilt changes within clips (D-503).
2. **AU-AIR camera tilt (decision coming).** AU-AIR does not record the camera tilt; Claude will bring options for estimating it from the images.
3. **B1 weights (optional).** The MOT17-trained `.pt` file from Luke's Kaggle run, if he still has it.
4. **Optional:** retrain B2 n 960 for more epochs on Kaggle; it peaked at its last epoch (50).

Resolved 2026-10-19 to 20: uncertainty on rough terrain (plans D, E and B built, D-401 to D-404); GPU training (three B2 models trained on Kaggle).

Resolved 2026-10-19 (D-314): large-error threshold 10 %; overlap exclusion approved; MOT17 repository linked; duplicate folders confirmed safe to delete.

## Data (Section 4)

5. **Mid-Air: downloading** (`scripts/download_midair.py`, started 2026-10-18 at your request). Kite_training/sunny without colour images, about 2.8 GB per trajectory. 39 archives failed during an internet outage on 2026-10-19 and will be retried when the current pass ends. It stops if free disk space falls below 10 GB, and it resumes if rerun. Progress is in `Data/midair/download_log.txt`. Delete `Data/midair/Kite_training/` when we are done with it.
6. **AU-AIR: resolved (2026-10-20).** Found by Luke, extracted to `G:\My Drive\aerial-track-and-range-data\AU-AIR`, copied by Claude to `Data/AU-AIR` (32,824 files, 0 failed) and set in `configs/data.yaml`. Verified: 32,823 annotated frames, all present and readable at 1920 × 1080, none missing, extra or duplicated.
   Licence: resolved by D-323 (restrictive reading: non-commercial, attributed; both sources cited).
7. **Stray files.** `Data/annotations/` and `Data/images/` (1,610 files each) duplicate VisDrone DET test-dev and are unused. Luke confirmed on 2026-10-19 (D-314) that they are safe to delete; Luke deletes them, or tells Claude to.
8. **Confirm the data root.** I use `Data/` inside this repository, which is git-ignored. Tell me if you want a different location.
9. **Mid-Air second climate (optional, Section 7.1).** A few trajectories of one PLE climate would give the one-line climate-invariance check. Not downloaded, to save disk space.

Resolved: VisDrone DET train and val are present and valid (2026-10-19).

## Paths and decisions (Section 3)

10. **`{{MOT17_REPO_PATH}}` and `{{MOT17_WEIGHTS_PATH}}`**: not provided. Without the weights, baseline B1 is skipped (Section 9.2). Without the repo, Phase 3 cannot quote your MOT17 numbers. You mentioned a link; it did not come through.
11. **`{{TARGET_FPS}}`**: resolved, 30 fps (stretch), with 10 fps reported as a reference (D-322).
12. **Licence variant**: you chose AGPL-3.0. Do you want "AGPL-3.0-only" (currently in `pyproject.toml`) or "AGPL-3.0-or-later"?
13. **`{{VOICE_SAMPLE}}`**: a sample of your writing in `docs/voice_sample.md`. Needed in Phase 6.
14. **`{{MAX_VIDEO_MB}}`, `{{VIDEO_LENGTH_S}}`**: demo video limits. Needed in Phase 6.

## Placeholders I introduced (no action needed unless you want to set them)

- `{{NONLINEAR_RATIO_TOL}}`: when first order and Monte Carlo "disagree materially" (Section 6.3). I will propose a value from the Phase 2 curves.
- `{{DEPTH_EDGE_REL}}`, `{{NORMAL_PATCH_PX}}`, `{{MIN_GROUPS_PER_BIN}}`: set from data or with a stated reason (D-209, D-213).
- `{{TILE_SIZE}}`, `{{TILE_OVERLAP}}`: chosen on validation when B3 runs (D-310).

## Later (not needed yet)

15. (Moved to "Decisions needed now", item 1.)
16. Optional: landmark distances for `[EXTRA]` E3.

## Tooling

17. **GNU Make is not installed**, so `make` targets cannot run as written. I run the same commands directly. To get it: `winget install ezwinports.make`. CI on Linux has `make`.
