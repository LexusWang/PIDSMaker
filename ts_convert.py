#!/usr/bin/env python3
"""Convert nanosecond timestamps to Chicago time (CST/CDT)."""

import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

CHICAGO = ZoneInfo("America/Chicago")


def convert(ts_ns: int) -> str:
    dt = datetime.fromtimestamp(ts_ns / 1e9, tz=timezone.utc).astimezone(CHICAGO)
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f %Z")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ts_convert.py <timestamp_ns> [timestamp_ns ...]")
        sys.exit(1)

    for arg in sys.argv[1:]:
        ts = int(arg)
        print(f"{ts} -> {convert(ts)}")
