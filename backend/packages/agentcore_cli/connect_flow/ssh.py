"""SSH helpers for connect / remote sync.

Module contract:
- Role: build and run SSH remote argv for AgentCore server operations.
- SoT / invariants: ``ConnectSettings.ssh`` + ``remote_client.ssh_argv`` quoting rules.
- Failures: non-zero SSH exit is returned to callers; missing ssh target yields no probe.
  Never allocate a remote TTY for interactive prompts (consent stays local).
"""

from __future__ import annotations

import subprocess

from agentcore_cli.connect_config import ConnectSettings


def ssh_command(
    settings: ConnectSettings, remote_command: list[str], *, connect_timeout: int = 15
) -> list[str]:
    from agentcore_cli.remote_client import ssh_argv

    return ssh_argv(
        settings.ssh,
        remote_command,
        connect_timeout=connect_timeout,
        identity_file=settings.ssh_identity or None,
    )


def run_ssh(settings: ConnectSettings, remote_command: list[str], *, connect_timeout: int = 15) -> int:
    return subprocess.run(ssh_command(settings, remote_command, connect_timeout=connect_timeout)).returncode


def remote_is_dir(settings: ConnectSettings, path: str) -> bool:
    """True when *path* is a directory on the SSH AgentCore host."""
    if not path or not settings.ssh:
        return False
    return run_ssh(settings, ["test", "-d", path]) == 0


def missing_server_source_message(path: str) -> str:
    return (
        f"{path} is not a directory on the AgentCore server "
        "(set source.server_path in .agentcore/connect.yaml to a path that exists "
        "there — NFS mount, clone, or synced tree — not the laptop checkout path)"
    )


# Compat aliases used by tests / older call sites.
_ssh_command = ssh_command
_run_ssh = run_ssh
_remote_is_dir = remote_is_dir
_missing_server_source_message = missing_server_source_message
