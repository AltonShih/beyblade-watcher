#!/usr/bin/env python3
"""Prune watcher history without loading the entire file into memory."""

import json
import os
from datetime import datetime, timedelta, timezone


HISTORY_FILE = os.environ.get("HISTORY_FILE", "history.jsonl")
RETENTION_DAYS = int(os.environ.get("HISTORY_RETENTION_DAYS", "180"))


def parse_timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def main():
    if not os.path.exists(HISTORY_FILE):
        return

    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    temp_file = f"{HISTORY_FILE}.tmp"
    kept = removed = 0

    with open(HISTORY_FILE, "r", encoding="utf-8") as source, open(
        temp_file, "w", encoding="utf-8"
    ) as target:
        for line in source:
            try:
                timestamp = parse_timestamp(json.loads(line).get("ts"))
            except json.JSONDecodeError:
                timestamp = None

            # Retain malformed rows so cleanup never discards recoverable data.
            if timestamp is None or timestamp >= cutoff:
                target.write(line)
                kept += 1
            else:
                removed += 1

    if removed:
        os.replace(temp_file, HISTORY_FILE)
    else:
        os.remove(temp_file)

    print(
        f"歷史清理完成：保留 {kept} 筆、刪除 {removed} 筆（保留最近 {RETENTION_DAYS} 天）。"
    )


if __name__ == "__main__":
    main()
