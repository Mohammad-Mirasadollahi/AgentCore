"""PATH install command."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from agentcore_cli.util import print_json, repo_root


def cmd_path_install(args: argparse.Namespace) -> int:
    """Ensure agentcore is available on PATH via ~/.local/bin symlink."""
    root = repo_root()
    venv_dir = os.environ.get("AGENTCORE_VENV_DIR", ".venv")
    source = root / venv_dir / "bin" / "agentcore"
    if not source.is_file():
        raise SystemExit(
            f"error: {venv_dir}/bin/agentcore missing; run: bash scripts/ensure-venv.sh"
        )
    local_bin = Path(os.path.expanduser("~")) / ".local" / "bin"
    target = local_bin / "agentcore"
    symlink_error: str | None = None
    try:
        local_bin.mkdir(parents=True, exist_ok=True)
        if target.is_symlink() or target.exists():
            target.unlink()
        target.symlink_to(source)
    except OSError as exc:  # sandbox / read-only home
        symlink_error = str(exc)
    on_path = str(local_bin) in os.environ.get("PATH", "").split(os.pathsep)
    if symlink_error is None and on_path:
        hint = None
    elif symlink_error is not None:
        hint = f"venv CLI ready at {source}; PATH symlink skipped ({symlink_error})"
    else:
        hint = f'Add to PATH: export PATH="{local_bin}:$PATH"  (ensure-venv can append this for you)'
    payload: dict = {
        "symlink": str(target),
        "points_to": str(source),
        "local_bin_on_path": on_path,
        "symlink_ok": symlink_error is None,
        "hint": hint,
    }
    if symlink_error is not None:
        payload["symlink_error"] = symlink_error
    print_json(payload)
    # Always append when --shell-rc is set. Do not gate on process PATH:
    # install.sh exports ~/.local/bin temporarily, which would skip the rc update
    # and leave new shells without agentcore.
    if args.shell_rc and symlink_error is None:
        try:
            _ensure_path_export(Path(os.path.expanduser("~")) / args.shell_rc, local_bin)
        except OSError as exc:
            print(f"warning: could not update shell rc: {exc}")
    # Venv binary is enough for local use; PATH symlink is best-effort.
    return 0


def _ensure_path_export(rc_file: Path, local_bin: Path) -> None:
    line = f'export PATH="{local_bin}:$PATH"  # AgentCore CLI'
    marker = "# AgentCore CLI"
    existing = rc_file.read_text(encoding="utf-8") if rc_file.is_file() else ""
    if marker in existing:
        print(f"PATH export already present in {rc_file}")
        return
    with rc_file.open("a", encoding="utf-8") as handle:
        handle.write(f"\n{line}\n")
    print(f"appended PATH export to {rc_file}")
