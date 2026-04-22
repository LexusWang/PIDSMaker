"""Shift all event timestamps so a chosen split time lands at the start of a new
US/Eastern day, enabling train/test splits within a single day's capture.

The entire dataset is shifted by the same offset — no gap or overlap is created.
After shifting, events before the split time fall in day N and events from the
split time onward fall in day N+1.

Usage:
    python parser_eaudit/split_days.py <data_dir> <test_start_time_utc> [--ground-truth <path>]

    data_dir            — folder output of parse_eaudit.py, containing the 4 CSVs and load.sql
    test_start_time_utc — UTC time where the test set begins (ISO 8601 format)
    --ground-truth      — path to ground_truth.json; if provided, the shifted attack window
                          is included in split_report.md

Example:
    python parser_eaudit/split_days.py data/test_eaudit/pidsmaker "2026-04-20T13:47:00+00:00" \\
        --ground-truth data/test_eaudit/ground_truth.json

Output:
    - event_table.csv updated in-place (timestamps shifted)
    - load.sql rewritten with current absolute paths
    - split_report.md written to data_dir
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timedelta, timezone

import pytz


def parse_utc(s):
    s = s.strip()
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
        return dt.replace(tzinfo=timezone.utc)


def next_midnight_et(dt_utc):
    """Return the first midnight US/Eastern strictly after dt_utc."""
    et = pytz.timezone("US/Eastern")
    dt_et = dt_utc.astimezone(et)
    midnight_et = (dt_et + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return midnight_et.astimezone(timezone.utc)


def fmt(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")


def fmt_et(dt_utc):
    et = pytz.timezone("US/Eastern")
    return dt_utc.astimezone(et).strftime("%Y-%m-%d %H:%M:%S")


def shift_ns(dt_utc, offset_ns):
    ns = int(dt_utc.timestamp() * 1_000_000_000) + offset_ns
    return datetime.fromtimestamp(ns / 1_000_000_000, tz=timezone.utc)


def main():
    parser = argparse.ArgumentParser(
        description="Shift event timestamps so a split time lands at a US/Eastern day boundary."
    )
    parser.add_argument("data_dir", help="Output folder of parse_eaudit.py")
    parser.add_argument("test_start_time_utc", help="UTC time where the test set begins (ISO 8601)")
    parser.add_argument("--ground-truth", metavar="PATH",
                        help="Path to ground_truth.json; attack window will be shifted and reported")
    args = parser.parse_args()

    data_dir = args.data_dir
    test_start_str = args.test_start_time_utc

    if not os.path.isdir(data_dir):
        print(f"Error: {data_dir} is not a directory")
        sys.exit(1)

    event_csv = os.path.join(data_dir, "event_table.csv")
    load_sql_path = os.path.join(data_dir, "load.sql")
    for f in [event_csv, load_sql_path]:
        if not os.path.exists(f):
            print(f"Error: missing required file: {f}")
            sys.exit(1)

    # --- Compute offset ---
    test_start_utc = parse_utc(test_start_str)
    test_start_ns = int(test_start_utc.timestamp() * 1_000_000_000)

    boundary_utc = next_midnight_et(test_start_utc)
    boundary_ns = int(boundary_utc.timestamp() * 1_000_000_000)
    offset_ns = boundary_ns - test_start_ns

    assert offset_ns > 0, (
        f"Offset must be positive, got {offset_ns}. "
        "This can happen if test_start_time is exactly at midnight ET."
    )

    offset_total_s = offset_ns / 1_000_000_000
    offset_h = int(offset_total_s // 3600)
    offset_m = int((offset_total_s % 3600) // 60)
    offset_s = offset_total_s % 60

    print(f"Test start (UTC):      {fmt(test_start_utc)}")
    print(f"Next midnight ET (UTC):{fmt(boundary_utc)}")
    print(f"Offset:                +{offset_h}h {offset_m}m {offset_s:.3f}s  ({offset_ns} ns)")

    # --- Read event_table.csv ---
    with open(event_csv, newline="") as f:
        rows = list(csv.reader(f))

    ts_values = []
    for row in rows:
        try:
            ts_values.append(int(row[6]))
        except (ValueError, IndexError):
            pass

    if not ts_values:
        print("Error: no valid timestamp_rec values found in event_table.csv")
        sys.exit(1)

    orig_min_ns = min(ts_values)
    orig_max_ns = max(ts_values)
    orig_start = datetime.fromtimestamp(orig_min_ns / 1_000_000_000, tz=timezone.utc)
    orig_end   = datetime.fromtimestamp(orig_max_ns / 1_000_000_000, tz=timezone.utc)

    new_start = shift_ns(orig_start, offset_ns)
    new_end   = shift_ns(orig_end,   offset_ns)

    # Derive ET day numbers for train and test
    et = pytz.timezone("US/Eastern")
    train_et = new_start.astimezone(et)
    test_et  = boundary_utc.astimezone(et)
    train_day = train_et.day
    test_day  = test_et.day
    year_month = train_et.strftime("%Y-%m")

    print(f"\nOriginal range:    {fmt(orig_start)}  →  {fmt(orig_end)}")
    print(f"New range:         {fmt(new_start)}  →  {fmt(new_end)}")
    print(f"Train/val (day {train_day}): {fmt(new_start)}  →  {fmt(boundary_utc)}")
    print(f"Test      (day {test_day}): {fmt(boundary_utc)}  →  {fmt(new_end)}")

    # --- Load and shift attack window from ground_truth.json (optional) ---
    attack_window_et = None
    gt_csv_placeholder = None
    if args.ground_truth:
        if not os.path.exists(args.ground_truth):
            print(f"Error: ground truth file not found: {args.ground_truth}")
            sys.exit(1)
        with open(args.ground_truth) as f:
            gt = json.load(f)
        aw = gt["attack_window"]
        atk_start_utc = shift_ns(parse_utc(aw["start"]), offset_ns)
        atk_end_utc   = shift_ns(parse_utc(aw["end"]),   offset_ns)
        attack_window_et = (fmt_et(atk_start_utc), fmt_et(atk_end_utc))
        print(f"\nAttack window (shifted, ET): {attack_window_et[0]}  →  {attack_window_et[1]}")

    # --- Write shifted event_table.csv ---
    shifted_rows = []
    for row in rows:
        try:
            row[6] = str(int(row[6]) + offset_ns)
        except (ValueError, IndexError):
            pass
        shifted_rows.append(row)

    with open(event_csv, "w", newline="") as f:
        csv.writer(f).writerows(shifted_rows)
    print(f"\nUpdated: {event_csv}")

    # --- Rewrite load.sql with current absolute paths ---
    abs_dir = os.path.abspath(data_dir)
    load_sql_content = (
        f"\\i {abs_dir}/schema.sql\n"
        f"\\copy netflow_node_table(node_uuid,hash_id,src_addr,src_port,dst_addr,dst_port,index_id) "
        f"FROM '{abs_dir}/netflow_node_table.csv' WITH (FORMAT csv);\n"
        f"\\copy subject_node_table(node_uuid,hash_id,path,cmd,index_id) "
        f"FROM '{abs_dir}/subject_node_table.csv' WITH (FORMAT csv);\n"
        f"\\copy file_node_table(node_uuid,hash_id,path,index_id) "
        f"FROM '{abs_dir}/file_node_table.csv' WITH (FORMAT csv);\n"
        f"\\copy event_table(src_node,src_index_id,operation,dst_node,dst_index_id,event_uuid,timestamp_rec) "
        f"FROM '{abs_dir}/event_table.csv' WITH (FORMAT csv);\n"
    )
    with open(load_sql_path, "w") as f:
        f.write(load_sql_content)
    print(f"Updated: {load_sql_path}")

    # --- Write split_report.md ---
    report_path = os.path.join(data_dir, "split_report.md")
    with open(report_path, "w") as f:
        f.write("# split_days.py report\n\n")
        f.write(f"**Input test start time (UTC):** `{fmt(test_start_utc)}`\n\n")
        f.write(f"**Offset applied:** `+{offset_h}h {offset_m}m {offset_s:.3f}s` (`{offset_ns}` ns)\n\n")
        f.write("## Time ranges\n\n")
        f.write("| Split | Start (UTC) | End (UTC) | ET day |\n")
        f.write("|---|---|---|---|\n")
        f.write(f"| Original (full dataset) | `{fmt(orig_start)}` | `{fmt(orig_end)}` | — |\n")
        f.write(f"| After shift (full dataset) | `{fmt(new_start)}` | `{fmt(new_end)}` | — |\n")
        f.write(
            f"| Train / val | `{fmt(new_start)}` | `{fmt(boundary_utc)}` | "
            f"`{train_et.strftime('%Y-%m-%d')}` (day {train_day}) |\n"
        )
        f.write(
            f"| Test | `{fmt(boundary_utc)}` | `{fmt(new_end)}` | "
            f"`{test_et.strftime('%Y-%m-%d')}` (day {test_day}) |\n"
        )
        if attack_window_et:
            f.write(f"\n**Attack window (shifted, US/Eastern):** `{attack_window_et[0]}` → `{attack_window_et[1]}`\n")
        f.write("\n## Dataset registration\n\n")
        f.write("Use these values when registering the dataset in `pidsmaker/config/config.py`:\n\n")
        f.write("```python\n")
        f.write(f'"year_month": "{year_month}",\n')
        f.write(f'"start_end_day_range": ({train_day}, {test_day}),\n')
        f.write(f'"train_files": ["graph_{train_day}"],\n')
        f.write(f'"val_files":   ["graph_{train_day}"],\n')
        f.write(f'"test_files":  ["graph_{test_day}"],\n')
        if attack_window_et:
            f.write(f'"attack_to_time_window": [\n')
            f.write(f'    ["<GT_CSV_PATH>", "{attack_window_et[0]}", "{attack_window_et[1]}"],\n')
            f.write(f'],\n')
        f.write("```\n")
        if not attack_window_et:
            f.write(
                f"\nRemember to convert `attack_to_time_window` timestamps to US/Eastern: "
                f"the test set starts at `{test_et.strftime('%Y-%m-%d %H:%M:%S')} ET`.\n"
            )

    print(f"Written:  {report_path}")


if __name__ == "__main__":
    main()
