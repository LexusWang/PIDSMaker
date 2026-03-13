# Training Full Flow: Train Once, Test on Multiple Attacks

## Overview

Train a model **once** on benign data, then run inference on each attack variant in ~1-2 minutes per attack. The pipeline automatically skips all training stages for attack variants and only computes what is new (the attack test graph).

---

## How It Works

All attack-variant datasets (`training_full_aa23_341a`, etc.) share the same database, train files, and config as `training_full`. This means their pipeline hashes for training stages are identical. The optimized pipeline exploits this:


| Stage                 | `training_full`   | `training_full_aa23_341a` | Mechanism                                                                 |
| --------------------- | ----------------- | ------------------------- | ------------------------------------------------------------------------- |
| `build_graphs`        | runs              | runs (~10s)               | must run to build attack test graph (e.g. `graph_65`)                     |
| `transformation`      | runs              | runs (~1s)                | must run to include attack test graph                                     |
| `feat_training`       | runs              | **skipped**               | path redirected to base's dir → `done.txt` found                          |
| `feat_inference`      | runs (all splits) | **fast** (~30s)           | symlinks train/val files from base; embeds only new nodes from `graph_65` |
| `graph_preprocessing` | runs              | runs                      | needs attack test data                                                    |
| `gnn_training`        | runs              | **skipped**               | path redirected to base's dir → `done.txt` found                          |
| `gnn_inference`       | runs              | runs                      | attack-specific, necessary                                                |
| `evaluation`          | runs              | runs                      | attack-specific, necessary                                                |


**The redirect works as follows:** each attack-variant dataset has `provattack_base_dataset = "training_full"` in `config.py`. `set_task_paths` uses the base dataset name when building artifact paths for training-only stages. Since the hashes are identical and the base has already written `done.txt` there, the framework sees those stages as complete.

---

## Quick Start

### Step 1 — Create the unified database (one time)

```bash
# In postgres container
docker exec -it postgres bash
psql -U postgres -h localhost -p 5432 -c "CREATE DATABASE training_full;"
exit

# In pidsmaker container
docker exec -it pidsmaker-pids bash
python -m dataset_preprocessing.provattack.create_database flash training_full
```

This loads benign data (`benign_1_5`, `benign_1_7`, `benign_1_8`, `benign_1_9`) and attack data (`AA23_341A`, `AA24_046A`, `ALPHVBlackcat`, `PhobosRansomware`) into a single database.

### Step 2 — Train the base model (one time, ~15 min)

```bash
python pidsmaker/main.py flash training_full --stop_after=gnn_training
```

`--stop_after=gnn_training` skips inference and evaluation on the benign-only dataset, which has no meaningful ground truth. The trained model is saved to:

```
artifacts/detection/gnn_training/<hash>/training_full/trained_models/model_epoch_N.pt
```

### Step 3 — Run inference per attack (~1-2 min each)

```bash
python pidsmaker/main.py flash training_full_aa23_341a
python pidsmaker/main.py flash training_full_aa24_046a
python pidsmaker/main.py flash training_full_alphvblackcat
python pidsmaker/main.py flash training_full_phobosransomware
```

Each run:

1. Runs `build_graphs` and `transformation` (~10s) to build the attack test graph (e.g. `graph_65`). Skips `feat_training` and `gnn_training` (redirected to base dataset paths).
2. Runs `feat_inference` in fast mode: symlinks pre-computed train/val edge-embed files from the base, then embeds only the new nodes from the attack test graph.
3. Runs `graph_preprocessing`, `gnn_inference`, and `evaluation` on the attack test data.
4. Saves results to `artifacts/detection/evaluation/<hash>/<dataset>/precision_recall_dir/`.

---

## What `feat_inference` Does in Fast Mode

For each split's graph files:

1. **Train/val files** (e.g. `graph_4`, `graph_5`, `graph_6`, `graph_7`, `graph_8`): These were already computed in the `training_full` run. The attack variant's `feat_inference` creates symlinks pointing to those files — no recomputation.
2. **Test file** (e.g. `graph_65`): Not in the base. The cached `indexid2vec.pkl` (node embeddings) from the base is loaded, then only nodes that appear in `graph_65` but are absent from the cache are embedded ("delta embedding"). Edge embeddings for `graph_65` are then computed normally.

