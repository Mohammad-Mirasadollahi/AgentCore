"""``client``, ``path``, ``ports``."""

from __future__ import annotations

import argparse

from agentcore_cli.util import add_scope_args


def register(sub: argparse._SubParsersAction) -> None:
    client = sub.add_parser("client", help="Dev host wiring to a remote AgentCore install")
    client_sub = client.add_subparsers(dest="client_command", required=True)
    client_sub.add_parser("list-mcp-clients", help="List supported coding-agent MCP config targets")
    wire = client_sub.add_parser("wire-remote", help="Write MCP configs (SSH stdio to AgentCore host)")
    add_scope_args(wire)
    wire.add_argument("--ssh", required=True, help="SSH target user@host for AgentCore server")
    wire.add_argument("--remote-root", required=True, help="AgentCore root on server (e.g. /opt/AgentCore)")
    wire.add_argument("--out", default="", help="Merge into this mcp.json path")
    wire.add_argument(
        "--project-dir",
        default="",
        help="Application repo root (default: cwd); used when --out is omitted",
    )
    wire.add_argument("--server-name", default="", help="MCP server key (default: AgentCore-Programming)")
    wire.add_argument("--register", action="store_true", help="Register/activate project on server")
    wire.add_argument("--project-name", default="", help="Project display name for --register")
    wire.add_argument("--usage-profile", default="programming-cursor-mcp")
    wire.add_argument("--remote-python", default="", help="Override remote venv python path")
    wire.add_argument(
        "--remote-os",
        choices=("unix", "windows"),
        default="unix",
        help="AgentCore host OS (venv layout)",
    )
    wire.add_argument(
        "--clients",
        default="all",
        help="Comma-separated client ids or 'all' (default: all project-scoped targets)",
    )
    wire.add_argument(
        "--include-user-clients",
        action="store_true",
        help="Also merge into user-global configs (cursor-user, claude-desktop)",
    )
    wire.add_argument("--skip-doctor", action="store_true", help="Skip remote python presence check")
    wire.add_argument("--dry-run", action="store_true", help="Print fragment only")
    doc = client_sub.add_parser("doctor-remote", help="Check SSH access to remote MCP serve entrypoint")
    doc.add_argument("--ssh", required=True)
    doc.add_argument("--remote-root", required=True)
    doc.add_argument("--remote-python", default="")
    doc.add_argument("--remote-os", choices=("unix", "windows"), default="unix")

    path_cmd = sub.add_parser("path", help="Install agentcore onto user PATH")
    path_sub = path_cmd.add_subparsers(dest="path_command", required=True)
    install = path_sub.add_parser("install", help="Symlink ~/.local/bin/agentcore -> .venv/bin/agentcore")
    install.add_argument(
        "--shell-rc",
        default="",
        help="Optional rc file to append PATH export (e.g. .bashrc)",
    )

    ports = sub.add_parser("ports", help="Port profile preflight")
    ports_sub = ports.add_subparsers(dest="ports_command", required=True)
    ports_show = ports_sub.add_parser("show", help="Show resolved ports from profile (env overrides)")
    ports_show.add_argument("--profile", default="", help="Port profile JSON path (default: agentcore-dev)")
    ports_check = ports_sub.add_parser("check", help="Check that profile ports are free to bind")
    ports_check.add_argument("--profile", default="", help="Port profile JSON path (default: agentcore-dev)")
