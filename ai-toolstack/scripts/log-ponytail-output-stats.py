#!/usr/bin/env python3
"""Append ponytail output-brevity estimate to token-stats events.jsonl (local only)."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def _stats_events_path() -> Path:
    raw = os.environ.get("AI_TOOLSTACK_TOKEN_STATS_DIR", "").strip()
    if raw:
        return Path(raw).expanduser() / "events.jsonl"
    repo = os.environ.get("REPO_ROOT", "").strip()
    if repo:
        return Path(repo) / "ai-toolstack" / "data" / "token-stats" / "events.jsonl"
    return Path("ai-toolstack/data/token-stats/events.jsonl")


def _extract_text(payload: dict) -> str:
    for key in (
        "text",
        "response",
        "message",
        "assistant_message",
        "content",
        "final_message",
    ):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
        if isinstance(val, dict):
            nested = val.get("text") or val.get("content")
            if isinstance(nested, str) and nested.strip():
                return nested.strip()
    return ""


def main() -> int:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return 0
        evt = json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return 0

    text = _extract_text(evt if isinstance(evt, dict) else {})
    if len(text) < 20:
        return 0

    try:
        ratio = float(os.environ.get("PONYTAIL_STATS_SAVE_RATIO", "0.35"))
    except ValueError:
        ratio = 0.35
    if ratio <= 0 or ratio >= 1:
        ratio = 0.35

    chars = len(text.encode("utf-8"))
    tokens_out = max(1, round(chars / 4))
    tokens_saved = max(0, round(tokens_out * ratio / (1.0 - ratio)))
    tokens_in = tokens_out + tokens_saved

    path = _stats_events_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "component": "ponytail",
        "event": "agent_response",
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "tokens_saved": tokens_saved,
        "meta": {
            "chars": chars,
            "save_ratio_est": ratio,
            "note": "heuristic output brevity vs verbose prose (ponytail-fa / ponytail lite)",
        },
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