---

## Expected Timings


| Stage                 | Before optimization | After optimization |
| --------------------- | ------------------- | ------------------ |
| `build_graphs`        | ~10s                | ~10s               |
| `transformation`      | ~1s                 | ~1s                |
| `feat_training`       | ~5 min              | Instant (skipped)  |
| `feat_inference`      | ~8 min              | ~30s               |
| `graph_preprocessing` | Instant             | Instant            |
| `gnn_training`        | ~1 min              | Instant (skipped)  |
| `gnn_inference`       | ~30s                | ~30s               |
| `evaluation`          | Fast                | Fast               |
| **Total per attack**  | **~15 min**         | **~1-2 min**       |


---

## Dataset Configs

All configs are defined in `pidsmaker/config/config.py`:


| Config key                       | `test_files`                | `provattack_base_dataset` |
| -------------------------------- | --------------------------- | ------------------------- |
| `training_full`                  | `graph_5` (val placeholder) | `""` (no redirect)        |
| `training_full_aa23_341a`        | `graph_65`                  | `"training_full"`         |
| `training_full_aa24_046a`        | TODO                        | `"training_full"`         |
| `training_full_alphvblackcat`    | TODO                        | `"training_full"`         |
| `training_full_phobosransomware` | TODO                        | `"training_full"`         |


---

## Completing TODO Attack Configs

For each unfinished attack, fill in three fields in `config.py` once you know the attack day and ground truth:

```python
"training_full_<attack>": {
    ...
    "start_end_day_range": (4, <attack_day + 1>),
    "test_files": ["graph_<attack_day>"],
    "ground_truth_relative_path": ["PROVATTACK/<attack>_0_hop.csv"],
    "attack_to_time_window": [
        ["PROVATTACK/<attack>_0_hop.csv", "<start_timestamp>", "<end_timestamp>"],
    ],
    "provattack_base_dataset": "training_full",   # already set, do not remove
}
```

To find the attack day from a raw JSONL file:

```bash
head -1 /rawdata/<attack>.jsonl | python -c "
import sys, json
from datetime import datetime
event = json.loads(sys.stdin.read())
ts = event.get('timestamp') or event.get('time')
print(datetime.fromtimestamp(int(ts)/1e9).strftime('%Y-%m-%d'))
"
```

No other changes are needed — the redirect and symlink logic are driven entirely by `provattack_base_dataset`.

---

## Adding a New Attack Variant

To add a completely new `training_full_<newattack>` dataset:

1. `**pidsmaker/config/config.py**` — add a new entry with `provattack_base_dataset: "training_full"` and the correct `test_files`, `ground_truth_relative_path`, and `attack_to_time_window`.
2. `**pidsmaker/utils/dataset_utils.py**` — add `"training_full_<newattack>"` to `PROVATTACK_DATASETS`.
3. Run: `python pidsmaker/main.py flash training_full_<newattack>`

No database changes needed — all attack data is already in the `training_full` database.

---

## Re-running After Config Changes

If you update a config (e.g. add `test_files`) and the attack variant has already run, force inference to re-run:

```bash
python pidsmaker/main.py flash training_full_aa24_046a --force_restart gnn_inference
```

If you need to recompute node embeddings for a changed test graph:

```bash
python pidsmaker/main.py flash training_full_aa24_046a --force_restart feat_inference
```

---

## Troubleshooting

**`feat_training` or `gnn_training` re-runs instead of being skipped**

The base dataset's artifact paths must exist and contain `done.txt`. Verify:

```bash
ls artifacts/featurization/training_full/feat_training/*/done.txt
ls artifacts/detection/gnn_training/*/training_full/done.txt
```

If missing, run Step 2 first: `python pidsmaker/main.py flash training_full --stop_after=gnn_training`

`**feat_inference` fails with a missing node in `indexid2vec**`

This should not happen — delta embedding adds all new nodes from the test split before edge embedding runs. If it does occur, force `feat_inference` to restart:

```bash
python pidsmaker/main.py flash training_full_aa23_341a --force_restart feat_inference
```

**Symlinks to base edge-embed files are broken**

The base's `feat_inference` must have completed. Run:

```bash
python pidsmaker/main.py flash training_full --stop_after=feat_inference
```

Then re-run the attack variant.