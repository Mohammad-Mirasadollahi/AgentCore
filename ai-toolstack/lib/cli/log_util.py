"""Timestamped console logging (Python counterpart of lib/log.sh)."""

from __future__ import annotations

from datetime import datetime


def ts_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def ts_log(message: str) -> None:
    print(f"[{ts_now()}] {message}")


def ts_section(title: str) -> None:
    print()
    ts_log(f"=== {title} ===")


def ts_item(message: str) -> None:
    ts_log(f"  {message}")


def ts_item_stderr(message: str) -> None:
    import sys

    print(f"[{ts_now()}]   {message}", file=sys.stderr)
