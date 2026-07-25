"""Remote purge from a client install (SSH to AgentCore server).

Security: effective scope is always connect.yaml; CLI scope flags must match or fail.
Never falls back to local GraphService.purge_scope.
"""

from __future__ import annotations

import argparse
import shlex

from agentcore_cli import ui
from agentcore_cli.connect_config import ConnectSettings
from agentcore_cli.connect_flow.ssh import run_ssh


def locked_scope_from_settings(settings: ConnectSettings) -> tuple[str, str, str]:
    tenant = (settings.tenant or "").strip()
    workspace = (settings.workspace or "").strip()
    project = (settings.project or "").strip()
    if not tenant or not workspace or not project:
        raise SystemExit(
            "error: connect.yaml must set scope.tenant, scope.workspace, and scope.project "
            "before client purge"
        )
    return tenant, workspace, project


def assert_cli_scope_matches_connect(args: argparse.Namespace, settings: ConnectSettings) -> None:
    """Hard-fail when CLI scope flags disagree with connect.yaml (no silent prefer)."""
    locked = locked_scope_from_settings(settings)
    pairs = (
        ("tenant", locked[0], str(getattr(args, "tenant", None) or "").strip()),
        ("workspace", locked[1], str(getattr(args, "workspace", None) or "").strip()),
        ("project", locked[2], str(getattr(args, "project", None) or "").strip()),
    )
    for name, want, got in pairs:
        if got and got != want:
            raise SystemExit(
                f"error: --{name} {got!r} does not match connect.yaml scope "
                f"({want!r}); client purge cannot change scope"
            )


def remote_sync_pidfile(settings: ConnectSettings, tenant: str, workspace: str, project: str) -> str:
    root = settings.remote_root.rstrip("/\\")
    return f"{root}/.agentcore/run/remote-sync-{tenant}-{workspace}-{project}.pid"


def remote_purge_from_args(settings: ConnectSettings, args: argparse.Namespace) -> int:
    if not settings.ssh:
        raise SystemExit("error: client purge requires server.ssh in connect.yaml")
    if not getattr(args, "yes", False):
        raise SystemExit("error: purge requires --yes (destructive: wipes project graph data)")

    assert_cli_scope_matches_connect(args, settings)
    tenant, workspace, project = locked_scope_from_settings(settings)
    root = settings.remote_root.rstrip("/\\")
    if not root:
        raise SystemExit("error: server.remote_root missing in connect.yaml")

    agentcore = f"{root}/.venv/bin/agentcore"
    pidfile = remote_sync_pidfile(settings, tenant, workspace, project)
    q = shlex.quote(pidfile)
    check = run_ssh(
        settings,
        [
            "bash",
            "-lc",
            (
                f"if [ -f {q} ]; then "
                f"pid=$(cat {q} 2>/dev/null || true); "
                f"if [ -n \"$pid\" ] && kill -0 \"$pid\" 2>/dev/null; then exit 42; fi; "
                f"fi; exit 0"
            ),
        ],
    )
    if check == 42:
        raise SystemExit(
            "error: remote sync still running for this scope; stop it (Ctrl+C) before purge"
        )

    remote = [
        agentcore,
        "purge",
        "--tenant",
        tenant,
        "--workspace",
        workspace,
        "--project",
        project,
        "--yes",
    ]
    ui.blank()
    print(f"   {ui.warn('…')} remote purge on server ({settings.ssh})")
    ui.kv("Scope", f"{tenant}/{workspace}/{project}")
    return run_ssh(settings, remote)
