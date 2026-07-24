"""`agentcore connect` — one-command coding-agent onboarding."""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

from agentcore_cli.connect_config import (
    ConnectSettings,
    default_connect_yaml_path,
    load_connect_settings,
    try_resolve_config_path,
    write_connect_template,
    write_or_merge_connect_yaml,
)
from agentcore_cli.connect_flow import run_connect
from agentcore_cli.connect_wizard import ensure_ssh_ready, run_ssh_connect_wizard


def parse_connect_project_dirs(
    raw: str,
    *,
    cwd: Path | None = None,
) -> list[Path]:
    """Parse comma-separated project directories (default: cwd)."""
    work = (cwd or Path.cwd()).resolve()
    text = (raw or "").strip()
    if not text:
        return [work]
    out: list[Path] = []
    seen: set[str] = set()
    for part in text.split(","):
        piece = part.strip()
        if not piece:
            continue
        path = Path(piece).expanduser().resolve()
        if not path.is_dir():
            raise SystemExit(f"error: connect path is not a directory: {path}")
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        out.append(path)
    if not out:
        raise SystemExit("error: no connect paths given (use cwd or PATH[,PATH…])")
    return out


def _parse_connect_target(raw: str) -> tuple[str, str]:
    """Return (mode, path_spec). mode is edit|init|'' ; path_spec is comma paths or ''."""
    text = (raw or "").strip()
    if not text:
        return "", ""
    lower = text.lower()
    if lower in {"edit", "init"}:
        return lower, ""
    if "," in text or "/" in text or text.startswith(".") or text.startswith("~"):
        return "", text
    # Bare token that is not edit/init — treat as a single relative/absolute path name.
    return "", text


def _settings_for_local(args: argparse.Namespace, *, work: Path) -> ConnectSettings:
    """Same-host connect: scope from flags → identity/env/connect.yaml (not hardcoded dogfood)."""
    from agentcore_cli.cli_defaults import resolve_operator_scope

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
        usage_profile=str(getattr(args, "usage_profile", "") or "").strip(),
        clients=str(args.clients or "all"),
        include_user_clients=bool(args.include_user_clients),
        register=True,
        smoke_test=False,
        ingest_mode="off",
        source_server_path=str(work),
        prefer_http=False,
    )


def _ensure_usage_profile(
    settings: ConnectSettings,
    args: argparse.Namespace,
    *,
    allow_prompt: bool,
) -> ConnectSettings:
    """Usage Profile is selected at connect time — never baked in at client install."""
    override = str(getattr(args, "usage_profile", "") or "").strip()
    if override:
        return replace(settings, usage_profile=override)
    if (settings.usage_profile or "").strip():
        return settings
    if allow_prompt and sys.stdin.isatty() and sys.stdout.isatty():
        from agentcore_cli.connect_wizard import prompt_usage_profile

        return replace(settings, usage_profile=prompt_usage_profile())
    raise SystemExit(
        "error: Usage Profile required at connect "
        "(pass --usage-profile ID, or run interactively to choose)"
    )


def _config_path_from_args(args: argparse.Namespace, *, project_dir: Path) -> Path | None:
    explicit = str(args.config or "").strip()
    if explicit:
        return Path(explicit).expanduser()
    return try_resolve_config_path(project_root=project_dir)


def _pin_software_paths(settings: ConnectSettings, roots: list[Path]) -> None:
    """Remember connected project dirs so later ``agentcore sync`` uses them."""
    from agentcore_cli.software_paths import normalize_software_paths, peek_software_paths, persist_software_paths

    merged = normalize_software_paths(
        [*peek_software_paths(), *[str(p) for p in roots]],
        must_exist=True,
    )
    persist_software_paths(
        merged,
        tenant=settings.tenant,
        workspace=settings.workspace,
        project=settings.project,
        display_name=settings.project_name or settings.project,
    )


