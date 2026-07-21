#!/usr/bin/env python3
"""CLI: ThinkingSOC token stats (RTK + Headroom + MCP JSONL) with time range."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Allow running as script without package install
_LIB = Path(__file__).resolve().parents[1]
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from cli.paths import ToolstackPaths  # noqa: E402
from token_stats.events import load_events  # noqa: E402
from token_stats.headroom import query_headroom  # noqa: E402
from token_stats.report import (  # noqa: E402
    Report,
    aggregate_events,
    format_json,
    format_text,
)
from token_stats.rtk import query_rtk, query_rtk_top_commands  # noqa: E402
from token_stats.time_range import parse_time_range  # noqa: E402


def build_report(
    paths: ToolstackPaths,
    since: str | None,
    until: str | None,
    project: bool,
) -> Report:
    tr = parse_time_range(since, until)
    events_path = paths.data / "token-stats" / "events.jsonl"
    events = load_events(events_path, tr.start, tr.end)
    components = aggregate_events(events)

    project_path = str(paths.repo) if project else None
    rtk = query_rtk(tr.start, tr.end, project_path)
    rtk_top = query_rtk_top_commands(tr.start, tr.end, project_path)

    os.environ.setdefault("HEADROOM_WORKSPACE_DIR", str(paths.data / "headroom"))
    headroom = query_headroom(tr.start, tr.end)

    return Report(
        range_label=tr.label,
        components=components,
        rtk=rtk,
        rtk_top=rtk_top,
        headroom=headroom,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="ThinkingSOC token usage and savings (RTK + Headroom + mcp-lazy JSONL)",
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="status",
        choices=("status", "gain"),
        help="status or gain (same report)",
    )
    parser.add_argument(
        "--since",
        "-s",
        metavar="WHEN",
        help="Start: 24h, 7d, 30d, 2026-06-01, or ISO timestamp (default: 7d ago)",
    )
    parser.add_argument(
        "--until",
        "-u",
        metavar="WHEN",
        help="End ISO timestamp (default: now)",
    )
    parser.add_argument(
        "--project",
        "-p",
        action="store_true",
        help="Limit RTK rows to this repo path",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=("text", "json"),
        default="text",
        help="Output format",
    )
    args = parser.parse_args(argv)

    paths = ToolstackPaths.discover()
    report = build_report(paths, args.since, args.until, args.project)

    if args.format == "json":
        print(json.dumps(format_json(report), indent=2))
    else:
        print(format_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
