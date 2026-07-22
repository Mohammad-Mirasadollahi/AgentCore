"""Unit tests for install runtime selection and PATH helpers."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
LIB = ROOT / "scripts" / "install"


def _bash_snippet(snippet: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    full = f"""
set -euo pipefail
export AGENTCORE_ROOT={ROOT.as_posix()!r}
export AGENTCORE_INSTALL_LIB={LIB.as_posix()!r}
source "{LIB.as_posix()}/common.sh"
{snippet}
"""
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        ["bash", "-c", full],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=merged,
    )


def test_normalize_install_runtime_accepts_host_and_docker() -> None:
    proc = _bash_snippet(
        'normalize_install_runtime host; echo; normalize_install_runtime docker; echo; '
        'normalize_install_runtime weird || echo bad'
    )
    assert proc.returncode == 0, proc.stderr
    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    assert lines[:2] == ["host", "docker"]
    assert "bad" in lines


def test_resolve_runtime_honors_flag_noninteractive() -> None:
    proc = _bash_snippet(
        "resolve_install_runtime; printf '%s\\n' \"${INSTALL_RUNTIME}\"",
        env={"INSTALL_NONINTERACTIVE": "1", "INSTALL_RUNTIME": "docker", "INSTALL_SKIP_INFRA": "0"},
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert proc.stdout.strip().splitlines()[-1] == "docker"


def test_resolve_runtime_defaults_host_when_noninteractive(tmp_path: Path) -> None:
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    state_file = state_dir / "install-state.env"
    proc = _bash_snippet(
        f'''
INSTALL_STATE_DIR="{state_dir.as_posix()}"
INSTALL_STATE_FILE="{state_file.as_posix()}"
INSTALL_RUNTIME=""
resolve_install_runtime
printf "%s\\n" "${{INSTALL_RUNTIME}}"
''',
        env={"INSTALL_NONINTERACTIVE": "1"},
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert proc.stdout.strip().splitlines()[-1] == "host"


def test_docker_runtime_rejects_skip_infra() -> None:
    proc = _bash_snippet(
        "resolve_install_runtime",
        env={"INSTALL_NONINTERACTIVE": "1", "INSTALL_RUNTIME": "docker", "INSTALL_SKIP_INFRA": "1"},
    )
    assert proc.returncode != 0
    assert "skip-infra" in (proc.stderr + proc.stdout).lower()


def test_install_help_mentions_runtime() -> None:
    proc = subprocess.run(
        ["bash", str(ROOT / "install.sh"), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "--runtime" in proc.stdout
    assert "host" in proc.stdout and "docker" in proc.stdout


def test_list_stages_includes_runtime_bringup() -> None:
    proc = subprocess.run(
        ["bash", str(ROOT / "install.sh"), "--list-stages"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "06_runtime_bringup" in proc.stdout
