"""Unit checks for AgentCore modular install (no full OS/docker mutation)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
INSTALL_SH = ROOT / "install.sh"
INSTALL_LIB = ROOT / "scripts" / "install"

REQUIRED_MODULES = (
    "common.sh",
    "load.sh",
    "01_prerequisites.sh",
    "02_venv.sh",
    "03_compose_env.sh",
    "04_docker_infra.sh",
    "05_verify.sh",
    "README.md",
)


def test_install_entrypoint_exists_and_executable() -> None:
    assert INSTALL_SH.is_file()
    assert os.access(INSTALL_SH, os.X_OK)


@pytest.mark.parametrize("name", REQUIRED_MODULES)
def test_install_module_present(name: str) -> None:
    path = INSTALL_LIB / name
    assert path.is_file(), f"missing install module: {path}"


def test_install_help_exits_zero() -> None:
    proc = subprocess.run(
        ["bash", str(INSTALL_SH), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "AgentCore installer" in proc.stdout
    assert "--check" in proc.stdout
    assert "--upgrade" in proc.stdout


def test_install_list_stages_order() -> None:
    proc = subprocess.run(
        ["bash", str(INSTALL_SH), "--list-stages"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    body = proc.stdout
    expected = [
        "01_prerequisites",
        "02_venv",
        "03_compose_env",
        "04_docker_infra",
        "05_verify",
    ]
    positions = [body.index(name) for name in expected]
    assert positions == sorted(positions)


def test_common_helpers_source_cleanly() -> None:
    script = r"""
set -euo pipefail
export AGENTCORE_ROOT="%s"
# shellcheck source=/dev/null
source "%s/common.sh"
py="$(python_bin)"
test -n "$py"
secret="$(random_secret)"
test "${#secret}" -ge 16
echo OK
""" % (
        ROOT,
        INSTALL_LIB,
    )
    proc = subprocess.run(
        ["bash", "-c", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "OK" in proc.stdout


def test_seed_repo_operator_files_copies_examples(tmp_path: Path) -> None:
    """Install seeds .env and agentcore.sync.yaml from examples when missing."""
    (tmp_path / ".env.example").write_text("AGENTCORE_TENANT_ID=demo\n", encoding="utf-8")
    (tmp_path / "agentcore.sync.yaml.example").write_text(
        "code:\n  exclude: []\ndocs:\n  match: []\n",
        encoding="utf-8",
    )
    script = r"""
set -euo pipefail
export AGENTCORE_ROOT="%s"
source "%s/common.sh"
seed_repo_operator_files
test -f "${AGENTCORE_ROOT}/.env"
test -f "${AGENTCORE_ROOT}/agentcore.sync.yaml"
grep -q 'AGENTCORE_TENANT_ID=demo' "${AGENTCORE_ROOT}/.env"
# Second call must not overwrite
echo KEEP > "${AGENTCORE_ROOT}/.env"
seed_repo_operator_files
grep -q KEEP "${AGENTCORE_ROOT}/.env"
echo OK
""" % (
        tmp_path,
        INSTALL_LIB,
    )
    proc = subprocess.run(
        ["bash", "-c", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "OK" in proc.stdout


def test_unknown_flag_exits_nonzero() -> None:
    proc = subprocess.run(
        ["bash", str(INSTALL_SH), "--not-a-real-flag"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0


def test_install_cli_on_path_writes_shim_and_shell_rc(tmp_path: Path) -> None:
    """Stage-02 helper must create ~/.local/bin/agentcore even if PATH already has it."""
    home = tmp_path / "home"
    local_bin = home / ".local" / "bin"
    local_bin.mkdir(parents=True)
    bashrc = home / ".bashrc"
    bashrc.write_text("# pretest\n", encoding="utf-8")
    # Fake venv agentcore that delegates to the real CLI for `path install`.
    fake_venv = tmp_path / "venv" / "bin"
    fake_venv.mkdir(parents=True)
    real_cli = ROOT / ".venv" / "bin" / "agentcore"
    if not real_cli.is_file():
        pytest.skip("project .venv/bin/agentcore required")
    fake_cli = fake_venv / "agentcore"
    fake_cli.symlink_to(real_cli)

    script = r"""
set -euo pipefail
export AGENTCORE_ROOT="%s"
export HOME="%s"
export PATH="%s:${PATH}"
source "%s/common.sh"
install_cli_on_path "%s"
user_cli_on_path
grep -q 'AgentCore CLI' "${HOME}/.bashrc"
test -e "${HOME}/.local/bin/agentcore"
echo OK
""" % (
        ROOT,
        home,
        local_bin,
        INSTALL_LIB,
        fake_cli,
    )
    proc = subprocess.run(
        ["bash", "-c", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "HOME": str(home), "AGENTCORE_ROOT": str(ROOT)},
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "OK" in proc.stdout
    assert (home / ".local" / "bin" / "agentcore").exists()
    assert "AgentCore CLI" in bashrc.read_text(encoding="utf-8")


def test_stage_02_requires_path_shim_in_check() -> None:
    body = (INSTALL_LIB / "02_venv.sh").read_text(encoding="utf-8")
    assert "user_cli_on_path" in body
    assert "install_cli_on_path" in body
    assert "|| true" not in body
    common = (INSTALL_LIB / "common.sh").read_text(encoding="utf-8")
    assert "install_cli_on_path()" in common
    assert "user_cli_on_path()" in common
