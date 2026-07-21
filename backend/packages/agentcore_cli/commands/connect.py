"""`agentcore connect` — one-command coding-agent onboarding."""

from __future__ import annotations

import argparse
from pathlib import Path

from agentcore_cli.connect_config import load_connect_settings, write_connect_template
from agentcore_cli.connect_flow import run_connect


def cmd_connect(args: argparse.Namespace) -> int:
    if args.init:
        path = write_connect_template()
        print(f"wrote {path}")
        print("Edit server.ssh and scope, then run: agentcore connect")
        return 0

    settings = load_connect_settings(
        config_path=str(args.config or ""),
        project_override=str(args.project or ""),
        ssh_override=str(args.ssh or ""),
        api_url_override=str(args.server or ""),
        clients_override=str(args.clients or ""),
        cwd=Path.cwd(),
    )
    if args.include_user_clients:
        settings.include_user_clients = True
    return run_connect(settings, project_dir=Path.cwd(), dry_run=bool(args.dry_run))
