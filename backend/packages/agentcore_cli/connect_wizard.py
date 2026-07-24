"""Interactive first-time / edit SSH onboarding for `agentcore connect`."""

from __future__ import annotations

import getpass
import sys
from dataclasses import replace
from pathlib import Path
from typing import Callable

from agentcore_cli import ui
from agentcore_cli.connect_config import (
    ConnectSettings,
    default_connect_yaml_path,
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
            "create .agentcore/connect.yaml (agentcore connect init) "
            "or run from a terminal: agentcore connect / agentcore connect edit"
        )


def _prompt_line(prompt: str, *, default: str = "", input_fn: PromptFn = input) -> str:
    suffix = f" [{default}]" if default else ""
    raw = input_fn(f"{prompt}{suffix}: ").strip()
    return raw or default


def prompt_usage_profile(
    *,
    default: str = "",
    input_fn: PromptFn = input,
) -> str:
    """Ask for a Usage Profile id (catalog). Empty default — chosen at connect, not install."""
    from usage_profile import list_profile_ids, load_usage_profile

    ids = list(list_profile_ids())
    if not ids:
        raise SystemExit("error: no Usage Profiles installed (usage_profile catalog empty)")
    ui.blank()
    print("   Usage Profiles (choose at connect — not set during client install):")
    for index, profile_id in enumerate(ids, start=1):
        try:
            title = str(load_usage_profile(profile_id).get("title") or "")
        except Exception:  # noqa: BLE001 — listing must not fail on one bad profile
            title = ""
        label = f"{profile_id}" + (f" — {title}" if title else "")
        mark = " *" if profile_id == default else ""
        print(f"     {index}) {label}{mark}")
    ui.blank()
    hint = default if default in ids else ""
    while True:
        raw = _prompt_line("Usage Profile id or number", default=hint, input_fn=input_fn).strip()
        if not raw:
            raise SystemExit(
                "error: Usage Profile is required at connect "
                "(pass --usage-profile or choose interactively)"
            )
        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= len(ids):
                return ids[idx - 1]
            print(f"   {ui.warn('!')} enter 1–{len(ids)} or a profile id")
            continue
        if raw in ids:
            return raw
        print(f"   {ui.warn('!')} unknown profile {raw!r}; pick from the list")


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
    ui.bullet("Remote AgentCore root is auto-discovered from install-root markers after SSH.")
    ui.bullet("Usage Profile is chosen here at connect (not during client install).")
    ui.bullet("Hand-edit .agentcore/connect.yaml for scope/clients; use connect edit to change SSH identity.")
    ui.blank()

    override_user, override_host = parse_ssh_target(ssh_override)
    cur_user, cur_host = parse_ssh_target(base.ssh)
    host_default = override_host or cur_host
    user_default = override_user or cur_user or getpass.getuser() or "ops"

    host = _prompt_line("Server host", default=host_default, input_fn=input_fn)
    user = _prompt_line("SSH username", default=user_default, input_fn=input_fn)
    ssh_target = format_ssh_target(user, host)

    tenant = _prompt_line("Tenant", default=base.tenant or "default", input_fn=input_fn)
    workspace = _prompt_line("Workspace", default=base.workspace or "default", input_fn=input_fn)
    usage_profile = prompt_usage_profile(
        default=(base.usage_profile or "").strip(),
        input_fn=input_fn,
    )
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

    print(f"   {ui.warn('…')} discovering AgentCore remote root (install-root marker)")
    from agentcore_cli.install_root_marker import discover_remote_install_root

    discovered = discover_remote_install_root(
        ssh_target,
        identity_file=result.private_path,
    )
    if discovered is not None:
        remote_root = str(discovered)
        print(f"   {ui.ok('✔')} remote root {remote_root}")
    else:
        raise SystemExit(
            "error: could not discover AgentCore remote root (no install-root marker).\n"
            "  On the server: finish install so markers are stamped "
            "(.agentcore/install-root), then retry connect.\n"
            "  Or set server.remote_root in .agentcore/connect.yaml and re-run "
            "after markers exist (connect does not prompt for this path)."
        )

    settings = replace(
        base,
        ssh=ssh_target,
        remote_root=remote_root.rstrip("/\\") or "/opt/AgentCore",
        ssh_identity=str(result.private_path),
        tenant=tenant,
        workspace=workspace,
        project=project,
        project_name=base.project_name or project,
        usage_profile=usage_profile,
        prefer_http=False,
        local=False,
        register=bool(base.register),
    )

    target = config_path or try_resolve_config_path() or default_connect_yaml_path()
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
            raise SystemExit("error: connect edit requires an interactive TTY")
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
                "or set server.ssh / auth.ssh_key in .agentcore/connect.yaml"
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
            "Run `agentcore connect edit` to re-auth and replace the AgentCore pubkey."
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
