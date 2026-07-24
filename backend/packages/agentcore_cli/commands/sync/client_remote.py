"""Client checkout: run sync on the AgentCore server via connect.yaml SSH."""

from __future__ import annotations

import argparse


def cmd_sync_client_remote(args: argparse.Namespace) -> int:
    from agentcore_cli.connect_config import load_connect_settings, try_resolve_config_path
    from agentcore_cli.connect_flow import remote_sync_from_args
    from agentcore_cli.service_runtime.paths import missing_local_stack_message
    from agentcore_cli.util import repo_root

    cfg = try_resolve_config_path()
    if cfg is None:
        raise SystemExit(missing_local_stack_message(repo_root()))
    settings = load_connect_settings(config_path=str(cfg), allow_incomplete=True)
    if not settings.ssh:
        raise SystemExit(missing_local_stack_message(repo_root()))
    return remote_sync_from_args(settings, args)


# Compat alias.
_cmd_sync_client_remote = cmd_sync_client_remote
