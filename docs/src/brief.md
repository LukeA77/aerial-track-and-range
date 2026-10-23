**DRAFT for Luke to review section by section. References marked [verify] must be checked against their primary sources before publication.**

# Tracking and ranging from a drone camera, with honest uncertainty, on a laptop CPU

*Discipline: computer vision and robotics perception engineering. Audience: senior engineers at an electro-optical tracking company.*

## Abstract

I built a pipeline that takes video from a single drone camera, detects and tracks people and vehicles, estimates how far away each one is with an error bar, and runs on a laptop central processing unit (CPU). On synthetic flights with exact ground truth, estimating the ground from the drone's own motion gave a median distance error of {{RESULT:headline.json#midair_test.terrain_median|.1%}}, against {{RESULT:headline.json#midair_test.flat_alt_median|.0%}} for a flat ground plane with an altimeter, and calibrated 90 % error bars held {{RESULT:headline.json#midair_test.cov_cal_90|.0%}} of the time. On real footage, stationary vehicles' positions repeated to {{RESULT:headline.json#auair.heldout_rel_all|.1%}} of their distance. The pipeline sustains {{RESULT:headline.json#edge.fast_fps|.0f}} frames per second, at a stated cost in accuracy.

## Problem

A camera gives direction, not distance. To turn a pixel into a range, I need to know where the ground is relative to the camera, and every error in height, attitude or ground shape becomes a range error that grows towards the horizon. So I wanted the system to report not only a range but how far to trust it, and to say when not to trust it at all.

## Method

1. **Detect and track.** I fine-tuned a YOLO26n detector on VisDrone2019 and used the BoT-SORT tracker with camera-motion compensation. I left out appearance re-identification on purpose: the tracker uses motion and overlap only.
2. **Range.** I cast a ray from the camera through each box's ground-contact point and intersect it with the ground. The ground is either a flat plane or a local surface I triangulate from image features tracked across frames, using the drone's known poses (terrain from motion). I chose the second because the first needs the height above the ground, which a real drone does not know.
3. **Uncertainty.** I propagate sensor noise to first order and by Monte Carlo, calibrate the intervals on separate flights (split conformal prediction), and train a small reliability flag on features I can explain.
4. **Speed and heading.** A constant-velocity Kalman filter per track, in world coordinates.
5. **Real time.** ONNX export, a smaller input, detection on every second frame, and detection running alongside tracking.

## Experiments and results

| Pillar | Data (each test split run once) | Result |
|---|---|---|
| A: tracking | VisDrone test-dev | Identity F1 (IDF1) {{RESULT:headline.json#visdrone_test.vehicle_idf1|.3f}} vehicles, {{RESULT:headline.json#visdrone_test.person_idf1|.3f}} people |
| B: ranging | Mid-Air test flights (synthetic) | Median error {{RESULT:headline.json#midair_test.terrain_median|.1%}} (terrain from motion), {{RESULT:headline.json#midair_test.flat_true_median|.1%}} (flat plane, true height), {{RESULT:headline.json#midair_test.flat_alt_median|.0%}} (flat plane, altimeter) |
| B: real footage | AU-AIR held-out flights | Repeatability {{RESULT:headline.json#auair.heldout_rel_all|.1%}} of range (no ground truth, so repeatability, not accuracy) |
| C: speed | Laptop CPU ({{RESULT:headline.json#edge.cpu|s}}) | {{RESULT:headline.json#edge.accurate_fps|.1f}} fps at IDF1 {{RESULT:headline.json#edge.accurate_idf1|.3f}}; {{RESULT:headline.json#edge.fast_fps|.1f}} fps sustained at IDF1 {{RESULT:headline.json#edge.fast_idf1|.3f}} (validation) |

Figures: `results/midair/test/figures/` (error against depression and slope), `results/auair/figures/`, `results/edge/figures/pareto.png`.

**What I tested, and what I found.**
- **H1, off-the-shelf models degrade on aerial footage and adapting them recovers part of the loss: partly supported.** On validation, mean IDF1 went from {{RESULT:headline.json#visdrone_val.b0_mean_idf1|.3f}} (pretrained, ByteTrack) to {{RESULT:headline.json#visdrone_val.b0_cmc_mean_idf1|.3f}} with camera-motion compensation, and to {{RESULT:headline.json#visdrone_val.b2_960_tuned|.3f}} after fine-tuning and tuning. Tiled inference did not help tracking ({{RESULT:headline.json#visdrone_val.b3_tuned|.3f}}). I compared the baselines on validation only; test-dev ran once, for the final setting.
- **H2, error grows towards the horizon as propagation predicts: supported.** First-order and Monte Carlo predictions match the measured noise effect above 5° of depression; below 2° the error becomes non-linear (Monte Carlo {{RESULT:headline.json#midair_test.mc_over_fo_below_2deg|.0f}} times first order).
- **H3, the uncertainty is calibrated, or can be made so with one scalar, and a flag catches the worst errors: partly supported.** Sensor noise alone is far too confident (standard deviation of the standardised error {{RESULT:headline.json#midair_test.flat_z_std_before|.1f}} for the flat plane, ideal 1), because the ground's shape dominates, and one scalar cannot fix that. Conformal calibration brings 90 % intervals to {{RESULT:headline.json#midair_test.cov_cal_90|.0%}}; the flag's area under the receiver operating characteristic curve (AUROC) is {{RESULT:headline.json#midair_test.flag_auroc|.2f}}.
- **H4, the flat-ground assumption breaks on slopes: supported.** Flat-plane error grows from {{RESULT:headline.json#midair_test.flat_err_slope_0_5|.1%}} to {{RESULT:headline.json#midair_test.flat_err_slope_45_90|.1%}} with slope; terrain from motion stays at or below {{RESULT:headline.json#midair_test.terrain_err_slope_30_45|.1%}} up to 45°.
- **H5, real time on a CPU at a small accuracy cost: partly supported.** I reached 30 frames per second in throughput ({{RESULT:headline.json#edge.fast_fps|.1f}}), but not in per-frame delay ({{RESULT:headline.json#edge.fast_latency_median_ms|.0f}} ms median), and IDF1 fell from {{RESULT:headline.json#edge.accurate_idf1|.3f}} to {{RESULT:headline.json#edge.fast_idf1|.3f}}.

## Where it breaks

Near the horizon, where the error becomes non-linear; on slopes above 45°; on small people ({{RESULT:headline.json#visdrone_test.person_recall_16_32|.0%}} tracked at 16 to 32 pixels tall); in the tail of terrain-from-motion errors (one in ten above {{RESULT:headline.json#midair_test.terrain_p90|.0%}}); and on real footage, where I had to infer the camera model and {{RESULT:headline.json#auair.vehicle_share_above_70|.0%}} of vehicle speeds are implausible. The full list is in `docs/limitations.md`.

## With real sensors

Several of the largest error sources I measured would go away with better telemetry: a recorded camera tilt and lens calibration, a referenced altitude, synchronised time stamps, and a terrain model. A laser rangefinder or radar would measure range directly. The per-object uncertainty here is what would let one filter weight the camera against the active sensor, and fall back to the camera when the active sensor drops out. I have not tested target hardware or thermal footage.

## References

Aharon, N., Orfaig, R. and Bobrovsky, B.-Z. (2022) 'BoT-SORT: robust associations multi-pedestrian tracking', arXiv:2206.14651. [verify]
Bernardin, K. and Stiefelhagen, R. (2008) 'Evaluating multiple object tracking performance: the CLEAR MOT metrics', *EURASIP Journal on Image and Video Processing*. [verify]
Bozcan, I. and Kayacan, E. (2020) 'AU-AIR: a multi-modal unmanned aerial vehicle dataset for low altitude traffic surveillance', *IEEE International Conference on Robotics and Automation*. [verify]
Fonder, M. and Van Droogenbroeck, M. (2019) 'Mid-Air: a multi-modal dataset for extremely low altitude drone flights', *CVPR Workshops*. [verify]
Lei, J., G'Sell, M., Rinaldo, A., Tibshirani, R. J. and Wasserman, L. (2018) 'Distribution-free predictive inference for regression', *Journal of the American Statistical Association*. [verify]
Ristani, E., Solera, F., Zou, R., Cucchiara, R. and Tomasi, C. (2016) 'Performance measures and a data set for multi-target, multi-camera tracking', *ECCV Workshops*. [verify]
Zhang, Y. et al. (2022) 'ByteTrack: multi-object tracking by associating every detection box', *ECCV*. [verify]
Zhu, P., Wen, L., Du, D., Bian, X., Fan, H., Hu, Q. and Ling, H. (2021) 'Detection and tracking meet drones challenge', *IEEE Transactions on Pattern Analysis and Machine Intelligence*, 44(11), pp. 7380-7399. [verify]

Datasets: VisDrone2019 (no stated licence; research evaluation only), Mid-Air (CC BY-NC-SA 4.0), AU-AIR (used as non-commercial, attributed). Software: Ultralytics (AGPL-3.0).
