#!/usr/bin/env python3
"""Thin launcher: run AgentCore client connect without adding agentcore to PATH.

SSH wiring (``wire-remote`` / ``doctor-remote``) has been removed from the
product; use ``connect`` (HTTPS) instead.
"""
from __future__ import annotations

import sys
from pathlib import Path


def _bootstrap_path() -> None:
    root = Path(__file__).resolve().parents[2]
    packages = root / "backend" / "packages"
    if packages.is_dir() and str(packages) not in sys.path:
        sys.path.insert(0, str(packages))


def main() -> int:
    _bootstrap_path()
    from agentcore_cli.main import main as agentcore_main

    if len(sys.argv) > 1 and sys.argv[1] == "connect":
        return agentcore_main(["connect", *sys.argv[2:]])
    if len(sys.argv) > 1 and sys.argv[1] == "list-mcp-clients":
        return agentcore_main(["client", "list-mcp-clients"])
    sys.stderr.write("usage: wire-remote-mcp.py connect|list-mcp-clients ... (same flags as agentcore)\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
