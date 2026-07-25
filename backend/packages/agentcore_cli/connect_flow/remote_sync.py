"""Client remote ``agentcore sync`` over SSH.

Module contract:
- Role: build remote sync argv and run it on the AgentCore server.
- SoT / invariants: local TTY cloud-LLM consent before SSH; bare ``max-file``; no ``--force``.
- Failures: missing ssh/source fail closed; declined consent aborts before SSH.
  Never rely on a remote TTY for consent prompts.
"""

from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path
from typing import Any

from agentcore_cli import ui
from agentcore_cli.connect_config import ConnectSettings
from agentcore_cli.connect_flow.ssh import (
    missing_server_source_message,
    remote_is_dir,
    run_ssh_interruptible,
    ssh_command,
)


ASSUME_CLOUD_LLM_CONFIG: dict[str, Any] = {
    "enabled": True,
    "api_base": "https://unverified-remote-llm.invalid",
    "docs_enabled": True,
    "embeddings_enabled": True,
    "route_docs": {"primary_model": "openai/unverified", "fallback_models": []},
    "route_embed": {"primary_model": "openai/unverified", "fallback_models": []},
}


def remote_llm_config(settings: ConnectSettings) -> dict[str, Any]:
    """Best-effort server ``llm_config``; assume cloud (prompt) if probe fails."""
    root = settings.remote_root.rstrip("/\\")
    py = f"{root}/.venv/bin/python"
    snippet = (
        "from agentcore_cli.cli_defaults import load_dotenv_files; "
        "load_dotenv_files(); "
        "from agentcore_cli.commands.graph import _graph_service; "
        "import json; "
        "print(json.dumps(_graph_service().llm_config()))"
    )
    try:
        result = subprocess.run(
            ssh_command(settings, [py, "-c", snippet]),
            capture_output=True,
            text=True,
            timeout=45,
        )
    except (OSError, subprocess.TimeoutExpired):
        return dict(ASSUME_CLOUD_LLM_CONFIG)
    if result.returncode != 0:
        return dict(ASSUME_CLOUD_LLM_CONFIG)
    lines = [ln.strip() for ln in (result.stdout or "").splitlines() if ln.strip()]
    if not lines:
        return dict(ASSUME_CLOUD_LLM_CONFIG)
    try:
        payload = json.loads(lines[-1])
    except json.JSONDecodeError:
        return dict(ASSUME_CLOUD_LLM_CONFIG)
    return payload if isinstance(payload, dict) else dict(ASSUME_CLOUD_LLM_CONFIG)


def client_remote_cloud_llm_allowed(
    settings: ConnectSettings,
    args: Any,
    *,
    tenant: str,
    workspace: str,
    project: str,
    paths: list[str],
) -> bool:
    """Prompt on the local TTY when server LLM is non-private; SSH cannot ask."""
    from agentcore_cli.commands.graph import _require_cloud_llm_consent

    class _ConfigSvc:
        def __init__(self, config: dict[str, Any]) -> None:
            self._config = config

        def llm_config(self) -> dict[str, Any]:
            return self._config

    return _require_cloud_llm_consent(
        _ConfigSvc(remote_llm_config(settings)),
        allowed=bool(getattr(args, "allow_cloud_llm", False)),
        tenant=tenant,
        workspace=workspace,
        project=project,
        paths=paths,
    )


