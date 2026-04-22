# parser_pidsmaker

Translate eAudit human-readable logs (`./eaudit -P file.txt`) into the
PIDSMaker PostgreSQL schema (4 tables).

```
 Data collector
 ┌─────────────────┐  ┌──────────────────┐
 │   events.txt    │  │ ground_truth.json │
 │  (eaudit log)   │  │ (attack window +  │
 │                 │  │  malicious nodes) │
 └────────┬────────┘  └────────┬─────────┘
          │                    │
          ▼                    │
 parse_eaudit.py               │
 ┌─────────────────────────┐   │
 │ netflow_node_table.csv  │   │
 │ subject_node_table.csv  │   │
 │ file_node_table.csv     │   │
 │ event_table.csv         │   │
 │ load.sql                │   │
 └────────────┬────────────┘   │
              │                │
              ▼                │
 split_days.py  (if single-session capture, to split train/test)
 ┌─────────────────────────┐   │
 │ event_table.csv (shifted│   │
 │ load.sql (updated paths)│   │
 │ split_report.md         │   │
 └────────────┬────────────┘   │
              │                │
              ▼                │
 verify_data.py                │
              │                │
              ▼                │
 create_dump.sh                │
 ┌─────────────────────────┐   │
 │ <db_name>.dump          │   │
 │ (PostgreSQL loaded)     │   │
 └────────────┬────────────┘   │
              │                │
              ▼                ▼
           make_ground_truth.py  (TODO)
           ┌──────────────────────────────┐
           │ Ground_Truth/orthrus/        │
           │   <DATASET>/node_<name>.csv  │
           └──────────────┬───────────────┘
                          │
                          ▼
           config.py  (register dataset)
                          │
                          ▼
           python pidsmaker/main.py <model> <DATASET>
```

## Files
- `schema.sql`       — the 4 tables (netflow / subject / file / event) + indexes.
- `parse_eaudit.py`  — parser. Reads eaudit text, writes 4 CSVs + `load.sql`.
- `out/`             — generated CSVs + a self-contained `load.sql`.

## Run

```bash
# single file
python3 parse_eaudit.py /tmp/eaudit.human.txt -o ./out

# directory of files (sorted, then merged in (ts, seq) order)
python3 parse_eaudit.py sample_data/ -o ./out
```

Output (in `./out/`):
```
schema.sql
netflow_node_table.csv
subject_node_table.csv
file_node_table.csv
event_table.csv
ground_truth.csv        # PLACEHOLDER — random sample, no real attacks
metadata.md             # time range, ops, attack window (placeholder), days
load.sql                # \i schema.sql + 4 \copy statements
```

Sampling knobs:
```
--gt-samples N    # how many placeholder GT rows to emit (default 15)
--seed S          # RNG seed for deterministic sampling (default 42)
```

## Split train/test across a day boundary (optional)

If your capture is a single continuous session and you want to split it into a training portion and a test portion, use `split_days.py`. It shifts **all** timestamps in `event_table.csv` by a single fixed offset so the chosen split point lands exactly at a US/Eastern midnight — the day boundary that PIDSMaker uses internally.

```bash
python parser_eaudit/split_days.py <data_dir> <test_start_time_utc> [--ground-truth <path>]

# Example: test set begins at 2026-04-20 13:47:00 UTC
python parser_eaudit/split_days.py data/test_eaudit/pidsmaker "2026-04-20T13:47:00+00:00" \
    --ground-truth data/test_eaudit/ground_truth.json
```

The script:
1. Computes `offset = next_midnight_US/Eastern_after_test_start − test_start`
2. Adds that offset to every `timestamp_rec` in `event_table.csv` (in-place)
3. Rewrites `load.sql` with current absolute paths
4. Writes `split_report.md` in `data_dir` — contains the offset used, original and shifted time ranges, and a ready-to-paste dataset config snippet

Pass `--ground-truth` to also shift the attack window from `ground_truth.json` by the same offset. The shifted window (in US/Eastern) is then included in `split_report.md` as the ready-to-use `attack_to_time_window` value.

After running, configure the dataset with:
```python
"train_files": ["graph_N"],   # day N  — everything before the split
"val_files":   ["graph_N"],
"test_files":  ["graph_M"],   # day M = N+1 — everything from the split onward
```
(The exact day numbers, `year_month`, and `attack_to_time_window` are printed in `split_report.md`.)

