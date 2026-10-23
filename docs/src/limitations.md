**DRAFT.** Measured limits are filled from `results/` (R1); every limit here is also reported in the brief (R6).

# Limitations

## Distance estimation (ranging)

### Measured on the Mid-Air test flights (synthetic, run once)

- **Flat ground fails in practice.** With the true height above the ground plane (an unrealistic best case), the median distance error is {{RESULT:headline.json#midair_test.flat_true_median|.1%}}; with a take-off altimeter (realistic) it is {{RESULT:headline.json#midair_test.flat_alt_median|.0%}}, with only {{RESULT:headline.json#midair_test.flat_alt_valid|.0%}} of estimates valid. On one test flight the altimeter method had no valid estimate at all: the drone flew below its take-off height (D-607).
- **Slopes (hypothesis H4).** Flat-ground error grows from {{RESULT:headline.json#midair_test.flat_err_slope_0_5|.1%}} on slopes under 5° to {{RESULT:headline.json#midair_test.flat_err_slope_45_90|.1%}} on slopes over 45°.
- **Near the horizon (H2).** Below 2° of depression the error distribution becomes strongly non-linear: the Monte Carlo prediction is {{RESULT:headline.json#midair_test.mc_over_fo_below_2deg|.1f}} times the first-order one, so first-order error bars are not trustworthy there.
- **Terrain from motion still has a heavy tail.** The median error is {{RESULT:headline.json#midair_test.terrain_median|.1%}}, but one estimate in ten is more than {{RESULT:headline.json#midair_test.terrain_p90|.0%}} off.
- **Error bars fall short.** After calibration on separate flights, nominal 68 %, 90 % and 95 % intervals contain the truth {{RESULT:headline.json#midair_test.cov_cal_68|.0%}}, {{RESULT:headline.json#midair_test.cov_cal_90|.0%}} and {{RESULT:headline.json#midair_test.cov_cal_95|.0%}} of the time: better than without calibration, but still short (H3).
- **The reliability flag is moderate.** Area under the receiver operating characteristic curve (AUROC) {{RESULT:headline.json#midair_test.flag_auroc|.2f}} on test flights ({{RESULT:headline.json#midair_test.flag_auroc_dev|.2f}} in development); precision {{RESULT:headline.json#midair_test.flag_precision|.2f}}, recall {{RESULT:headline.json#midair_test.flag_recall|.2f}}.

### Mid-Air scope

- Synthetic imagery from one climate, with no people or vehicles: it validates geometry, not detection.
- Intervals resample whole flights, and there are {{RESULT:headline.json#midair_test.n_test_flights|d}} test flights, so intervals are wide.

## Real footage (AU-AIR)

- **No ground truth.** AU-AIR records no target positions or speeds, so its results are repeatability and plausibility, never accuracy (build.md Section 8).
- **The camera model is inferred.** Focal length {{RESULT:headline.json#auair.focal_px|.0f}} pixels (95 % interval {{RESULT:headline.json#auair.focal_ci.0|.0f}} to {{RESULT:headline.json#auair.focal_ci.1|.0f}}), principal point assumed at the image centre, lens distortion not fitted (the central part of the image is used where it matters), camera tilt not recorded and estimated from motion (it agreed with independent checks where they were possible, D-514; available on {{RESULT:headline.json#auair.tilt_frame_share|.0%}} of frames, because it needs the drone to move).
- **The altimeter drifts** by metres within a flight; the offset was measured only on two calibration flights (weakly on one).
- **Shallow views.** Held-out repeatability is {{RESULT:headline.json#auair.heldout_rel_dep_20_40|.1%}} of range at 20-40° below the horizon but {{RESULT:headline.json#auair.heldout_rel_dep_0_10|.1%}} below 10°.
- **Implausible speeds.** {{RESULT:headline.json#auair.vehicle_share_above_70|.0%}} of vehicle tracks read above 70 km/h at a junction where that is implausible; likely causes (shallow views, identity switches) are not tested.
- **Detector transfer.** The VisDrone-trained detector scores poorly on AU-AIR at the protocol threshold (vehicle AP50 {{RESULT:headline.json#auair.heldout_vehicle_ap50|.2f}}, people {{RESULT:headline.json#auair.heldout_person_ap50|.2f}} on held-out flights); part of this is AU-AIR's looser annotation boxes (D-512).
- **Data:** one drone model, one site (a junction in Aarhus), heights of {{RESULT:headline.json#auair.alt_min_m|.0f}} to {{RESULT:headline.json#auair.alt_max_m|.0f}} m, short ranges. AU-AIR's annotations are not consistent from frame to frame (D-516).

## Tracking (VisDrone)

- **Small objects.** People 16 to 32 pixels tall are found {{RESULT:headline.json#visdrone_test.person_recall_16_32|.0%}} of the time, against {{RESULT:headline.json#visdrone_test.person_recall_128|.0%}} above 128 pixels.
- **The tuned tracker trades recall for fewer false tracks**: it misses more people in exchange for far fewer identity switches (D-321).
- No appearance re-identification, by design; identity switches under occlusion remain the main tracking error (failure gallery, D-321).
- Comparisons with MOT17 numbers show a domain gap and are not like-for-like.
- VisDrone states no licence; it is used for research evaluation only and not redistributed.

## Speed (edge budget)

- **One laptop CPU** ({{RESULT:headline.json#edge.cpu|s}}); no claims about other hardware.
- **30 frames per second is reached in throughput, not in delay.** The fast setting sustains {{RESULT:headline.json#edge.fast_fps|.1f}} frames per second, but each frame's result arrives {{RESULT:headline.json#edge.fast_latency_median_ms|.0f}} ms after it is read (99th percentile {{RESULT:headline.json#edge.fast_latency_p99_ms|.0f}} ms), and its tracking accuracy is lower (IDF1 {{RESULT:headline.json#edge.fast_idf1|.3f}} against {{RESULT:headline.json#edge.accurate_idf1|.3f}}).
- **8-bit integer (INT8) quantisation was slower** on this CPU ({{RESULT:headline.json#edge.int8dyn_detect_ms|.0f}} ms per detection with dynamic INT8 against {{RESULT:headline.json#edge.fp32_detect_ms|.0f}} ms in 32-bit floating point), so it is not used.
- Benchmarks ran with the editor open (measured background load is recorded in each benchmark file).
