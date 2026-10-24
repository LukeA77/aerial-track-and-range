# Model card: detector and tracker

## What it is

- **Detector:** YOLO26n (Ultralytics 8.4.182), fine-tuned from Common Objects in Context (COCO) weights on the VisDrone2019 detection training set at an input size of {{RESULT:headline.json#model.imgsz|d}} pixels, for {{RESULT:headline.json#model.epochs|d}} epochs on one {{RESULT:headline.json#model.gpu|s}} graphics processing unit (GPU) ({{RESULT:headline.json#model.train_hours|.1f}} hours, library defaults otherwise). The best epoch was the last ({{RESULT:headline.json#model.best_epoch|d}}), so the model had not finished improving.
- **Tracker:** BoT-SORT from the same library, motion and overlap only (no appearance re-identification, by design), with camera-motion compensation and two confidence thresholds tuned on the validation set (D-321).
- **Exported form:** Open Neural Network Exchange (ONNX); its detections match the original exactly on the validation frames checked (D-604).

## Intended use

Research evaluation of detection, tracking and ground-plane distance estimation from low-altitude drone video of road scenes. Not intended for identifying individuals, for safety-critical decisions, or for use outside the tested conditions (see limitations).

## Classes

Trained on VisDrone's ten classes; evaluated as two groups: **person** (pedestrian, people) and **vehicle** (car, van, truck, bus).

## Performance

| Data | Measure | Person | Vehicle |
|---|---|---|---|
| VisDrone detection validation set (all ten classes) | mAP50 / mAP50-95 | {{RESULT:headline.json#model.det_val_map50|.3f}} / {{RESULT:headline.json#model.det_val_map50_95|.3f}} | (all classes) |
| VisDrone MOT validation frames | AP50 | {{RESULT:headline.json#model.mot_val_person_ap50|.3f}} | {{RESULT:headline.json#model.mot_val_vehicle_ap50|.3f}} |
| VisDrone MOT test-dev (run once) | AP50 | {{RESULT:headline.json#visdrone_test.person_ap50|.3f}} | {{RESULT:headline.json#visdrone_test.vehicle_ap50|.3f}} |
| VisDrone MOT test-dev (run once) | Tracking IDF1 / MOTA | {{RESULT:headline.json#visdrone_test.person_idf1|.3f}} / {{RESULT:headline.json#visdrone_test.person_mota|.3f}} | {{RESULT:headline.json#visdrone_test.vehicle_idf1|.3f}} / {{RESULT:headline.json#visdrone_test.vehicle_mota|.3f}} |
| AU-AIR held-out flights (cross-dataset) | AP50 at IoU 0.5 | {{RESULT:headline.json#auair.heldout_person_ap50|.3f}} | {{RESULT:headline.json#auair.heldout_vehicle_ap50|.3f}} |

AP50: average precision at an intersection over union (IoU) of 0.5. mAP50-95: mean over IoU 0.5 to 0.95. IDF1: identity F1 score. MOTA: multiple object tracking accuracy.

## Known weaknesses

- Small objects: people 16 to 32 pixels tall are tracked {{RESULT:headline.json#visdrone_test.person_recall_16_32|.0%}} of the time on test-dev.
- Night scenes, partial occlusion and dense queues of similar vehicles cause most misses and identity switches (failure gallery, `results/failures/`).
- On AU-AIR (different camera, many straight-down views) detection transfers poorly at the protocol threshold; AU-AIR's looser boxes explain part of the gap (D-512).

## Training data and licence

VisDrone2019 detection train (with {{RESULT:headline.json#data.visdrone_excluded_images|d}} images removed that share source videos with the validation and test-dev tracking clips, D-308). VisDrone states no licence; the weights are not distributed. The code is AGPL-3.0-only, matching Ultralytics.
