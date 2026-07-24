"""Interactive first-time / --edit SSH onboarding for `agentcore connect`."""

from __future__ import annotations

import getpass
import sys
from dataclasses import replace
from pathlib import Path
from typing import Callable

from agentcore_cli import ui
from agentcore_cli.connect_config import (
    ConnectSettings,
    try_resolve_config_path,
    write_or_merge_connect_yaml,
)
from agentcore_cli.ssh_bootstrap import bootstrap_ssh_auth, default_identity_path, probe_batch_mode


PromptFn = Callable[[str], str]
PasswordFn = Callable[[str], str]


def parse_ssh_target(raw: str) -> tuple[str, str]:
    """Split ``user@host`` into (user, host). Host-only returns empty user."""
    text = (raw or "").strip()
    if not text:
        return "", ""
    if "@" in text:
        user, _, host = text.partition("@")
        return user.strip(), host.strip()
    return "", text


def format_ssh_target(user: str, host: str) -> str:
    user = user.strip()
    host = host.strip()
    if not host:
        raise SystemExit("error: SSH host is required")
    if user:
        return f"{user}@{host}"
    return host


def _require_tty() -> None:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise SystemExit(
            "error: interactive SSH setup needs a TTY; "
            "create ~/.agentcore/connect.yaml (agentcore connect --init) "
            "or run from a terminal: agentcore connect / agentcore connect --edit"
        )


def _prompt_line(prompt: str, *, default: str = "", input_fn: PromptFn = input) -> str:
    suffix = f" [{default}]" if default else ""
    raw = input_fn(f"{prompt}{suffix}: ").strip()
    return raw or default


def run_ssh_connect_wizard(
    *,
    existing: ConnectSettings | None = None,
    rotate: bool = False,
    config_path: Path | None = None,
    project_dir: Path | None = None,
    ssh_override: str = "",
    input_fn: PromptFn = input,
    password_fn: PasswordFn = getpass.getpass,
) -> ConnectSettings:
    """Prompt for host/user/password, install pubkey, merge connect.yaml, return settings."""
    _require_tty()
    work = project_dir or Path.cwd()
    base = existing or ConnectSettings()

    ui.blank()
    ui.heading("SSH connect setup" if not rotate else "SSH connect edit (replace pubkey)")
    ui.blank()
    ui.bullet("Password is used once to install an AgentCore SSH key; it is never saved.")
    ui.bullet("Hand-edit ~/.agentcore/connect.yaml for scope/clients; use --edit to change SSH identity.")
    ui.blank()

    override_user, override_host = parse_ssh_target(ssh_override)
    cur_user, cur_host = parse_ssh_target(base.ssh)
    host_default = override_host or cur_host
    user_default = override_user or cur_user or getpass.getuser() or "ops"

    host = _prompt_line("Server host", default=host_default, input_fn=input_fn)
    user = _prompt_line("SSH username", default=user_default, input_fn=input_fn)
    ssh_target = format_ssh_target(user, host)

    remote_root = _prompt_line(
        "AgentCore remote root",
        default=base.remote_root or "/opt/AgentCore",
        input_fn=input_fn,
    )
    tenant = _prompt_line("Tenant", default=base.tenant or "default", input_fn=input_fn)
    workspace = _prompt_line("Workspace", default=base.workspace or "default", input_fn=input_fn)
    project = base.project or work.name or "project"

    password = password_fn(f"SSH password for {ssh_target}: ")
    if not password:
        raise SystemExit("error: empty password")

    identity = Path(base.ssh_identity).expanduser() if base.ssh_identity else default_identity_path()
    print(f"   {ui.warn('…')} installing AgentCore SSH pubkey on {ssh_target}")
    result = bootstrap_ssh_auth(
        ssh_target,
        password,
        rotate=rotate,
        identity=identity,
    )
    # Drop password from locals as soon as possible (best-effort).
    password = ""

    settings = replace(
        base,
        ssh=ssh_target,
        remote_root=remote_root.rstrip("/\\") or "/opt/AgentCore",
        ssh_identity=str(result.private_path),
        tenant=tenant,
        workspace=workspace,
        project=project,
        project_name=base.project_name or project,
        prefer_http=False,
        local=False,
        register=bool(base.register),
    )

    target = config_path or try_resolve_config_path() or (Path.home() / ".agentcore" / "connect.yaml")
    written = write_or_merge_connect_yaml(settings, path=target, prefer_http=False)
    print(f"   {ui.ok('✔')} wrote {written}")
    print(f"   {ui.ok('✔')} SSH key {result.private_path} (BatchMode ready)")
    return settings


def ensure_ssh_ready(
    settings: ConnectSettings,
    *,
    force_edit: bool = False,
    allow_wizard: bool = True,
    config_path: Path | None = None,
    project_dir: Path | None = None,
    ssh_override: str = "",
) -> ConnectSettings:
    """Run wizard when forced, missing SSH, or BatchMode probe fails (TTY only)."""
    if settings.local:
        return settings

    http_ready = bool(settings.prefer_http and settings.mcp_http_url and settings.api_token)
    if force_edit:
        if not allow_wizard:
            raise SystemExit("error: --edit requires an interactive TTY")
        return run_ssh_connect_wizard(
            existing=settings,
            rotate=True,
            config_path=config_path,
            project_dir=project_dir,
            ssh_override=ssh_override or settings.ssh,
        )

    # Prefer HTTP when fully ready; skip SSH wizard unless SSH is the only path.
    if http_ready and not settings.ssh:
        return settings

    if not settings.ssh:
        if not allow_wizard:
            raise SystemExit(
                "error: no server.ssh in connect config; run `agentcore connect` in a TTY "
                "or set server.ssh / auth.ssh_key in ~/.agentcore/connect.yaml"
            )
        return run_ssh_connect_wizard(
            existing=settings,
            rotate=False,
            config_path=config_path,
            project_dir=project_dir,
            ssh_override=ssh_override,
        )

    if http_ready:
        return settings

    identity = Path(settings.ssh_identity).expanduser() if settings.ssh_identity else default_identity_path()
    if probe_batch_mode(settings.ssh, identity):
        if not settings.ssh_identity:
            return replace(settings, ssh_identity=str(identity))
        return settings

    if not allow_wizard or not sys.stdin.isatty():
        raise SystemExit(
            f"error: SSH key login failed for {settings.ssh} (BatchMode). "
            "Hand-editing server.ssh / auth.ssh_key requires a working key. "
            "Run `agentcore connect --edit` to re-auth and replace the AgentCore pubkey."
        )

    print(
        f"   {ui.warn('!')} SSH BatchMode failed for {settings.ssh}; "
        "starting interactive key setup",
        file=sys.stderr,
    )
    return run_ssh_connect_wizard(
        existing=settings,
        rotate=True,
        config_path=config_path,
        project_dir=project_dir,
        ssh_override=ssh_override or settings.ssh,
    )
