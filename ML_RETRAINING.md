# ML Retraining — How To

## When to retrain

Retrain when you have enough new settled picks to meaningfully update the models. A rough guide:
- Every 3–6 months post-launch
- Or when you notice model performance drifting on the Results page (CLV win rate dropping, ROI diverging from expected)

---

## What the models do

| File | Model | Purpose |
|------|-------|---------|
| `models/sigma_tweedie.pkl` | Tweedie regressor | Predicts sigma (line movement magnitude) |
| `models/logit_bag.pkl` | Bagged logistic regression | Predicts CLV probability |
| `models/clv_meta.json` | Metadata | Feature names, thresholds used at training time |
| `models/sigma_design.json` | Metadata | Feature names for sigma model |

---

## The retraining workflow

### 1. Make sure snapshots are up to date
Your Windows Task Scheduler pulls daily `.parquet` files to `./snapshots/` every morning at 9 AM. Before retraining, confirm the folder has recent files:
```
ls snapshots/
```

### 2. Run your retraining script locally
Point your retraining script at `./snapshots/` as the data source. It should read all parquets, train updated models, and write the outputs back to `models/`:
```
python retrain.py --data ./snapshots/ --output ./models/
```
*(exact command depends on your retraining script)*

### 3. Verify the new models locally
Run the test suite to confirm the new `.pkl` files load correctly and produce sensible output:
```
python _test_v2_pipeline.py
```
All 35 tests should pass. If any fail, do not push.

### 4. Commit and push the updated model files
```
git add models/
git commit -m "Retrain models on data through YYYYMMDD"
git push
```

### 5. Railway auto-redeploys
Railway detects the push and redeploys the worker. The new models are live on the next poll cycle — no manual action needed.

---

## Important constraints

- **scikit-learn version** — models must be trained with `scikit-learn < 1.5` (pinned in `requirements.txt`). If you retrain on a newer version the `.pkl` files will crash on Railway. Check before retraining:
  ```
  python -c "import sklearn; print(sklearn.__version__)"
  ```
- **Cross-platform pickle** — the `_loss` shim at the top of `bet_scheduler7.py` handles the Windows→Linux difference. As long as you stay on `scikit-learn < 1.5` this is already handled.
- **Never regenerate model files without running the test suite first.** The models are loaded at Railway startup — a broken `.pkl` takes down the whole worker.
- **Do not retrain on `current_picks` data** — that table only has live ungraded picks. Use `./snapshots/` (raw board data) and `settled_picks` (graded outcomes) as your training sources.

---

## Rollback

If a retrained model causes issues in production, rolling back is just reverting the commit:
```
git revert HEAD
git push
```
Railway redeploys with the previous model files immediately.
