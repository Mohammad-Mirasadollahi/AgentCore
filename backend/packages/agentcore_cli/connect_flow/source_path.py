"""Shared SSH discovery for ``source.server_path``.

Module contract:
- Role: resolve on-server software path for connect ingest and client remote sync.
- SoT / invariants: one probe order for connect and sync; never invent AgentCore
  identity pins as a silent fallback; persist only via callers that merge yaml.
- Failures: missing tree on server fails closed with probed list; configured path
  that is not a remote dir fails closed. Never prompt on TTY.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from agentcore_cli.connect_config import ConnectSettings


def source_path_for_connect(*, local: bool, work: Path, configured: str = "") -> str:
    """Ingest path: same-host cwd is fine; remote SSH needs an on-server path (or empty).

    ``source.server_path`` must exist on the AgentCore host (NFS/clone), not a blind
    copy of the laptop checkout path. Only dogfood ``--local`` may default to cwd.
    Remote SSH fills this via ``ensure_remote_source_path`` (SSH probe candidates).
    """
    text = (configured or "").strip()
    if text:
        return text
    if local:
        return str(work)
    return ""


def remote_source_candidates(
    work: Path,
    *,
    remote_root: str = "",
    project_name: str = "",
) -> list[str]:
    """Ordered absolute paths to probe on the AgentCore host for software ingest."""
    from agentcore_cli.install_root_marker import looks_like_agentcore_root

    name = (project_name or work.name or "").strip()
    out: list[str] = []
    seen: set[str] = set()

    def add(raw: str) -> None:
        path = (raw or "").strip().rstrip("/\\")
        if not path or path in seen:
            return
        seen.add(path)
        out.append(path)

    add(str(work.resolve()))
    root = (remote_root or "").strip().rstrip("/\\")
    if root:
        if looks_like_agentcore_root(work) or (name and Path(root).name == name):
            add(root)
        if name:
            add(str(Path(root).parent / name))
    if name:
        add(f"/opt/{name}")
        add(f"/srv/repos/{name}")
        add(f"/var/lib/agentcore/sources/{name}")
    return out


def ensure_remote_source_path(
    settings: ConnectSettings,
    work: Path,
    *,
    allow_prompt: bool = False,
    input_fn=input,
) -> ConnectSettings:
    """Set ``source.server_path`` via SSH discovery (no operator prompt).

    Order: configured path → probe candidates (client path, AgentCore remote_root when
    dogfooding, ``/opt/<project>``, …). Fail closed with the probed list when nothing
    exists on the server.
    """
    del allow_prompt, input_fn  # kept for call-site compatibility; never prompt
    from agentcore_cli import ui
    from agentcore_cli.connect_flow.ssh import missing_server_source_message, remote_is_dir
    from agentcore_cli.install_root_marker import discover_remote_install_root

    if settings.local:
        path = (settings.source_server_path or "").strip() or str(work.resolve())
        return replace(settings, source_server_path=path)

    configured = (settings.source_server_path or "").strip()
    if configured:
        if settings.ssh and not remote_is_dir(settings, configured):
            raise SystemExit(f"error: {missing_server_source_message(configured)}")
        return settings

    if not settings.ssh:
        return settings

    resolved = settings
    remote_root = (resolved.remote_root or "").strip().rstrip("/\\")
    if not remote_root or remote_root == "/opt/AgentCore":
        discovered = discover_remote_install_root(
            resolved.ssh,
            identity_file=resolved.ssh_identity or None,
        )
        if discovered is not None:
            remote_root = str(discovered)
            resolved = replace(resolved, remote_root=remote_root)

    candidates = remote_source_candidates(
        work,
        remote_root=remote_root,
        project_name=(resolved.project or work.name or ""),
    )
    for candidate in candidates:
        if remote_is_dir(resolved, candidate):
            print(f"   {ui.ok('✔')} source.server_path on server: {candidate}")
            return replace(resolved, source_server_path=candidate)

    tried = ", ".join(candidates) if candidates else "(none)"
    raise SystemExit(
        "error: could not auto-discover source.server_path on the AgentCore server "
        f"(client checkout {work.resolve()}).\n"
        f"  Probed via SSH: {tried}\n"
        "  Put a copy of this software on the server (clone/rsync/NFS), then re-run "
        "`agentcore connect` or `agentcore sync`, or set source.server_path in "
        ".agentcore/connect.yaml."
    )


# Compat aliases for connect.py / older tests.
_source_path_for_connect = source_path_for_connect
_remote_source_candidates = remote_source_candidates
_ensure_remote_source_path = ensure_remote_source_path
