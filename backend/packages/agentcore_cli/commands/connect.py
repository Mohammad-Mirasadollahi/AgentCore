"""`agentcore connect` — one-command coding-agent onboarding."""

from __future__ import annotations

import argparse
from pathlib import Path

from agentcore_cli.connect_config import (
    ConnectSettings,
    default_connect_yaml_path,
    load_connect_settings,
    try_resolve_config_path,
    write_connect_template,
)
from agentcore_cli.connect_flow import run_connect
from agentcore_cli.connect_wizard import ensure_ssh_ready, run_ssh_connect_wizard


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


def _config_path_from_args(args: argparse.Namespace) -> Path | None:
    explicit = str(args.config or "").strip()
    if explicit:
        return Path(explicit).expanduser()
    return try_resolve_config_path()


def cmd_connect(args: argparse.Namespace) -> int:
    if args.init:
        path = write_connect_template()
        print(f"wrote {path}")
        print("Edit connect.yaml (local / ssh / http), then run: agentcore connect")
        return 0

    work = Path.cwd()
    force_edit = bool(getattr(args, "edit", False))

    if args.local and not args.config:
        settings = _settings_for_local(args)
        return run_connect(settings, project_dir=work, dry_run=bool(args.dry_run))

    cfg = _config_path_from_args(args)
    if cfg is None and not args.local:
        # Zero-config: interactive SSH wizard writes <checkout>/.agentcore/connect.yaml.
        settings = run_ssh_connect_wizard(
            existing=ConnectSettings(
                project=str(args.project or "") or work.name,
                project_name=str(args.project or "") or work.name,
                clients=str(args.clients or "all"),
                include_user_clients=bool(args.include_user_clients),
                tenant=str(args.tenant or "default"),
                workspace=str(args.workspace or "default"),
                prefer_http=False,
            ),
            rotate=force_edit,
            config_path=default_connect_yaml_path(),
            project_dir=work,
            ssh_override=str(args.ssh or ""),
        )
        if args.include_user_clients:
            settings.include_user_clients = True
        return run_connect(settings, project_dir=work, dry_run=bool(args.dry_run))

    settings = load_connect_settings(
        config_path=str(args.config or ""),
        project_override=str(args.project or ""),
        ssh_override=str(args.ssh or ""),
        api_url_override=str(args.server or ""),
        clients_override=str(args.clients or ""),
        cwd=work,
        allow_incomplete=force_edit,
    )
    if args.local:
        settings.local = True
        settings.prefer_http = False
        if not settings.source_server_path:
            settings.source_server_path = str(work)
    if args.include_user_clients:
        settings.include_user_clients = True
    if args.tenant:
        settings.tenant = str(args.tenant)
    if args.workspace:
        settings.workspace = str(args.workspace)

    if not settings.local:
        settings = ensure_ssh_ready(
            settings,
            force_edit=force_edit,
            allow_wizard=not bool(args.dry_run),
            config_path=cfg,
            project_dir=work,
            ssh_override=str(args.ssh or ""),
        )

    return run_connect(settings, project_dir=work, dry_run=bool(args.dry_run))