## Verify the generated data
Checks index_id uniqueness/non-overlap, hash_id format, referential integrity (all src/dst in events exist in node tables), index_id consistency, ground truth validity
```bash
python data/verify_data.py ./out
```

## Load into Postgres
The generated `.sql` file can be used to create the Postgres database. You can use these commands in the Postgres environment.
```bash
createdb pidsmaker_eaudit
psql -d pidsmaker_eaudit -f ./out/load.sql
```

Otherwise, you can use this script `data/create_dump.sh`. It copies CSVs into the postgres container, creates the database, loads schema + data, verifies counts, exports dump to `data/<db_name>.dump`. **Note: if a database with the same name already exists, it will be dropped and recreated from scratch.**
```bash
bash data/create_dump.sh ./out test_eaudit
```

## Create and place the ground truth file
Place the ground truth CSV under:
```
Ground_Truth/orthrus/<DATASET_NAME>/node_<capture_name>.csv
```

The file has no header. Each row is one malicious node:
```
node_uuid,label_dict_string,index_id
072DFCB5-87F4-46FB-BAC0-2078316DC093,{'file': '/etc/pam.d/common-session'},539
91AC7CB9-E3BB-496E-A005-A1F352FA7B90,{'netflow': '->10.0.2.3:53'},1
```

- `node_uuid` — must match a `node_uuid` in one of the three node tables
- `label_dict_string` — human-readable label for display (e.g. `{'subject': 'None bash'}`, `{'file': '/etc/passwd'}`, `{'netflow': '->1.2.3.4:80'}`)
- `index_id` — the node's integer `index_id` from the node tables

## Dataset Registration

After creating the dump and the ground truth file, register the dataset by adding an entry to `DATASET_DEFAULT_CONFIG` in `pidsmaker/config/config.py`:

```python
"MY_DATASET": {
    "raw_dir": "",                  # legacy unused field, always ""
    "database": "my_db_name",       # PostgreSQL database name (must match create_dump.sh argument)
    "database_all_file": "my_db_name",  # same as database; only differs if construction.use_all_files=True (unused in practice)
    "num_node_types": 3,            # always 3 — hardcoded by the 3-table schema (netflow/subject/file)
    "num_edge_types": 10,           # must match the number of entries in your rel2id dict (see below)
    "year_month": "2026-04",        # YYYY-MM of the capture (used to build day boundaries)
    "start_end_day_range": (20, 21),# only used by the MAGIC model; ignored by all other models (nodlink, orthrus, etc.)
    "train_files": ["graph_20"],    # list of graph_N folder names whose time-windows are used for training
    "val_files":   ["graph_20"],    # same — all time-window files inside the folder go to this split
    "test_files":  ["graph_21"],    # same
    "unused_files": [],             # days present in the database but excluded from all splits
    "ground_truth_relative_path": [
        "MY_DATASET/node_capture_name.csv",   # relative to Ground_Truth/orthrus/
    ],
    "attack_to_time_window": [
        # [gt_csv_path, attack_start (US/Eastern), attack_end (US/Eastern)]
        ["MY_DATASET/node_capture_name.csv", "2026-04-20 13:27:00", "2026-04-20 13:47:00"],
    ],
},
```

Key points:

- **`year_month` + day number** defines the time window queried from the database. Day `N` covers `YYYY-MM-N 00:00:00` to `YYYY-MM-(N+1) 00:00:00` in **US/Eastern** time. Make sure your `timestamp_rec` values fall within these boundaries.

- **`start_end_day_range`** is only used by the MAGIC model (`build_magic_graphs.py`). All other models (nodlink, orthrus, threatrace, etc.) derive which days to process directly from the union of `train_files + val_files + test_files` and ignore this field entirely. Set it to cover the same day range as your files to keep things consistent, but it has no effect on non-MAGIC pipelines.

