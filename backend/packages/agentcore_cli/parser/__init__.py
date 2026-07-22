"""Argument parser for the agentcore CLI.

Split by domain under ``agentcore_cli.parser``; public entry is ``build_parser``.
"""

from __future__ import annotations

import argparse

from agentcore_cli.parser import graph, identity, profiles, remote, reporting, service, sync_llm
from agentcore_cli.parser._core import AgentCoreArgumentParser

__all__ = ["build_parser"]


def build_parser() -> argparse.ArgumentParser:
    parser = AgentCoreArgumentParser(
        prog="agentcore",
        description="AgentCore CLI — manage Usage Profiles, projects, and Cursor MCP",
    )
    parser.add_argument("--version", action="store_true", help="Show version")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("version", help="Show CLI version and repo root")
    sub.add_parser("doctor", help="Check venv, imports, profiles, and PATH")

    # Registration order matches historical help listing.
    service.register(sub)
    identity.register_init(sub)
    reporting.register(sub)
    sync_llm.register(sub)
    identity.register_paths(sub)
    profiles.register(sub)
    remote.register(sub)
    graph.register(sub)

    return parser
