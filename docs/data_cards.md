DRAFT

# Data cards

What each dataset is, how it is used here, and its licence and terms as checked at build time. Counts and checksums are not typed here. They come from `results/data_check.json` (counts and schema) and `results/data_manifest.json` (file counts, bytes and SHA-256 tree hashes per folder). No data is redistributed in this repository.

## VisDrone2019 (Pillar A: tracking)

- **Source:** https://github.com/VisDrone/VisDrone-Dataset (links to Google Drive and Baidu). Collected by the AISKYEYE team, Lab of Machine Learning and Data Mining, Tianjin University.
- **Citation:** Zhu, P., Wen, L., Du, D., Bian, X., Fan, H., Hu, Q. and Ling, H. (2021) 'Detection and tracking meet drones challenge', *IEEE Transactions on Pattern Analysis and Machine Intelligence*, 44(11), pp. 7380–7399. This is the citation block in the repository README, read 2026-10-19; verify it against the journal before the brief.
- **Licence and terms (checked 2026-10-19):** the repository has no licence file (GitHub reports none), and the README states no terms of use. The README notes that test-dev annotations are available and that "researchers can use test-dev to publish papers". With no stated licence, this project uses the data for research evaluation only, does not redistribute any of it, and publishes only code, metrics and figures. Thumbnails in a failure gallery or video should be kept minimal; confirm with Luke before publishing any image.
- **Used:** MOT train, val and test-dev (tracking); DET train and val (detector training and selection). Not used: DET test-dev and the challenge test sets.
- **Splits (Section 4.5):** DET train for training; DET val for model selection; MOT val for tracker tuning and the pixel-noise fit; MOT test-dev once, at the end.
- **Known issue (D-308):** some DET images come from the same source videos as MOT val and test-dev clips. Those images are excluded from training and selection.
- **Annotation schema:** verified on the real files by `scripts/check_data.py`. MOT has 10 integer columns and DET has 8; category 0 marks ignored regions.

## Mid-Air (Pillar B: ranging ground truth)

- **Source:** https://midair.ulg.ac.be (selective download form); example scripts at https://github.com/montefiore-ai/midair-dataset.
- **Citation:** Fonder, M. and Van Droogenbroeck, M. (2019) Mid-Air, CVPR Workshops. Verify the full reference before the brief.
- **Licence:** Creative Commons Attribution-NonCommercial-ShareAlike 4.0 (CC BY-NC-SA 4.0), as stated in build.md. Re-check it on the dataset page before release. Attribute; do not redistribute the data; publish code, metrics and figures only; publish no derived dataset.
- **Used:** climate Kite_training/sunny; depth, segmentation and normals for the left camera, plus `sensor_records.hdf5`. Colour images are not downloaded (not needed for geometry validation).
- **Splits:** by trajectory, seed 0, 50 / 20 / 30 % for development, calibration and test (`results/splits.json`, D-208).
- **Conventions resolved by test:** D-201 to D-207 (radial depth, wxyz body-to-world quaternion, level forward mount, sky sentinel, normals decoding).
- **Limitation:** synthetic, with no people or vehicles. It validates the geometry, not the detector.

## AU-AIR (Pillar B: real footage)

Not downloaded (see BLOCKED.md). Licence per build.md: CC BY. Credit Bozcan and Kayacan (2020), ICRA.
