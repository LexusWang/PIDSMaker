# Changelog

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
