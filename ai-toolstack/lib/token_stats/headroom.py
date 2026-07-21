"""Query Headroom session_stats.jsonl for MCP compression savings."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


def _headroom_stats_path() -> Path:
    workspace = os.environ.get("HEADROOM_WORKSPACE_DIR", "").strip()
    if workspace:
        return Path(workspace).expanduser() / "session_stats.jsonl"
    return Path.home() / ".headroom" / "session_stats.jsonl"


def query_headroom(
    start: datetime,
    end: datetime,
) -> dict[str, Any]:
    stats_path = _headroom_stats_path()
    if not stats_path.is_file():
        return {
            "available": False,
            "compressions": 0,
            "retrievals": 0,
            "tokens_in": 0,
            "tokens_out": 0,
            "tokens_saved": 0,
            "savings_pct": 0.0,
        }

    start_ts = start.timestamp()
    end_ts = end.timestamp()
    compressions = 0
    retrievals = 0
    tokens_in = 0
    tokens_out = 0

    with stats_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                evt = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = float(evt.get("timestamp") or 0)
            if ts < start_ts or ts > end_ts:
                continue
            kind = str(evt.get("type") or "")
            if kind == "compress":
                compressions += 1
                tokens_in += int(evt.get("input_tokens") or 0)
                tokens_out += int(evt.get("output_tokens") or 0)
            elif kind == "retrieve":
                retrievals += 1

    saved = max(0, tokens_in - tokens_out)
    pct = (100.0 * saved / tokens_in) if tokens_in else 0.0
    return {
        "available": True,
        "compressions": compressions,
        "retrievals": retrievals,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "tokens_saved": saved,
        "savings_pct": round(pct, 1),
        "stats_path": str(stats_path),
    }