- **Multi-month data is not supported.** The construction code builds time windows by literally appending the day number to `year_month` (e.g. `"2026-04" + "-" + "20"`), so all days must belong to the same calendar month. Data that spans month boundaries (e.g. Jan 28 – Feb 5) cannot be handled in a single dataset registration. The only workaround is to split the data at the month boundary and register two separate datasets (one per month).
- **`attack_to_time_window` times must be in US/Eastern**, not UTC. Convert with:
  ```python
  from datetime import datetime
  import pytz
  utc_time = datetime.fromisoformat("2026-04-20T17:27:20+00:00")
  eastern = utc_time.astimezone(pytz.timezone("US/Eastern"))
  print(eastern.strftime("%Y-%m-%d %H:%M:%S"))  # → "2026-04-20 13:27:20"
  ```
- **`num_node_types`** is always `3` — it corresponds to the three fixed node types (netflow, subject, file) that the schema is built around. It feeds the node-type one-hot dimension in the GNN feature vector and should never be changed.

- **`num_edge_types`** must equal the number of operation types in the `rel2id` dict that will be used for your dataset. For eAudit data, all 8 operations are a subset of `rel2id_darpa_tc` (10 entries), so use `10`. If your data has different or additional operation types, you must:
  1. Edit `pidsmaker/utils/dataset_utils.py` — add or modify the `rel2id_*` dict for your operation names, where each entry maps `"OP_NAME": integer_id` (and `integer_id: "OP_NAME"`) starting from 1.
  2. If you created a new `rel2id_*` dict, add your dataset name to the appropriate set and extend the `get_rel2id()` function to return it.
  3. Set `num_edge_types` to the number of entries (integer keys only) in that dict.

  The relevant section in `pidsmaker/utils/dataset_utils.py`:
  ```python
  rel2id_darpa_tc = {          # used by default for all DARPA TC + eAudit datasets
      1: "EVENT_CONNECT", "EVENT_CONNECT": 1,
      2: "EVENT_EXECUTE", "EVENT_EXECUTE": 2,
      3: "EVENT_OPEN",    "EVENT_OPEN":    3,
      4: "EVENT_READ",    "EVENT_READ":    4,
      5: "EVENT_RECVFROM","EVENT_RECVFROM":5,
      6: "EVENT_RECVMSG", "EVENT_RECVMSG": 6,
      7: "EVENT_SENDMSG", "EVENT_SENDMSG": 7,
      8: "EVENT_SENDTO",  "EVENT_SENDTO":  8,
      9: "EVENT_WRITE",   "EVENT_WRITE":   9,
      10:"EVENT_CLONE",   "EVENT_CLONE":  10,
  }
  # Dataset name sets that control which rel2id is used:
  OPTC_DATASETS      = {"optc_h201", "optc_h501", "optc_h051"}
  ATLASv2_DATASETS   = {"atlasv2_h1"}
  PROVATTACK_DATASETS = {"PROVATTACK25", ...}
  # All other datasets fall through to rel2id_darpa_tc
  ```
  Events with operation names NOT present in the chosen `rel2id` dict are **silently dropped** during graph construction.

- **`train_files` / `val_files` / `test_files`** are lists of `graph_N` names corresponding to day numbers. The construction stage queries all events for each day that appears in `train_files + val_files + test_files`, then slices them into sub-day snapshots using `construction.time_window_size` (minutes, default 15). Each snapshot is saved as a file inside a `graph_N/` folder named by its time interval:
  ```                                                                                                                       
  artifacts/.../graphs/                                                                                                     
    graph_20/                                                                                                             
      "2026-04-20 13:07:00~2026-04-20 13:22:00"                                                                         
      "2026-04-20 13:22:00~2026-04-20 13:37:00"                                                                         
      ...                                                                                                               
  ```
`train_files = ["graph_20"]` means: collect **all** time-window files inside `graph_20/` and use them for training. The split granularity is at the **day (folder)** level — every window within a day goes to the same split.

