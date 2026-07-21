"""`agentcore connect` — one-command coding-agent onboarding."""

from __future__ import annotations

import argparse
from pathlib import Path

from agentcore_cli.connect_config import ConnectSettings, load_connect_settings, write_connect_template
from agentcore_cli.connect_flow import run_connect


def _settings_for_local(args: argparse.Namespace) -> ConnectSettings:
    """Same-host connect: scope from flags → identity/env/connect.yaml (not hardcoded dogfood)."""
    from agentcore_cli.cli_defaults import resolve_operator_scope

    work = Path.cwd()
    tenant, workspace, project = resolve_operator_scope(
        tenant=str(args.tenant or ""),
        workspace=str(args.workspace or ""),
        project=str(args.project or ""),
        cwd=work,
    )
    return ConnectSettings(
        local=True,
        remote_root=str(Path(args.remote_root).resolve()) if args.remote_root else str(work),
        tenant=tenant,
        workspace=workspace,
        project=project,
        project_name=project,
        usage_profile="programming-cursor-mcp",
        clients=str(args.clients or "all"),
        include_user_clients=bool(args.include_user_clients),
        register=True,
        smoke_test=False,
        ingest_mode="off",
        source_server_path=str(work),
        prefer_http=False,
    )


def cmd_connect(args: argparse.Namespace) -> int:
    if args.init:
        path = write_connect_template()
        print(f"wrote {path}")
        print("Edit connect.yaml (local / ssh / http), then run: agentcore connect")
        return 0

    if args.local and not args.config:
        settings = _settings_for_local(args)
    else:
        settings = load_connect_settings(
            config_path=str(args.config or ""),
            project_override=str(args.project or ""),
            ssh_override=str(args.ssh or ""),
            api_url_override=str(args.server or ""),
            clients_override=str(args.clients or ""),
            cwd=Path.cwd(),
        )
        if args.local:
            settings.local = True
            settings.prefer_http = False
            if not settings.source_server_path:
                settings.source_server_path = str(Path.cwd())
    if args.include_user_clients:
        settings.include_user_clients = True
    if args.tenant:
        settings.tenant = str(args.tenant)
    if args.workspace:
        settings.workspace = str(args.workspace)
    return run_connect(settings, project_dir=Path.cwd(), dry_run=bool(args.dry_run))
