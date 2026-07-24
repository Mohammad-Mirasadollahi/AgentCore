"""Well-known AgentCore install-root markers (no-root-required discovery).

Role: stamp the absolute AgentCore checkout path after install/first run, and
discover it over SSH for ``agentcore connect`` without asking the operator.
Source of truth: plain-text ``install-root`` files (one absolute path per line).
Allowed: user-home + in-tree markers (mode 0644); SUDO_USER home when install
ran via sudo. Forbidden: world-writable temp paths; treating unvalidated paths
as AgentCore roots; requiring root to read markers.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

MARKER_NAME = "install-root"
_ABS_PATH_RE = re.compile(r"^(/|[A-Za-z]:[\\/]).+")


def looks_like_agentcore_root(root: Path) -> bool:
    """True when *root* looks like an AgentCore checkout (readable without root)."""
    try:
        path = root.expanduser().resolve()
    except OSError:
        return False
    if not path.is_dir():
        return False
    if (path / ".venv" / "bin" / "agentcore").is_file():
        return True
    if (path / ".venv" / "Scripts" / "agentcore.exe").is_file():
        return True
    pyproject = path / "pyproject.toml"
    if pyproject.is_file():
        try:
            text = pyproject.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            text = ""
        if 'name = "agentcore"' in text or "name='agentcore'" in text:
            return True
    return (path / "backend" / "packages" / "agentcore_cli").is_dir()


def marker_path_in_tree(root: Path) -> Path:
    return root.expanduser().resolve() / ".agentcore" / MARKER_NAME


def marker_path_in_home(home: Path | None = None) -> Path:
    base = (home or Path.home()).expanduser()
    return base / ".agentcore" / MARKER_NAME


def marker_path_xdg_state() -> Path | None:
    raw = (os.environ.get("XDG_STATE_HOME") or "").strip()
    if not raw:
        return None
    return Path(raw).expanduser() / "agentcore" / MARKER_NAME


def read_marker_file(path: Path) -> Path | None:
    """Return absolute install root from a marker file, or None if missing/invalid."""
    try:
        if not path.is_file():
            return None
        line = path.read_text(encoding="utf-8").splitlines()[0].strip()
    except OSError:
        return None
    if not line or not _ABS_PATH_RE.match(line):
        return None
    candidate = Path(line).expanduser()
    if looks_like_agentcore_root(candidate):
        return candidate.resolve()
    return None


def stamp_install_root(
    root: Path,
    *,
    home: Path | None = None,
    extra_homes: list[Path] | None = None,
) -> list[Path]:
    """Write install-root markers; return paths successfully written.

    Always stamps ``<root>/.agentcore/install-root`` (mode 0644 when possible) so
    non-root SSH users can read an install under ``/opt/...``. Also stamps the
    current user home (and optional extra homes such as ``SUDO_USER``).
    """
    resolved = root.expanduser().resolve()
    if not looks_like_agentcore_root(resolved):
        raise ValueError(f"not an AgentCore root: {resolved}")
    payload = f"{resolved}\n"
    targets: list[Path] = [marker_path_in_tree(resolved), marker_path_in_home(home)]
    xdg = marker_path_xdg_state()
    if xdg is not None:
        targets.append(xdg)
    for extra in extra_homes or []:
        targets.append(marker_path_in_home(extra))

    written: list[Path] = []
    seen: set[Path] = set()
    for target in targets:
        key = target.expanduser()
        if key in seen:
            continue
        seen.add(key)
        try:
            key.parent.mkdir(parents=True, exist_ok=True)
            key.write_text(payload, encoding="utf-8")
            try:
                key.chmod(0o644)
            except OSError:
                pass
            # Tree .agentcore should be traversable by the SSH login user.
            if key.parent.name == ".agentcore":
                try:
                    key.parent.chmod(0o755)
                except OSError:
                    pass
            written.append(key)
        except OSError:
            continue
    return written


def sudo_user_home() -> Path | None:
    """Home directory for ``SUDO_USER`` when install ran under sudo (best effort)."""
    user = (os.environ.get("SUDO_USER") or "").strip()
    if not user or user == "root":
        return None
    try:
        import pwd

        return Path(pwd.getpwnam(user).pw_dir)
    except (ImportError, KeyError, OSError):
        return None


def stamp_install_root_from_env(root: Path | None = None) -> list[Path]:
    """Stamp markers for *root* (or ``AGENTCORE_ROOT`` / cwd checkout)."""
    if root is None:
        env = (os.environ.get("AGENTCORE_ROOT") or "").strip()
        root = Path(env) if env else Path.cwd()
    extras: list[Path] = []
    sudo_home = sudo_user_home()
    if sudo_home is not None:
        extras.append(sudo_home)
    return stamp_install_root(root, extra_homes=extras)


_REMOTE_DISCOVER_SCRIPT = r"""
set +e
_try_marker() {
  f="$1"
  [ -f "$f" ] && [ -r "$f" ] || return 1
  p=$(head -n1 "$f" 2>/dev/null | tr -d '\r')
  [ -n "$p" ] || return 1
  if [ -x "$p/.venv/bin/agentcore" ] || [ -f "$p/pyproject.toml" ]; then
    printf '%s\n' "$p"
    return 0
  fi
  return 1
}
for f in \
  "$HOME/.agentcore/install-root" \
  "${XDG_STATE_HOME:-$HOME/.local/state}/agentcore/install-root"
do
  _try_marker "$f" && exit 0
done
if command -v agentcore >/dev/null 2>&1; then
  bin=$(command -v agentcore)
  # shim or venv entry → climb to checkout
  for cand in \
    "$(dirname "$bin")/../.." \
    "$(dirname "$(readlink -f "$bin" 2>/dev/null || echo "$bin")")/../.."
  do
    r=$(cd "$cand" 2>/dev/null && pwd)
    [ -n "$r" ] || continue
    if [ -x "$r/.venv/bin/agentcore" ] || [ -f "$r/pyproject.toml" ]; then
      printf '%s\n' "$r"
      exit 0
    fi
  done
fi
for cand in /opt/AgentCore /usr/local/AgentCore "$HOME/AgentCore" "$HOME/agentcore" "$HOME/opt/AgentCore"; do
  _try_marker "$cand/.agentcore/install-root" && exit 0
  if [ -x "$cand/.venv/bin/agentcore" ]; then
    printf '%s\n' "$cand"
    exit 0
  fi
done
exit 1
"""


def discover_remote_install_root(
    ssh_target: str,
    *,
    identity_file: str | Path | None = None,
    connect_timeout: int = 15,
) -> Path | None:
    """SSH BatchMode: read well-known markers / PATH / common roots on the server."""
    from agentcore_cli.remote_client import ssh_argv

    identity = str(Path(identity_file).expanduser()) if identity_file else None
    remote = ["bash", "-lc", _REMOTE_DISCOVER_SCRIPT.strip()]
    argv = ssh_argv(
        ssh_target,
        remote,
        batch_mode=True,
        connect_timeout=connect_timeout,
        identity_file=identity,
    )
    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=max(connect_timeout + 10, 25),
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    line = (completed.stdout or "").strip().splitlines()
    if not line:
        return None
    candidate = Path(line[0].strip())
    # Remote already validated; still require absolute path shape locally.
    if not _ABS_PATH_RE.match(str(candidate)):
        return None
    return candidate
