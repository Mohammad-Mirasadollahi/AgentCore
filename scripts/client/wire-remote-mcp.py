#!/usr/bin/env python3
"""Thin launcher: run AgentCore client wire-remote without adding agentcore to PATH."""
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
    if len(sys.argv) > 1 and sys.argv[1] == "wire-remote":
        return agentcore_main(["client", *sys.argv[1:]])
    if len(sys.argv) > 1 and sys.argv[1] == "doctor-remote":
        return agentcore_main(["client", *sys.argv[1:]])
    sys.stderr.write("usage: wire-remote-mcp.py wire-remote|doctor-remote ... (same flags as agentcore client)\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
