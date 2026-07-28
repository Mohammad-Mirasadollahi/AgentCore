"""Local and remote ingest helpers used during connect / sync."""

from __future__ import annotations

import subprocess
import sys

from agentcore_cli import ui
from agentcore_cli.connect_config import ConnectSettings
from agentcore_cli.connect_flow.ssh import missing_server_source_message, remote_is_dir
from agentcore_cli.util import repo_root


def remote_ingest(settings: ConnectSettings) -> int:
    if not settings.source_server_path or not settings.ssh:
        return 0
    path = settings.source_server_path
    if not remote_is_dir(settings, path):
        msg = missing_server_source_message(path)
        if settings.ingest_mode == "always":
            print(f"   {ui.warn('!')} {msg}", file=sys.stderr)
            return 1
        print(f"   {ui.warn('!')} skipping ingest: {msg}")
        return 0
    # SSH has no TTY — reuse the client-side consent path used by ``agentcore sync``.
    from types import SimpleNamespace

    from agentcore_cli.connect_flow.remote_sync import remote_sync_from_args

    return remote_sync_from_args(
        settings,
        SimpleNamespace(
            tenant=settings.tenant,
            workspace=settings.workspace,
            project=settings.project,
            path=[path],
            allow_cloud_llm=False,
            max_files=None,
            cpu_percent=None,
            progress_interval=None,
            skip_nonconforming=False,
            sync_nonconforming=False,
            exclude_dir=None,
            include_path=None,
            include_ext=None,
        ),
    )


def local_ingest(settings: ConnectSettings, path: str) -> int:
    root = repo_root()
    agentcore = root / ".venv" / "bin" / "agentcore"
    exe = str(agentcore if agentcore.is_file() else "agentcore")
    print(f"   {ui.warn('…')} syncing {path} (local)")
    return subprocess.run(
        [
            exe,
            "sync",
            "--tenant",
            settings.tenant,
            "--workspace",
            settings.workspace,
            "--project",
            settings.project,
            "--path",
            path,
        ],
        cwd=str(root),
    ).returncode


def should_ingest(settings: ConnectSettings) -> bool:
    if not settings.source_server_path and not settings.source_git_remote:
        return False
    mode = settings.ingest_mode
    if mode == "off":
        return False
    if mode == "always":
        return True
    return mode in ("optional", "if_source", "true", "yes")


_local_ingest = local_ingest
_should_ingest = should_ingest
