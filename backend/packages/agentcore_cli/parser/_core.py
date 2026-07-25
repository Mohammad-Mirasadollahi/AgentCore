"""Shared argparse helpers for the agentcore CLI parser package."""

from __future__ import annotations

import argparse
import sys

_SYNC_MAX_FILE_DASHED = frozenset({"-max-file", "--max-file", "-max-files", "--max-files"})
DEFAULT_SYNC_MAX_FILES = 2000


def peel_sync_max_file(argv: list[str], error) -> tuple[list[str], int | None]:
    """Accept bare ``max-file N`` on sync; dashed forms are aliases (same value)."""
    if not argv or argv[0] != "sync":
        return argv, None
    out: list[str] = []
    override: int | None = None
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok in _SYNC_MAX_FILE_DASHED or tok == "max-file":
            label = "max-file" if tok == "max-file" else tok.lstrip("-")
            if i + 1 >= len(argv):
                error(f"argument {label}: expected one integer argument")
            try:
                override = int(argv[i + 1])
            except ValueError:
                error(f"argument {label}: invalid int value: {argv[i + 1]!r}")
            i += 2
            continue
        out.append(tok)
        i += 1
    return out, override


class AgentCoreArgumentParser(argparse.ArgumentParser):
    def parse_known_args(self, args=None, namespace=None):
        if args is None:
            args = sys.argv[1:]
        args, max_files_override = peel_sync_max_file(list(args), self.error)
        ns, rest = super().parse_known_args(args, namespace)
        if max_files_override is not None:
            ns.max_files = max_files_override
        return ns, rest
