"""Tests for agentcore path install quiet mode."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
CLI = ROOT / ".venv" / "bin" / "agentcore"


@pytest.mark.skipif(not CLI.is_file(), reason="project .venv/bin/agentcore required")
def test_path_install_quiet_suppresses_json(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["PATH"] = f"{ROOT / '.venv' / 'bin'}:{env.get('PATH', '')}"
    proc = subprocess.run(
        [str(CLI), "path", "install", "--quiet", "--no-shell-rc"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "{" not in proc.stdout
    assert "symlink" not in proc.stdout
    link = home / ".local" / "bin" / "agentcore"
    assert link.is_symlink() or link.exists()


@pytest.mark.skipif(not CLI.is_file(), reason="project .venv/bin/agentcore required")
def test_path_install_default_prints_json(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["PATH"] = f"{ROOT / '.venv' / 'bin'}:{env.get('PATH', '')}"
    proc = subprocess.run(
        [str(CLI), "path", "install", "--no-shell-rc"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    start = proc.stdout.find("{")
    end = proc.stdout.rfind("}")
    assert start >= 0 and end > start
    payload = json.loads(proc.stdout[start : end + 1])
    assert payload.get("symlink_ok") is True
