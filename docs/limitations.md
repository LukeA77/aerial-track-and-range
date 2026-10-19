DRAFT. Structure and known-by-design limits only. Measured limits are added from results files via `{{RESULT:...}}` tokens once the final runs exist (R1, R6).

# Limitations

## Ranging (Pillar B)

### Known by design

- **Flat-ground assumption.** The deployed method intersects each ray with one horizontal plane. Where terrain is not flat, the estimate is biased, and the bias grows as the ray approaches the horizon. The slope experiment (H4) measures how much error this explains; it does not remove it.
- **Ground above the camera cannot be ranged.** A horizontal plane below the camera cannot represent ground seen above it, such as hills ahead of a low-flying drone. Those estimates are reported as invalid, and the valid fraction is reported alongside every accuracy figure.
- **Height above the plane must be known.** The `oracle_plane` mode is an upper bound that uses ground truth. The `relative_altitude` mode (a take-off-relative altimeter) inherits every change in terrain height since take-off. Real systems would need a terrain model or a rangefinder for this.
- **Uncertainty covers sensor noise, not terrain.** The propagated sigma models pixel, altitude, attitude, tilt and focal-length noise. It does not model terrain relief, so it is expected to be over-confident where terrain dominates. This is tested (H3), and a single recalibration scalar is fitted on the calibration split only.
- **Sensor-noise levels on Mid-Air are a sweep, not a sensor model.** Headline noise values come from AU-AIR hover segments (Section 8.5).

### Mid-Air validation scope

- Synthetic imagery from one climate (Kite_training/sunny) with no people or vehicles, so it validates geometry, not detection.
- Ground-truth pixels are sampled from ground classes only, with depth discontinuities and image borders excluded (D-209).
- Forward-looking camera, low altitude (heights above the oracle plane are reported per bin).
- Intervals resample whole trajectories, and there are few trajectories per split, so intervals are wide.
- The convention checks (D-201 to D-207) looked at two test-split trajectories before the split existed. Nothing was fitted there (D-208).

### Measured limits (to be filled from results)

- Usable depression angle: `{{MIN_DEPRESSION_DEG}}`. Usable range: `{{MAX_RANGE_M}}`. Rule in D-311.
- Calibration before and after recalibration on the test split: from `results/midair/test/calibration_applied.json`.
- Reliability flag precision and recall on the test split: same file.

## Tracking (Pillar A)

- Benchmarks differ: comparisons with MOT17 numbers show a domain gap; they are not a like-for-like comparison.
- VisDrone has no stated licence; data are used for research evaluation only and not redistributed (data cards).
- Some VisDrone DET images share source videos with MOT val and test-dev. Those images are excluded from training and selection (D-308), but other near-duplicate content cannot be ruled out entirely.
- No appearance re-identification, by design. Identity switches under long occlusion are expected.
- Training compute: CPU only on the development machine, unless Luke chooses otherwise (BLOCKED.md).

## Edge budget (Pillar C)

- One CPU model (`results/env.json`); no claims about other hardware.
- The budget is set by `{{TARGET_FPS}}`, still to be chosen.

## Real footage (AU-AIR)

- Not yet available. Claims there will be about plausibility and repeatability only, never accuracy (Section 8).
