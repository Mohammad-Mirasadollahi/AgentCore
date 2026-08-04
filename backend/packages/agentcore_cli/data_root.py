"""Sibling data root for durable AgentCore runtime data.

Module contract:
- Role: resolve and create ``<install>-data`` (or ``AGENTCORE_DATA_ROOT``) layout;
  stamp ``.agentcore/data-root`` for remote discovery; migrate legacy in-tree
  durable dirs once.
- SoT / invariants: durable DB/sources/usage/cache/backup live under data root;
  lightweight ``.agentcore`` identity/upgrade/run stays under the install tree.
- Failures: never invent paths under Docker volume storage; mkdir/stamp/migrate
  are best-effort via ``ensure_data_root``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

DATA_SUBDIRS: tuple[str, ...] = (
    "postgres",
    "neo4j",
    "sources",
    "backup",
    "cache",
    "mcp-usage",
    "sync-usage",
)

# Formerly under ``<install>/.agentcore/`` — moved into the data root.
LEGACY_IN_TREE_SUBDIRS: tuple[str, ...] = (
    "backup",
    "cache",
    "mcp-usage",
    "sync-usage",
)

ENV_DATA_ROOT = "AGENTCORE_DATA_ROOT"
DATA_ROOT_MARKER = "data-root"
LEGACY_STAGED_SOURCES_ROOT = "/var/lib/agentcore/sources"


def default_data_root(install_root: Path | str) -> Path:
    """``/opt/AgentCore`` → ``/opt/AgentCore-data``."""
    root = Path(install_root)
    return root.parent / f"{root.name}-data"


def resolve_data_root(
    *,
    install_root: Path | str | None = None,
    environ: dict[str, str] | None = None,
) -> Path:
    """Prefer ``AGENTCORE_DATA_ROOT``, else marker file, else sibling ``<basename>-data``."""
    env = environ if environ is not None else os.environ
    raw = str(env.get(ENV_DATA_ROOT) or "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    if install_root is None:
        from agentcore_cli.util import repo_root

        install_root = repo_root()
    marked = read_data_root_marker(install_root)
    if marked is not None:
        return marked
    return default_data_root(install_root).resolve()


def data_root_marker_path(install_root: Path | str) -> Path:
    return Path(install_root).expanduser().resolve() / ".agentcore" / DATA_ROOT_MARKER


def read_data_root_marker(install_root: Path | str) -> Path | None:
    path = data_root_marker_path(install_root)
    try:
        if not path.is_file():
            return None
        line = path.read_text(encoding="utf-8").splitlines()[0].strip()
    except OSError:
        return None
    if not line:
        return None
    candidate = Path(line).expanduser()
    try:
        return candidate.resolve()
    except OSError:
        return candidate


def stamp_data_root(install_root: Path | str, data_root: Path | str) -> Path:
    """Write ``<install>/.agentcore/data-root`` (absolute path, mode 0644)."""
    install = Path(install_root).expanduser().resolve()
    payload = f"{Path(data_root).expanduser().resolve()}\n"
    marker = data_root_marker_path(install)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(payload, encoding="utf-8")
    try:
        marker.chmod(0o644)
        marker.parent.chmod(0o755)
    except OSError:
        pass
    return marker


def _dir_nonempty(path: Path) -> bool:
    if not path.is_dir():
        return False
    try:
        next(path.iterdir())
    except StopIteration:
        return False
    except OSError:
        return False
    return True


def migrate_legacy_in_tree_dirs(install_root: Path | str, data_root: Path | str) -> list[str]:
    """Copy nonempty ``.agentcore/{backup,cache,…}`` into data root when dest empty."""
    install = Path(install_root).expanduser().resolve()
    dest_root = Path(data_root).expanduser().resolve()
    moved: list[str] = []
    for name in LEGACY_IN_TREE_SUBDIRS:
        src = install / ".agentcore" / name
        dest = dest_root / name
        if not _dir_nonempty(src):
            continue
        if _dir_nonempty(dest):
            continue
        dest.mkdir(parents=True, exist_ok=True)
        for child in src.iterdir():
            target = dest / child.name
            if target.exists():
                continue
            if child.is_dir():
                shutil.copytree(child, target, dirs_exist_ok=True)
            else:
                shutil.copy2(child, target)
        moved.append(name)
    return moved


def ensure_data_root(
    *,
    install_root: Path | str | None = None,
    environ: dict[str, str] | None = None,
) -> Path:
    """Create data-root subdirs, stamp marker, migrate legacy in-tree dirs."""
    if install_root is None:
        from agentcore_cli.util import repo_root

        install_root = repo_root()
    root = resolve_data_root(install_root=install_root, environ=environ)
    root.mkdir(parents=True, exist_ok=True)
    for name in DATA_SUBDIRS:
        (root / name).mkdir(parents=True, exist_ok=True)
    stamp_data_root(install_root, root)
    migrate_legacy_in_tree_dirs(install_root, root)
    return root


def staged_sources_root(
    install_root: Path | str | None = None,
    *,
    environ: dict[str, str] | None = None,
) -> Path:
    """``…/AgentCore-data/sources`` (stage/rsync target parent)."""
    return resolve_data_root(install_root=install_root, environ=environ) / "sources"


def staged_source_path_for_project(
    project_name: str,
    *,
    install_root: Path | str | None = None,
    environ: dict[str, str] | None = None,
) -> str:
    name = (project_name or "").strip().strip("/\\")
    if not name or "/" in name or "\\" in name or name in (".", ".."):
        raise SystemExit(
            "error: cannot stage source without a simple project name "
            f"(got {project_name!r})"
        )
    return str(staged_sources_root(install_root, environ=environ) / name)


def is_staged_source_path(
    path: str,
    *,
    install_root: Path | str | None = None,
    environ: dict[str, str] | None = None,
    extra_roots: list[str] | None = None,
) -> bool:
    text = (path or "").strip().rstrip("/\\")
    if not text:
        return False
    sources = str(staged_sources_root(install_root, environ=environ)).rstrip("/")
    legacy = LEGACY_STAGED_SOURCES_ROOT.rstrip("/")
    roots = [sources, legacy, *(extra_roots or [])]
    for root in roots:
        root = str(root).rstrip("/")
        if text == root or text.startswith(root + "/"):
            return True
    return False


def postgres_data_dir(
    *,
    install_root: Path | str | None = None,
    environ: dict[str, str] | None = None,
) -> Path:
    return resolve_data_root(install_root=install_root, environ=environ) / "postgres"


def neo4j_data_dir(
    *,
    install_root: Path | str | None = None,
    environ: dict[str, str] | None = None,
) -> Path:
    return resolve_data_root(install_root=install_root, environ=environ) / "neo4j"


def backup_dir(
    *,
    install_root: Path | str | None = None,
    environ: dict[str, str] | None = None,
) -> Path:
    return resolve_data_root(install_root=install_root, environ=environ) / "backup"


def cache_dir(
    *,
    install_root: Path | str | None = None,
    environ: dict[str, str] | None = None,
) -> Path:
    return resolve_data_root(install_root=install_root, environ=environ) / "cache"


def mcp_usage_dir(
    *,
    install_root: Path | str | None = None,
    environ: dict[str, str] | None = None,
) -> Path:
    return resolve_data_root(install_root=install_root, environ=environ) / "mcp-usage"


def sync_usage_dir(
    *,
    install_root: Path | str | None = None,
    environ: dict[str, str] | None = None,
) -> Path:
    return resolve_data_root(install_root=install_root, environ=environ) / "sync-usage"


def discover_remote_data_root(
    settings: object,
    remote_root: str,
) -> str | None:
    """SSH-read ``.agentcore/data-root`` or ``install-state.env`` ``data_root=`` on server."""
    import shlex

    from agentcore_cli.connect_flow.ssh import ssh_command

    root = (remote_root or "").strip().rstrip("/\\")
    if not root or not getattr(settings, "ssh", ""):
        return None
    marker = f"{root}/.agentcore/{DATA_ROOT_MARKER}"
    try:
        result = subprocess.run(
            ssh_command(
                settings,  # type: ignore[arg-type]
                ["bash", "-lc", f"head -n1 {shlex.quote(marker)} 2>/dev/null"],
            ),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        result = None
    if result is not None and result.returncode == 0:
        lines = [ln.strip() for ln in (result.stdout or "").splitlines() if ln.strip()]
        if lines and lines[0].startswith("/"):
            return lines[0].rstrip("/")

    state = f"{root}/.agentcore/install-state.env"
    snippet = (
        f"grep -E '^data_root=' {shlex.quote(state)} 2>/dev/null "
        "| head -n1 | cut -d= -f2-"
    )
    try:
        result = subprocess.run(
            ssh_command(settings, ["bash", "-lc", snippet]),  # type: ignore[arg-type]
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    lines = [ln.strip() for ln in (result.stdout or "").splitlines() if ln.strip()]
    if lines and lines[0].startswith("/"):
        return lines[0].rstrip("/")
    return None