def _connect_one(
    args: argparse.Namespace,
    *,
    work: Path,
    shared: ConnectSettings | None,
    force_edit: bool,
) -> tuple[int, ConnectSettings]:
    """Connect a single project directory. Reuse *shared* SSH settings when provided."""
    project_override = str(args.project or "").strip()
    project_id = project_override or work.name or "project"

    if args.local and not args.config:
        settings = _settings_for_local(args, work=work)
        if not project_override:
            settings = replace(settings, project=project_id, project_name=project_id)
        settings = replace(settings, source_server_path=str(work))
        settings = _ensure_usage_profile(
            settings, args, allow_prompt=not bool(args.dry_run)
        )
        code = run_connect(settings, project_dir=work, dry_run=bool(args.dry_run))
        return code, settings

    cfg = _config_path_from_args(args, project_dir=work)
    yaml_path = default_connect_yaml_path(work)

    if shared is not None:
        settings = replace(
            shared,
            project=project_id,
            project_name=project_override or shared.project_name or project_id,
            source_server_path=str(work),
        )
        if args.include_user_clients:
            settings = replace(settings, include_user_clients=True)
        settings = _ensure_usage_profile(
            settings, args, allow_prompt=not bool(args.dry_run)
        )
        if not bool(args.dry_run):
            write_or_merge_connect_yaml(settings, path=yaml_path, prefer_http=settings.prefer_http)
        code = run_connect(settings, project_dir=work, dry_run=bool(args.dry_run))
        return code, settings

    if cfg is None and not args.local:
        existing = ConnectSettings(
            project=project_id,
            project_name=project_id,
            clients=str(args.clients or "all"),
            include_user_clients=bool(args.include_user_clients),
            tenant=str(args.tenant or "default"),
            workspace=str(args.workspace or "default"),
            usage_profile=str(getattr(args, "usage_profile", "") or "").strip(),
            prefer_http=False,
            source_server_path=str(work),
        )
        settings = run_ssh_connect_wizard(
            existing=existing,
            rotate=force_edit,
            config_path=yaml_path,
            project_dir=work,
            ssh_override=str(args.ssh or ""),
        )
        if args.include_user_clients:
            settings = replace(settings, include_user_clients=True)
        settings = replace(settings, source_server_path=settings.source_server_path or str(work))
        settings = _ensure_usage_profile(
            settings, args, allow_prompt=not bool(args.dry_run)
        )
        code = run_connect(settings, project_dir=work, dry_run=bool(args.dry_run))
        return code, settings

    settings = load_connect_settings(
        config_path=str(args.config or "") or (str(cfg) if cfg else ""),
        project_override=project_override,
        ssh_override=str(args.ssh or ""),
        api_url_override=str(args.server or ""),
        clients_override=str(args.clients or ""),
        cwd=work,
        allow_incomplete=force_edit,
        project_root=work,
    )
    if args.local:
        settings = replace(settings, local=True, prefer_http=False)
        if not settings.source_server_path:
            settings = replace(settings, source_server_path=str(work))
    if args.include_user_clients:
        settings = replace(settings, include_user_clients=True)
    if args.tenant:
        settings = replace(settings, tenant=str(args.tenant))
    if args.workspace:
        settings = replace(settings, workspace=str(args.workspace))
    if not settings.source_server_path:
        settings = replace(settings, source_server_path=str(work))

    if not settings.local:
        settings = ensure_ssh_ready(
            settings,
            force_edit=force_edit,
            allow_wizard=not bool(args.dry_run),
            config_path=cfg or yaml_path,
            project_dir=work,
            ssh_override=str(args.ssh or ""),
        )

    settings = _ensure_usage_profile(
        settings, args, allow_prompt=not bool(args.dry_run)
    )
    code = run_connect(settings, project_dir=work, dry_run=bool(args.dry_run))
    return code, settings


def cmd_connect(args: argparse.Namespace) -> int:
    mode, path_spec = _parse_connect_target(str(getattr(args, "connect_mode", "") or ""))
    if mode == "init":
        path = write_connect_template(default_connect_yaml_path(Path.cwd()))
        print(f"wrote {path}")
        print("Edit connect.yaml (local / ssh / http), then run: agentcore connect")
        return 0

    cwd = Path.cwd()
    roots = parse_connect_project_dirs(path_spec, cwd=cwd)
    force_edit = mode == "edit"

    if force_edit and len(roots) > 1:
        raise SystemExit("error: connect edit applies to one project dir (omit PATH[,PATH…] or pass a single path)")

    shared: ConnectSettings | None = None
    last_code = 0
    for index, work in enumerate(roots):
        if len(roots) > 1:
            print(f"\n=== connect {index + 1}/{len(roots)}: {work} ===\n")
        code, settings = _connect_one(
            args,
            work=work,
            shared=shared,
            force_edit=force_edit,
        )
        if code != 0:
            last_code = code
            break
        if index == 0 and len(roots) > 1 and not settings.local:
            shared = settings
        last_code = code

    if last_code == 0 and not bool(args.dry_run):
        # Pin all connected dirs for sync (cwd alone, or every comma-separated path).
        try:
            _pin_software_paths(settings, roots)
        except SystemExit:
            raise
        except Exception as exc:  # noqa: BLE001 — pin is best-effort after successful connect
            print(f"warning: could not pin software paths for sync: {exc}", flush=True)

    return last_code
