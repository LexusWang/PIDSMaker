# Changelog

## 2026-03-12 — Eliminate PROVATTACK stage redundancy

Redirect `feat_training` and `gnn_training` for PROVATTACK attack variants to the base dataset's artifact paths so they are skipped. `build_graphs` and `transformation` run per-variant (~10s each) to build the attack test graph (e.g. `graph_65`) which the base dataset never builds. `feat_inference` symlinks pre-computed train/val edge-embed files from the base and only embeds nodes/edges for the new attack graph. Reduces attack-variant run time from ~15 min to ~1-2 min.

**Files changed:**
- `pidsmaker/config/config.py` — added `provattack_base_dataset` field to `training_full` (empty) and four attack-variant dataset entries (pointing to `"training_full"`)
- `pidsmaker/config/pipeline.py` — `set_task_paths` redirects `feat_training` and `gnn_training` paths to base dataset; sets `_base_edge_embeds_dir` for feat_inference
- `pidsmaker/featurization/feat_inference_methods/feat_inference_flash.py` — after loading cached indexid2vec, delta-embeds any test-split nodes missing from cache
- `pidsmaker/featurization/feat_inference.py` — symlinks base dataset's pre-computed `.TemporalData.simple` files; only computes edges for files not already present

## 2026-03-12

### Fix: Cross-month date construction in graph building

**Files changed:**
- `pidsmaker/preprocessing/build_graph_methods/build_default_graphs.py`
- `pidsmaker/preprocessing/build_graph_methods/build_magic_graphs.py`

**Problem:**

Day-boundary timestamps were built by naively concatenating `year_month` with a day
integer extracted from the graph filename (e.g. `graph_32` → day `32`):

```python
# Before
date_start = cfg.dataset.year_month + "-" + str(day) + " 00:00:00"
date_stop  = cfg.dataset.year_month + "-" + str(day + 1) + " 00:00:00"
```

When a dataset spans a month boundary (e.g. `year_month = "2026-01"` and the graph
files include `graph_32`, `graph_33`, …), the above produces invalid date strings like
`"2026-01-32 00:00:00"`, causing `datetime_to_ns_time_US` to crash.

**Fix:**

Use `datetime` arithmetic relative to the first day of `year_month` instead of string
concatenation:

```python
# After
base = datetime.strptime(cfg.dataset.year_month + "-01", "%Y-%m-%d")
date_start = (base + timedelta(days=day - 1)).strftime("%Y-%m-%d") + " 00:00:00"
date_stop  = (base + timedelta(days=day)).strftime("%Y-%m-%d") + " 00:00:00"
```

`datetime` and `timedelta` were already imported in both files, so no new dependencies
are introduced.

**How to configure a cross-month dataset:**

Set `year_month` to the starting month and use graph numbers that are day-offsets from
the 1st of that month. For example, for data running from Jan 29 to Feb 3 2026:

```python
"year_month": "2026-01",
"start_end_day_range": (29, 34),  # 29=Jan 29, 32=Feb 1, 33=Feb 2, 34=Feb 3
"train_files": ["graph_29", "graph_30", "graph_31"],
"val_files":   ["graph_31"],
"test_files":  ["graph_32", "graph_33"],
"attack_to_time_window": [
    ["PROVATTACK/your_gt.csv", "2026-02-01 10:30:00", "2026-02-01 11:00:00"],
],
```

`attack_to_time_window` entries are full ISO timestamp strings and are unaffected by
this issue — they are passed directly to `datetime_to_ns_time_US` and have always
supported any date.

---

## 2026-03-12

### Fix: Segfault in `feat_inference` for large datasets

**Files changed:**
- `pidsmaker/featurization/feat_inference.py`

**Problem:** During "Computing edge embeddings", millions of individual torch tensors were accumulated in a Python list and then `torch.vstack` was called on all of them at once. For large datasets like `training_full` (~510K nodes), individual daily graphs can have millions of edges, exhausting memory and causing a segfault (not a Python OOM — a native crash).

**Fix:** Pre-convert onehot dicts to numpy once before the loop, accumulate lightweight numpy arrays per edge instead of torch tensors, pre-allocate `src/dst/t/y` as numpy arrays, and do a single `np.vstack` + `torch.from_numpy` at the end.

---

### Setup: Automatic change logging

**Files changed:**
- `.claude/hooks/log_changes.sh`
- `.claude/settings.json`
- `CLAUDE.md`

Added a `PostToolUse` hook that appends a timestamped line to `CHANGES.md` after every `Edit`/`Write` tool call. Also added a `CLAUDE.md` instruction for task-level summaries.
- [2026-03-12 17:53:18] `Write` → `/home/ziyu/.claude/plans/eager-spinning-anchor.md`
- [2026-03-12 17:56:55] `Edit` → `/home/ziyu/PIDSMaker-1/pidsmaker/config/config.py`
- [2026-03-12 17:57:03] `Edit` → `/home/ziyu/PIDSMaker-1/pidsmaker/config/config.py`
- [2026-03-12 17:57:14] `Edit` → `/home/ziyu/PIDSMaker-1/pidsmaker/config/config.py`
- [2026-03-12 17:57:21] `Edit` → `/home/ziyu/PIDSMaker-1/pidsmaker/config/config.py`
- [2026-03-12 17:57:27] `Edit` → `/home/ziyu/PIDSMaker-1/pidsmaker/config/config.py`
- [2026-03-12 17:57:37] `Edit` → `/home/ziyu/PIDSMaker-1/pidsmaker/config/pipeline.py`
- [2026-03-12 17:57:44] `Edit` → `/home/ziyu/PIDSMaker-1/pidsmaker/config/pipeline.py`
- [2026-03-12 17:57:58] `Edit` → `/home/ziyu/PIDSMaker-1/pidsmaker/featurization/feat_inference_methods/feat_inference_flash.py`
- [2026-03-12 17:58:12] `Edit` → `/home/ziyu/PIDSMaker-1/pidsmaker/featurization/feat_inference.py`
- [2026-03-12 17:58:57] `Edit` → `/home/ziyu/PIDSMaker-1/CHANGES.md`
- [2026-03-12 18:01:00] `Write` → `/home/ziyu/PIDSMaker-1/README for TRAINING_FULL FLOW.md`
- [2026-03-12 18:28:07] `Edit` → `/home/ziyu/PIDSMaker-1/pidsmaker/config/pipeline.py`
- [2026-03-12 18:29:27] `Edit` → `/home/ziyu/PIDSMaker-1/CHANGES.md`
- [2026-03-12 18:41:46] `Edit` → `/home/ziyu/PIDSMaker-1/README for TRAINING_FULL FLOW.md`
- [2026-03-12 18:41:57] `Edit` → `/home/ziyu/PIDSMaker-1/README for TRAINING_FULL FLOW.md`
- [2026-03-12 18:42:05] `Edit` → `/home/ziyu/PIDSMaker-1/README for TRAINING_FULL FLOW.md`
- [2026-03-12 18:42:14] `Edit` → `/home/ziyu/PIDSMaker-1/README for TRAINING_FULL FLOW.md`
- [2026-03-12 18:42:25] `Edit` → `/home/ziyu/PIDSMaker-1/README for TRAINING_FULL FLOW.md`
