"""Interactive first-time / edit onboarding for `agentcore connect` (HTTPS)."""

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


PromptFn = Callable[[str], str]
PasswordFn = Callable[[str], str]


def _require_tty() -> None:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise SystemExit(
            "error: interactive HTTPS setup needs a TTY; "
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
    """Resolve Usage Profile id from catalog. Single catalog entry is auto-selected."""
    from usage_profile import list_profile_ids, load_usage_profile

    ids = list(list_profile_ids())
    if not ids:
        raise SystemExit("error: no Usage Profiles installed (usage_profile catalog empty)")
    if len(ids) == 1:
        only = ids[0]
        print(f"   {ui.ok('✔')} Usage Profile: {only}")
        return only
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


def run_https_connect_wizard(
    *,
    existing: ConnectSettings | None = None,
    config_path: Path | None = None,
    project_dir: Path | None = None,
    url_override: str = "",
    input_fn: PromptFn = input,
    password_fn: PasswordFn = getpass.getpass,
) -> ConnectSettings:
    """Prompt for HTTPS URL + bootstrap secret; merge connect.yaml, return settings.

    The actual bootstrap HTTP call (mint the long-lived access token, register
    the project) happens later in ``run_connect`` — this wizard only collects
    the inputs and writes them to ``connect.yaml``.
    """
    _require_tty()
    work = project_dir or Path.cwd()
    base = existing or ConnectSettings()

    ui.blank()
    ui.heading("HTTPS connect setup")
    ui.blank()
    ui.bullet("Bootstrap secret authenticates the first connect only; it is never saved.")
    ui.bullet("Usage Profile defaults to the sole shipped catalog entry when only one exists.")
    ui.blank()

    url = _prompt_line(
        "AgentCore server URL (https://…)",
        default=url_override or base.api_url,
        input_fn=input_fn,
    ).rstrip("/")
    if not url:
        raise SystemExit("error: server URL is required")
    if url.split("://", 1)[0].lower() != "https":
        raise SystemExit(f"error: HTTPS connect requires an https:// URL, got {url!r}")

    tenant = _prompt_line("Tenant", default=base.tenant or "default", input_fn=input_fn)
    workspace = _prompt_line("Workspace", default=base.workspace or "default", input_fn=input_fn)
    usage_profile = (base.usage_profile or "").strip() or prompt_usage_profile(
        default=(base.usage_profile or "").strip(),
        input_fn=input_fn,
    )
    project = base.project or work.name or "project"
    secret = password_fn(f"Bootstrap secret for {url} (blank if none configured): ")

    settings = replace(
        base,
        api_url=url,
        tenant=tenant,
        workspace=workspace,
        project=project,
        project_name=base.project_name or project,
        usage_profile=usage_profile,
        prefer_http=True,
        local=False,
        register=True,
        bootstrap_secret=secret,
    )
    secret = ""

    target = config_path or try_resolve_config_path() or default_connect_yaml_path()
    written = write_or_merge_connect_yaml(settings, path=target, prefer_http=True)
    print(f"   {ui.ok('✔')} wrote {written}")
    print(f"   {ui.ok('✔')} HTTPS target {settings.api_url}")
    return settings