def remote_sync_from_args(settings: ConnectSettings, args: Any) -> int:
    """Run `agentcore sync` on the connected server (client checkout path)."""
    if not settings.ssh:
        raise SystemExit("error: connect.yaml has no server.ssh for remote sync")
    root = settings.remote_root.rstrip("/\\")
    agentcore = f"{root}/.venv/bin/agentcore"
    tenant = str(getattr(args, "tenant", None) or settings.tenant or "default")
    workspace = str(getattr(args, "workspace", None) or settings.workspace or "default")
    project = str(getattr(args, "project", None) or settings.project or "project")
    remote_cmd = [
        agentcore,
        "sync",
        "--tenant",
        tenant,
        "--workspace",
        workspace,
        "--project",
        project,
    ]
    paths = list(getattr(args, "path", None) or [])
    if paths:
        for path in paths:
            remote_cmd.extend(["--path", str(path)])
        target = ", ".join(str(p) for p in paths)
        consent_paths = [str(p) for p in paths]
    elif settings.source_server_path:
        if not remote_is_dir(settings, settings.source_server_path):
            raise SystemExit(f"error: {missing_server_source_message(settings.source_server_path)}")
        remote_cmd.extend(["--path", settings.source_server_path])
        target = settings.source_server_path
        consent_paths = [settings.source_server_path]
    else:
        # Do not fall back to the AgentCore host identity pins — that silently syncs
        # /opt/AgentCore (or whatever the server last pinned) instead of the client app.
        raise SystemExit(
            "error: remote sync needs an explicit server-side software path\n"
            "  In .agentcore/connect.yaml (on the client) set:\n"
            "    source:\n"
            "      server_path: /opt/YourApp   # path that EXISTS on the AgentCore server\n"
            "  Or pass once: agentcore sync --path /opt/YourApp\n"
            "  The client checkout path is not used over SSH; copy/NFS/clone the tree "
            "onto the server first if it is missing there."
        )

    # SSH has no TTY — ask on the local interactive client, then forward the flag.
    allow_cloud = client_remote_cloud_llm_allowed(
        settings,
        args,
        tenant=tenant,
        workspace=workspace,
        project=project,
        paths=consent_paths,
    )
    if allow_cloud:
        remote_cmd.append("--allow-cloud-llm")

    max_files = getattr(args, "max_files", None)
    if max_files is not None:
        # Bare form only — AgentCoreArgumentParser.peel_sync_max_file rejects --max-files.
        remote_cmd.extend(["max-file", str(max_files)])
    cpu_percent = getattr(args, "cpu_percent", None)
    if cpu_percent is not None and str(cpu_percent).strip() != "":
        remote_cmd.extend(["--cpu-percent", str(cpu_percent).strip()])
    progress_interval = getattr(args, "progress_interval", None)
    if progress_interval is not None:
        remote_cmd.extend(["--progress-interval", str(progress_interval)])
    if getattr(args, "skip_nonconforming", False):
        remote_cmd.append("--skip-nonconforming")
    if getattr(args, "sync_nonconforming", False):
        remote_cmd.append("--sync-nonconforming")
    for item in getattr(args, "exclude_dir", None) or []:
        remote_cmd.extend(["--exclude-dir", str(item)])
    for item in getattr(args, "include_path", None) or []:
        remote_cmd.extend(["--include-path", str(item)])
    for item in getattr(args, "include_ext", None) or []:
        remote_cmd.extend(["--include-ext", str(item)])
    # Do not forward --force: sync has no such flag (init/project do).
    print(f"   {ui.warn('…')} remote sync on server ({target})")
    print(f"   {ui.dim('Ctrl+C stops the server-side sync (not only this SSH session).')}")

    # Pidfile so client Ctrl+C can kill the remote process (SSH drop alone leaves it running).
    pidfile = (
        f"{root}/.agentcore/run/"
        f"remote-sync-{tenant}-{workspace}-{project}.pid"
    )
    wrapped = (
        f"mkdir -p {shlex.quote(str(Path(pidfile).parent))} && "
        f"echo $$ > {shlex.quote(pidfile)} && "
        f"trap 'rm -f {shlex.quote(pidfile)}' EXIT && "
        f"exec {shlex.join(remote_cmd)}"
    )
    return run_ssh_interruptible(
        settings,
        ["bash", "-lc", wrapped],
        on_interrupt_remote=[
            "bash",
            "-lc",
            (
                f"if [ -f {shlex.quote(pidfile)} ]; then "
                f"kill -INT \"$(cat {shlex.quote(pidfile)})\" 2>/dev/null || true; "
                f"sleep 2; "
                f"kill -TERM \"$(cat {shlex.quote(pidfile)})\" 2>/dev/null || true; "
                f"rm -f {shlex.quote(pidfile)}; "
                f"fi"
            ),
        ],
    )


# Compat aliases for monkeypatches / older names.
_ASSUME_CLOUD_LLM_CONFIG = ASSUME_CLOUD_LLM_CONFIG
_remote_llm_config = remote_llm_config
_client_remote_cloud_llm_allowed = client_remote_cloud_llm_allowed
