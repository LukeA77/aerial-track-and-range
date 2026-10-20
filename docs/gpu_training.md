# Training the detector on a free Kaggle GPU (step by step)

This trains baseline B2: our detector, fine-tuned on drone images. It takes about 1 hour per pass on the laptop CPU, so a cloud GPU is much faster. You do the upload and the run; the project never uploads anything itself.

## 1. The file to upload (already made)

- `cache/gpu_package/visdrone_yolo.zip`, about 1.6 GB.
- Its fingerprint (SHA-256) is in `cache/gpu_package/manifest.json`. You don't need to check it; it's there if anything looks wrong.
- It contains 6,414 training images and 527 validation images. The 78 images that overlap the test videos are already removed.

## 2. Put it on Kaggle as a PRIVATE dataset

1. Sign in at https://www.kaggle.com, then go to **Datasets → New Dataset**.
2. Drag in `visdrone_yolo.zip` and name it `visdrone-yolo`.
3. **Set visibility to Private.** VisDrone has no stated licence, so it must not be shared publicly.
4. Click **Create**. Kaggle unzips it for you, which takes a few minutes.

## 3. Run the training

1. Go to **Code → New Notebook**.
2. **Switch the GPU on.** In the right-hand panel, open **Session options** and set **Accelerator** to **GPU T4 x2** or **GPU P100**.
   - If no GPU option appears, verify your phone number in your Kaggle account settings; Kaggle only allows GPUs after that.
3. Also in the panel, under **Input → Add Input**, add your private `visdrone-yolo` dataset.
4. In the panel, turn **Internet** on.
5. Copy the whole of `gpu/train_b2_kaggle.py` into the first cell.
6. Run it in the background so it keeps going when you close the browser: click **Save Version**, choose **Save & Run All (Commit)**, then **Save**. The run continues on Kaggle's side (up to Kaggle's session limit), and its outputs are kept with that version.
7. Check it's really using the GPU, by opening the running version's log:
   - near the top, `device:` must name a GPU (for example `Tesla T4`). The script now stops with "NO GPU FOUND" if there is none;
   - in the training lines, the `GPU_mem` column must show a value above `0G`;
   - each pass (epoch) should take minutes, not an hour.
8. It trains for at most 50 passes and stops early once the validation score stops improving (D-315).

## 4. Bring the results back

1. When it finishes, download `B2_yolo26n_640_outputs.zip`.
2. If you used Save Version, the file is in that version's **Output** tab.
3. Unzip it into this project's `cache/train/` folder, so that you have `cache/train/B2_yolo26n_640/weights/best.pt`.
4. Tell Claude. The next steps (scoring on the validation videos, tracking, the before/after comparison) run locally from there.

## Costs

- Kaggle's GPU time is free within a weekly quota, which should be enough for this run.
- If you choose a paid service instead, the same script works on Colab: upload the zip to Google Drive, unzip it in the notebook, and run the script.
