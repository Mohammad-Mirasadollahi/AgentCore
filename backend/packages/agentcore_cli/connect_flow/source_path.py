"""Shared SSH discovery for ``source.server_path``.

Module contract:
- Role: resolve on-server software path for connect ingest and client remote sync.
- SoT / invariants: one probe order for connect and sync; never invent AgentCore
  identity pins as a silent fallback; when no candidate exists, stage the client
  checkout to ``<install>-data/sources/<project>`` via rsync; persist only via
  callers that merge yaml.
- Failures: stage/rsync failure fails closed; configured path that is not a remote
  dir fails closed. Never prompt on TTY.
"""

from __future__ import annotations

import shlex
import shutil
import subprocess
from dataclasses import replace
from pathlib import Path

from agentcore_cli.connect_config import ConnectSettings
from agentcore_cli.data_root import (
    LEGACY_STAGED_SOURCES_ROOT,
    is_staged_source_path as data_is_staged_source_path,
    staged_source_path_for_project,
)

# Keep the staged mirror lean; graph sync still applies its own excludes server-side.
STAGE_RSYNC_EXCLUDES: tuple[str, ...] = (
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    ".next",
    "dist",
    "build",
    "vcp_images_dump",
)


def staged_source_path(project_name: str, *, remote_root: str = "", data_root: str = "") -> str:
    """Canonical auto-stage destination on the AgentCore host."""
    root = (remote_root or "").strip().rstrip("/\\")
    explicit = (data_root or "").strip().rstrip("/\\")
    if explicit:
        name = (project_name or "").strip().strip("/\\")
        if not name or "/" in name or "\\" in name or name in (".", ".."):
            raise SystemExit(
                "error: cannot stage source without a simple project name "
                f"(got {project_name!r})"
            )
        return f"{explicit}/sources/{name}"
    # When staging onto a remote install, ignore the client's AGENTCORE_DATA_ROOT.
    environ: dict[str, str] | None = {} if root else None
    return staged_source_path_for_project(
        project_name,
        install_root=root or None,
        environ=environ,
    )


def is_staged_source_path(path: str, *, remote_root: str = "", data_root: str = "") -> bool:
    """True when *path* is under the auto-stage root (or legacy /var/lib path)."""
    root = (remote_root or "").strip().rstrip("/\\")
    explicit = (data_root or "").strip().rstrip("/\\")
    extra: list[str] = []
    if explicit:
        extra.append(f"{explicit}/sources")
    environ: dict[str, str] | None = {} if root else None
    return data_is_staged_source_path(
        path,
        install_root=root or None,
        environ=environ,
        extra_roots=extra,
    )


def refresh_staged_checkout(
    settings: ConnectSettings,
    work: Path,
    *,
    server_path: str = "",
) -> None:
    """Re-rsync the client checkout when ``source.server_path`` is a staged mirror."""
    from agentcore_cli import ui
    from agentcore_cli.data_root import discover_remote_data_root

    dest = (server_path or settings.source_server_path or "").strip()
    remote_root = settings.remote_root or ""
    data_root = discover_remote_data_root(settings, remote_root) or ""
    if not is_staged_source_path(dest, remote_root=remote_root, data_root=data_root):
        return
    print(f"   {ui.warn('…')} refreshing staged source → {dest} (rsync)")
    stage_local_checkout(settings, work, dest)


