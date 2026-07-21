#!/usr/bin/env python3
"""Unified ThinkingSOC ai-toolstack CLI (sync, stats, benchmark, verify, timer)."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1]
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from cli.paths import ToolstackPaths  # noqa: E402
from cli.token_stats_gain import build_report  # noqa: E402
from token_stats.benchmark import run_benchmark  # noqa: E402
from token_stats.report import format_json, format_text  # noqa: E402


def _repo_paths() -> ToolstackPaths:
    return ToolstackPaths.discover()


def _sync_entry() -> Path:
    return _repo_paths().ai_toolstack / "lib/sync/entry.sh"


def cmd_sync(argv: list[str]) -> int:
    entry = _sync_entry()
    if not entry.is_file():
        print(f"FAIL: sync entry missing: {entry}", file=sys.stderr)
        return 1
    env = os.environ.copy()
    env["AI_TOOLSTACK_INTERNAL"] = "1"
    env.setdefault("AI_TOOLSTACK_CLI", str(_repo_paths().repo / "ai-toolstack/scripts/ai-toolstack.sh"))
    proc = subprocess.run(["bash", str(entry), *argv], env=env)
    return int(proc.returncode or 0)


def cmd_stats(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="ai-toolstack stats", description="Token usage and savings")
    parser.add_argument("command", nargs="?", default="status", choices=("status", "gain"))
    parser.add_argument("--since", "-s", metavar="WHEN")
    parser.add_argument("--until", "-u", metavar="WHEN")
    parser.add_argument("--project", "-p", action="store_true")
    parser.add_argument("--format", "-f", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    paths = _repo_paths()
    report = build_report(paths, args.since, args.until, args.project)
    if args.format == "json":
        print(json.dumps(format_json(report), indent=2))
    else:
        print(format_text(report))
    return 0


def cmd_benchmark(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="ai-toolstack benchmark")
    parser.add_argument(
        "target",
        nargs="?",
        default="all",
        choices=("all",),
        help="Token benchmark (MCP lazy + headroom + RTK)",
    )
    parser.add_argument("--format", "-f", choices=("text", "json"), default="text")
    args, _rest = parser.parse_known_args(argv)
    paths = _repo_paths()
    result = run_benchmark(paths)
    if args.format == "json":
        out = {
            "fixed_per_turn_tokens": result["fixed"].fixed_per_turn,
            "mcp_saved_per_turn": result["fixed"].mcp_saved_per_turn,
            "probes": result["probes"],
            "scenarios": [
                {
                    "name": s.name,
                    "description": s.description,
                    "steps": s.steps,
                    "total_tokens_out": s.total_out,
                    "total_tokens_saved": s.total_saved,
                }
                for s in result["scenarios"]
            ],
            "text": result.get("text"),
        }
        print(json.dumps(out, indent=2))
    else:
        print(result.get("text") or "")
    return 0


def cmd_verify(argv: list[str]) -> int:
    paths = _repo_paths()
    env = os.environ.copy()
    env["REPO_ROOT"] = str(paths.repo)
    env["PYTHONPATH"] = f"{paths.ai_toolstack / 'lib'}{os.pathsep}{env.get('PYTHONPATH', '')}"
    proc = subprocess.run(
        [sys.executable, str(paths.ai_toolstack / "lib/cli/verify_agent_stack.py"), *argv],
        env=env,
    )
    return int(proc.returncode or 0)


def cmd_timer(argv: list[str]) -> int:
    paths = _repo_paths()
    env = os.environ.copy()
    proc = subprocess.run(
        ["bash", str(paths.ai_toolstack / "lib/cli/timer.sh"), *argv],
        env=env,
        cwd=str(paths.repo),
    )
    return int(proc.returncode or 0)


def _print_help() -> None:
    print(
        """ThinkingSOC ai-toolstack — single entry point

Usage:
  ./ai-toolstack/scripts/ai-toolstack.sh [sync-flags...]   lightweight sync (re-run install.sh for MCP)
  ./ai-toolstack/scripts/ai-toolstack.sh stats [status|gain] [--since 24h] [-p]
  ./ai-toolstack/scripts/ai-toolstack.sh benchmark [all] [-f json]
  ./ai-toolstack/scripts/ai-toolstack.sh verify [--quick]
  ./ai-toolstack/scripts/ai-toolstack.sh timer install|status|uninstall

Default sync examples:
  ai-toolstack.sh              no-op plan (re-run install.sh for MCP config)
  ai-toolstack.sh --check      plan only

Discovery: repo docs + narrow rg/Read. Cursor MCP: mcp-lazy only (memory + headroom backends).
"""
    )


_SUBCOMMANDS = frozenset({"stats", "benchmark", "verify", "timer", "sync", "help"})


def main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    if not argv:
        return cmd_sync([])
    if argv[0] in ("-h", "--help", "help"):
        _print_help()
        return 0

    command = argv[0]

    if command not in _SUBCOMMANDS:
        return cmd_sync(argv)

    rest = argv[1:]
    if command == "sync":
        return cmd_sync(rest)
    if command == "stats":
        return cmd_stats(rest)
    if command == "benchmark":
        return cmd_benchmark(rest)
    if command == "verify":
        return cmd_verify(rest)
    if command == "timer":
        return cmd_timer(rest)

    print(f"Unknown command: {command}\n", file=sys.stderr)
    _print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