- **Sub-day splitting (e.g. first 40 min benign, last 20 min attack)** is not natively supported. The workaround is to shift **all** timestamps in the dataset by a single fixed offset so the desired split point lands exactly on a day boundary. Since `val_files` only monitors loss during training and does not need to be a separate time segment, a two-way split is sufficient:
  ```
  Original:  |---- train (40 min) ----|---- test (20 min) ----|
             13:07                   13:47                   14:07

  Shift all timestamps by +(24:00 - 13:47) = +10h13min:

  After:     |---- train ----|---- test ----|
             23:20          00:00           00:20
              (day 20)       ↑ day boundary  (day 21)
  ```
  The key is to shift the **entire dataset** by the same amount — not just the test portion — so no overlap or gap is introduced. This should be done as a post-processing step on the CSVs (before `create_dump.sh`), using a script that:
  1. Takes the desired split time and target day boundary as input
  2. Computes `offset = day_boundary_ns - split_time_ns`
  3. Adds `offset` to every `timestamp_rec` in `event_table.csv` (the only table that contains timestamps — the three node tables have no time columns)
  4. Updates `load.sql` with the new output file paths
  5. Updates `metadata.md` (time range, `attack_to_time_window`, day classification)
  6. Copies `schema.sql` and `ground_truth.csv` unchanged — neither contains timestamps

  Then configure: `train_files = ["graph_20"]`, `val_files = ["graph_20"]`, `test_files = ["graph_21"]`.

## Run the pipeline

```bash
python pidsmaker/main.py nodlink MY_DATASET [params]
```

## Mapping

| eaudit syscall            | PIDSMaker operation         | edge direction              |
|---------------------------|-----------------------------|-----------------------------|
| `execve`                  | `EVENT_EXECUTE`             | file → subject              |
| `clone` / `fork` / `vfork`| `EVENT_EXECUTE`             | parent subj → child subj    |
| `open` / `openat` / `creat`| `EVENT_OPEN`               | subj → file                 |
| `read` / `pread` / `readv`| `EVENT_READ`                | file → subj                 |
| `write` / `pwrite`/`writev`| `EVENT_WRITE`              | subj → file                 |
| `close`                   | `EVENT_CLOSE`               | subj → resource             |
| `connect` / `bind`        | `EVENT_CONNECT`             | subj → netflow              |
| `accept`                  | `EVENT_CONNECT`             | netflow → subj              |
| `sendto`                  | `EVENT_SENDTO`              | subj → netflow              |
| `sendmsg`                 | `EVENT_SENDMSG`             | subj → netflow              |
| `recvfrom`                | `EVENT_RECVFROM`            | netflow → subj              |
| `recvmsg`                 | `EVENT_RECVMSG`             | netflow → subj              |
| (read/write on socket fd) | promoted to `RECVFROM`/`SENDTO` | auto                    |
| anything else             | dropped                     | —                           |

If you add operations, also extend `OP_MAP` in `parse_eaudit.py` AND add the
operation name to `rel2id` in `pidsmaker/utils/dataset_utils.py` (else the
graph builder silently drops the edges).

## Field-rule compliance

- **`index_id`** — globally unique across all 3 node tables. Ranges:
  netflow `[0, N)`, subject `[N, N+M)`, file `[N+M, N+M+F)` — matches the
  PIDSMaker convention.
- **`hash_id`** — 64-char SHA-256 hex. Hashed from
  `f"{node_uuid}_{path}_{cmd}"` (subject), `f"{node_uuid}_{path}"` (file),
  `f"{node_uuid}_{src_addr}_{src_port}_{dst_addr}_{dst_port}"` (netflow).
- **`node_uuid`** — `uuid.uuid4()` per node (eaudit doesn't provide one).
- **`event_table.src_node`/`dst_node`** — `hash_id` (not uuid) of endpoints.
- **`event_table.src_index_id`/`dst_index_id`** — index_id as varchar.
- **`timestamp_rec`** — nanoseconds (`int(ts_seconds * 1e9)`). eaudit timestamps
  are float seconds with millisecond resolution, so the trailing 6 digits are
  always zero — fine for time-window bucketing.
- **`event_uuid`** — fresh `uuid.uuid4()` per emitted edge.

## Caveats specific to eAudit input

- **Pre-existing processes** (pids that existed before `ecapd` started) get a
  stub subject node with `path=''`, `cmd=f'pid:{p}'`. They will not have an
  `EVENT_EXECUTE` predecessor.
- **Pre-existing fds** (read/write on an fd that was opened before capture
  began) are dropped — we have no resource to attach them to.
- **Sequence-number wrap**: capture was taken with default 16-bit seq numbers;
  for long captures consider running ecapd with `-S` and updating the parser
  to ignore the seq column.
- **`ecapd`'s own pid** appears in the log (its own perf-buffer cleanup); you
  may want to filter it out before loading.