def source_path_for_connect(*, local: bool, work: Path, configured: str = "") -> str:
    """Ingest path: same-host cwd is fine; remote SSH needs an on-server path (or empty).

    ``source.server_path`` must exist on the AgentCore host (NFS/clone/staged), not a
    blind copy of the laptop checkout path. Only dogfood ``--local`` may default to cwd.
    Remote SSH fills this via ``ensure_remote_source_path`` (SSH probe + optional stage).
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
    data_root: str = "",
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
        if root or data_root:
            add(staged_source_path(name, remote_root=root, data_root=data_root))
        add(f"{LEGACY_STAGED_SOURCES_ROOT}/{name}")
    return out


def _rsync_ssh_e(settings: ConnectSettings) -> str:
    """Shell-safe ``rsync -e`` value using the same SSH options as connect probes."""
    parts = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=30"]
    identity = (settings.ssh_identity or "").strip()
    if identity:
        parts.extend(
            [
                "-i",
                str(Path(identity).expanduser()),
                "-o",
                "IdentitiesOnly=yes",
            ]
        )
    return " ".join(shlex.quote(p) for p in parts)


def stage_local_checkout(
    settings: ConnectSettings,
    work: Path,
    remote_dest: str,
) -> None:
    """Rsync the client checkout to *remote_dest* on the AgentCore host."""
    from agentcore_cli.connect_flow.ssh import run_ssh

    if not (settings.ssh or "").strip():
        raise SystemExit("error: cannot stage source without server.ssh")
    if shutil.which("rsync") is None:
        raise SystemExit(
            "error: rsync is required to stage the client checkout onto the AgentCore server"
        )
    dest = (remote_dest or "").strip().rstrip("/")
    if not dest:
        raise SystemExit("error: empty stage destination on AgentCore server")
    if run_ssh(settings, ["mkdir", "-p", dest], connect_timeout=30) != 0:
        raise SystemExit(f"error: could not create {dest} on the AgentCore server")

    local = f"{work.resolve()}/"
    remote = f"{settings.ssh}:{dest}/"
    cmd = ["rsync", "-az", "--delete", "-e", _rsync_ssh_e(settings)]
    for pattern in STAGE_RSYNC_EXCLUDES:
        cmd.extend(["--exclude", pattern])
    cmd.extend([local, remote])
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise SystemExit(
            f"error: rsync to {dest} on the AgentCore server failed "
            f"(exit {result.returncode})"
        )


def ensure_remote_source_path(
    settings: ConnectSettings,
    work: Path,
    *,
    allow_prompt: bool = False,
    input_fn=input,
) -> ConnectSettings:
    """Set ``source.server_path`` via SSH discovery (no operator prompt).

    Order: configured path → probe candidates → auto-stage to
    ``<remote_root parent>/<name>-data/sources/<project>``. Fail closed only when
    stage also fails.
    """
    del allow_prompt, input_fn  # kept for call-site compatibility; never prompt
    from agentcore_cli import ui
    from agentcore_cli.connect_flow.ssh import missing_server_source_message, remote_is_dir
    from agentcore_cli.data_root import discover_remote_data_root
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

    data_root = discover_remote_data_root(resolved, remote_root) or ""
    project_name = (resolved.project or work.name or "").strip()
    candidates = remote_source_candidates(
        work,
        remote_root=remote_root,
        project_name=project_name,
        data_root=data_root,
    )
    for candidate in candidates:
        if remote_is_dir(resolved, candidate):
            print(f"   {ui.ok('✔')} source.server_path on server: {candidate}")
            return replace(resolved, source_server_path=candidate)

    dest = staged_source_path(
        project_name or work.name,
        remote_root=remote_root,
        data_root=data_root,
    )
    print(f"   {ui.warn('…')} staging client checkout → {dest} on server (rsync)")
    stage_local_checkout(resolved, work, dest)
    if remote_is_dir(resolved, dest):
        print(f"   {ui.ok('✔')} source.server_path on server: {dest}")
        return replace(resolved, source_server_path=dest)

    tried = ", ".join(candidates) if candidates else "(none)"
    raise SystemExit(
        "error: could not auto-discover or stage source.server_path on the AgentCore "
        f"server (client checkout {work.resolve()}).\n"
        f"  Probed via SSH: {tried}\n"
        f"  Stage target: {dest}\n"
        "  Fix SSH/rsync access, then re-run `agentcore connect` or `agentcore sync`."
    )


# Compat aliases for connect.py / older tests.
_source_path_for_connect = source_path_for_connect
_remote_source_candidates = remote_source_candidates
_ensure_remote_source_path = ensure_remote_source_path
