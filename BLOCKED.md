# Items that need Luke

Last updated: 2026-10-18.

## Data (Section 4)

1. **VisDrone image detection (train, val) is not in the data folder.** `scripts/check_data.py` looked for `VisDrone2019-DET-train` and `VisDrone2019-DET-val` (folder or `.zip`) in `Data/` and found neither. Only the three MOT zips are there. Needed for Phase 3 (detector training). Please download them or move them into `Data/`.
2. **Mid-Air: downloading** (`scripts/download_midair.py`, started 2026-10-18 at your request). Kite_training/sunny without colour images, about 2.8 GB per trajectory. It stops if free disk space falls below 10 GB, and it resumes if rerun. Progress is in `Data/midair/download_log.txt`. Delete `Data/midair/Kite_training/` when we are done with it.
3. **AU-AIR: not downloaded** (the dataset site's links are broken). Needed from Phase 4 only. When you have it, set `auair_subdir` in `configs/data.yaml`.
4. **Confirm the data root.** Your brief left the path blank. I used `Data/` inside this repository, because that is where the files are. It is git-ignored. Tell me if you want a different location.

## Paths and decisions (Section 3)

5. **`{{MOT17_REPO_PATH}}` and `{{MOT17_WEIGHTS_PATH}}`**: your brief left these blank, so they are treated as "not provided". Without the weights, baseline B1 is skipped (Section 9.2). Without the repo, Phase 3 cannot quote your MOT17 numbers.
6. **`{{TARGET_FPS}}`**: you chose "decide later". Needed in Phase 5.
7. **Licence variant**: you chose AGPL-3.0. Do you want "AGPL-3.0-only" (currently in `pyproject.toml`) or "AGPL-3.0-or-later"?
8. **`{{VOICE_SAMPLE}}`**: a sample of your writing in `docs/voice_sample.md`. Needed in Phase 6.
9. **`{{MAX_VIDEO_MB}}`, `{{VIDEO_LENGTH_S}}`**: demo video limits. Needed in Phase 6.

## New placeholder introduced in Phase 1 (no action needed now)

- `{{NONLINEAR_RATIO_TOL}}` (`configs/uncertainty.yaml`): Section 6.3 says to switch to the Monte Carlo interval where the two methods "disagree materially", but gives no threshold. I will propose a value from the Phase 2 Mid-Air curves and record the evidence. Tell me if you would rather set it yourself.

## Later (not needed yet)

10. Label AU-AIR clip tilt categories from contact sheets (Section 8.2, Phase 4).
11. Optional: landmark distances for `[EXTRA]` E3.

## Tooling

12. **GNU Make is not installed** on this machine, so `make lint test` cannot run as written. I ran the same commands directly (see PROGRESS.md). To get `make`, for example: `winget install ezwinports.make`. Alternatively, run the commands in the Makefile by hand. CI on Linux has `make`.
