"""Dev client wiring (remote AgentCore host over SSH)."""

from __future__ import annotations

import argparse
from pathlib import Path

from agentcore_cli.mcp_client_targets import DEFAULT_SERVER_NAME, list_mcp_client_targets
from agentcore_cli.remote_client import doctor_remote, wire_remote_dev_host
from agentcore_cli.util import print_json, require_scope


def cmd_client_list_mcp_clients(_args: argparse.Namespace) -> int:
    print_json(list_mcp_client_targets())
    return 0


def cmd_client_wire_remote(args: argparse.Namespace) -> int:
    tenant, workspace, project_id = require_scope(args)
    ssh_target = str(args.ssh).strip()
    remote_root = str(args.remote_root).strip()
    if not ssh_target or not remote_root:
        raise SystemExit("error: --ssh and --remote-root are required")

    out_path = Path(args.out).resolve() if args.out else None
    project_dir = Path(args.project_dir).resolve() if args.project_dir else Path.cwd()

    if args.dry_run:
        from agentcore_cli.remote_client import materialize_ssh_mcp_fragment

        fragment = materialize_ssh_mcp_fragment(
            ssh_target=ssh_target,
            remote_root=remote_root,
            tenant=tenant,
            workspace=workspace,
            project_id=project_id,
            server_name=str(args.server_name or DEFAULT_SERVER_NAME),
            remote_python=str(args.remote_python).strip() or None,
            remote_os=str(args.remote_os or "unix"),
        )
        print_json(fragment)
        return 0

    return wire_remote_dev_host(
        ssh_target=ssh_target,
        remote_root=remote_root,
        tenant=tenant,
        workspace=workspace,
        project_id=project_id,
        out_path=out_path,
        server_name=str(args.server_name or DEFAULT_SERVER_NAME),
        project_dir=project_dir,
        register=bool(args.register),
        project_name=str(args.project_name or ""),
        usage_profile=str(args.usage_profile or "programming-cursor-mcp"),
        dry_run=False,
        remote_python=str(args.remote_python).strip() or None,
        remote_os=str(args.remote_os or "unix"),
        skip_doctor=bool(args.skip_doctor),
        clients=str(args.clients or "all"),
        include_user_clients=bool(args.include_user_clients),
    )


def cmd_client_doctor_remote(args: argparse.Namespace) -> int:
    return doctor_remote(
        str(args.ssh).strip(),
        str(args.remote_root).strip(),
        remote_python=str(args.remote_python).strip() or None,
        remote_os=str(args.remote_os or "unix"),
    )
