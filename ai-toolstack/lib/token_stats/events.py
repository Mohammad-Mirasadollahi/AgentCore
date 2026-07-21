"""Load JSONL token events."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _parse_ts(raw: str) -> datetime:
    dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def load_events(
    path: Path,
    start: datetime,
    end: datetime,
) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts_raw = row.get("ts")
            if not ts_raw:
                continue
            try:
                ts = _parse_ts(str(ts_raw))
            except ValueError:
                continue
            if start <= ts <= end:
                rows.append(row)
    return rows
