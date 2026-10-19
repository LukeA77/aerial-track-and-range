# Runbook: finishing the evaluations once data and decisions are in

Commands run from the repository root with the project virtual environment. On Windows, use `.venv/Scripts/python`; elsewhere, `.venv/bin/python`. Test splits run **once**, after every setting is frozen (R5), and the scripts refuse to run them without `--final`.

## Mid-Air (Phase 2)

1. Finish the download. This resumes and skips anything done:
   `python scripts/download_midair.py --only Kite_training/sunny --skip color_left --min-free-gb 10`
2. Check the data: `python scripts/check_data.py`. Then record checksums for the data cards with `python scripts/data_manifest.py`, which is heavy on disk; run it when nothing else is reading the data.
3. Development and calibration evaluation and analysis: `make midair-eval`. Without make, run the five commands under `midair-eval` in the Makefile.
4. Review the development figures in `results/midair/development/figures/`. Revisit the D-209 sampling values only if bins are under-populated, and record any change.
5. Decide `{{ERR_THRESHOLD_FRAC}}` (BLOCKED.md), then fit on calibration:
   `python scripts/midair_calibrate.py --level mid --base oracle_plane`
6. Freeze. Record the fitted values from `results/midair/calibration_fit.json` in `configs/uncertainty.yaml` and `configs/geometry.yaml`, with sources.
7. Test split, once:

   ```
   python scripts/midair_eval.py --split test --final
   python scripts/midair_analyse.py --split test --final
   python scripts/midair_calibrate.py --level mid --base oracle_plane --apply-test --final
   ```

## VisDrone (Phase 3)

1. Prepare the data: `make visdrone-prep` (the overlap check, then the MOT ground truth and the YOLO set with the leakage exclusion, D-308).
2. B0 is done for YOLO26n at 640 with ByteTrack. Other B0 variants follow the same pattern:
   `python scripts/track_eval.py --run B0_<tag> --weights weights/yolo26n.pt --class-map coco --imgsz 640 --tracker configs/trackers/bytetrack.yaml`
3. B2, fine-tuning. This needs a compute decision (BLOCKED.md):
   `python scripts/train_detector.py --name B2_yolo26n_640 --model yolo26n.pt --imgsz 640`
   Then track with `--weights cache/train/B2_yolo26n_640/weights/best.pt --class-map visdrone10`.
4. B3 tiled inference, the tracker grid, and the pixel-noise fit (`{{SIGMA_PIX_MODEL}}`) are all on val.
5. Test-dev, once: rerun the frozen configurations with `--split test-dev --final`.
