#!/usr/bin/env python3
import argparse
import csv
import re
from typing import Any, Optional

import torch


UUID_RE = re.compile(
    r'(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b'
)


def load_torch_file(path: str):
    """
    Load a .pth/.pkl file produced by PIDSMaker preprocessing/evaluation.
    Compatible with torch>=2.6 where weights_only=True is the default.
    """
    try:
        return torch.load(path, map_location="cpu", weights_only=False)
    except TypeError:
        return torch.load(path, map_location="cpu")


def find_uuid_in_text(text: str) -> Optional[str]:
    if not isinstance(text, str):
        return None
    m = UUID_RE.search(text)
    return m.group(0) if m else None


def extract_uuid(entry: Any) -> Optional[str]:
    """
    Robust UUID extraction for node_to_paths.pkl entries.

    Handles cases like:
      - {'node_uuid': '...'}
      - {'uuid': '...'}
      - {'path': '21590 | <uuid> | ...'}
      - nested lists / tuples / dict values that contain a UUID string
    """
    if entry is None:
        return None

    if isinstance(entry, str):
        return find_uuid_in_text(entry)

    if isinstance(entry, dict):
        # Prefer explicit UUID-like fields first.
        for key in ("node_uuid", "uuid", "id"):
            value = entry.get(key)
            found = find_uuid_in_text(value) if isinstance(value, str) else None
            if found:
                return found

        # Then inspect the common text-bearing fields from this dataset.
        for key in ("path", "msg", "cmd", "name"):
            value = entry.get(key)
            found = find_uuid_in_text(value) if isinstance(value, str) else None
            if found:
                return found

        # Finally, inspect all values as a fallback.
        for value in entry.values():
            found = extract_uuid(value)
            if found:
                return found
        return None

    if isinstance(entry, (list, tuple)):
        for value in entry:
            found = extract_uuid(value)
            if found:
                return found
        return None

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Merge PIDSMaker node predictions with UUIDs from node_to_paths.pkl."
    )
    parser.add_argument(
        "--result_pth",
        required=True,
        help="Path to result_model_epoch_XX.pth",
    )
    parser.add_argument(
        "--node_to_paths_pkl",
        required=True,
        help="Path to node_id_to_path/node_to_paths.pkl",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output CSV path",
    )
    args = parser.parse_args()

    results = load_torch_file(args.result_pth)
    node_to_paths = load_torch_file(args.node_to_paths_pkl)

    if not isinstance(results, dict):
        raise TypeError(
            f"Unexpected type for result_pth: {type(results)}. Expected dict-like object."
        )
    if not isinstance(node_to_paths, dict):
        raise TypeError(
            f"Unexpected type for node_to_paths_pkl: {type(node_to_paths)}. "
            f"Did you pass the wrong file? Expected dict-like object keyed by node_index."
        )

    rows = []
    missing_uuid = []

    for node_index in sorted(results.keys()):
        result = results[node_index]
        mapping_entry = node_to_paths.get(node_index)
        uuid_value = extract_uuid(mapping_entry)

        if uuid_value is None:
            missing_uuid.append(node_index)

        y_true = result.get("y_true")
        y_hat = result.get("y_hat")

        rows.append(
            {
                "node_index": node_index,
                "uuid": uuid_value if uuid_value is not None else "",
                "y_true": y_true,
                "y_hat": y_hat,
            }
        )

    with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f, fieldnames=["node_index", "uuid", "y_true", "y_hat"]
        )
        writer.writeheader()
        writer.writerows(rows)

    tp = sum(1 for r in rows if r["y_true"] == 1 and r["y_hat"] == 1)
    fp = sum(1 for r in rows if r["y_true"] == 0 and r["y_hat"] == 1)
    tn = sum(1 for r in rows if r["y_true"] == 0 and r["y_hat"] == 0)
    fn = sum(1 for r in rows if r["y_true"] == 1 and r["y_hat"] == 0)

    print(f"Output CSV: {args.out}")
    print(f"Rows: {len(rows)}")
    print(f"Missing UUID: {len(missing_uuid)}")
    if missing_uuid:
        print(f"First missing node_index examples: {missing_uuid[:10]}")
    print(f"TP={tp}, FP={fp}, TN={tn}, FN={fn}")


if __name__ == "__main__":
    main()
