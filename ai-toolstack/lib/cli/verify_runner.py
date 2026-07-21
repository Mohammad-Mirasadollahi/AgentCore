"""Shared pass/fail/warn helpers for verify scripts."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from cli.log_util import ts_section


class VerifyRunner:
    def __init__(self) -> None:
        self.pass_count = 0
        self.warn_count = 0
        self.fail_count = 0

    def pass_(self, message: str) -> None:
        print(f"  OK   {message}")
        self.pass_count += 1

    def warn(self, message: str) -> None:
        print(f"  WARN {message}", file=sys.stderr)
        self.warn_count += 1

    def fail(self, message: str) -> None:
        print(f"  FAIL {message}", file=sys.stderr)
        self.fail_count += 1

    def section(self, title: str) -> None:
        ts_section(title)

    def file_ok(self, path: Path, label: str) -> None:
        if path.is_file():
            self.pass_(label)
        else:
            self.fail(f"{label}: missing {path}")

    def executable_ok(self, path: Path, label: str) -> None:
        if path.is_file() and os.access(path, os.X_OK):
            self.pass_(label)
        else:
            self.fail(f"{label}: not executable or missing ({path})")

    def symlink_ok(self, link: Path, expected: Path, label: str) -> None:
        if not link.exists() and not link.is_symlink():
            self.fail(f"{label}: missing ({link})")
            return
        try:
            resolved = link.resolve()
            target = expected.resolve()
        except OSError:
            self.fail(f"{label}: cannot resolve {link}")
            return
        if resolved == target:
            self.pass_(label)
        else:
            self.fail(f"{label}: {link} -> {resolved} (expected {target})")

    def json_ok(self, path: Path, label: str) -> None:
        if not path.is_file():
            self.fail(f"{label}: missing {path}")
            return
        try:
            json.loads(path.read_text(encoding="utf-8"))
            self.pass_(label)
        except (json.JSONDecodeError, OSError):
            self.fail(f"{label}: invalid JSON ({path})")
