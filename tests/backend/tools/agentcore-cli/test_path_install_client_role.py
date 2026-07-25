"""Client role PATH shim points at thin entry."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path


def test_path_install_client_role_uses_thin_binary(monkeypatch, tmp_path: Path):
    from agentcore_cli.commands import path_cmd

    root = tmp_path / "AgentCore"
    venv_bin = root / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    thin = venv_bin / "agentcore-client"
    thin.write_text("#!/bin/sh\n", encoding="utf-8")
    thin.chmod(0o755)
    (venv_bin / "agentcore").write_text("#!/bin/sh\n", encoding="utf-8")

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(path_cmd, "repo_root", lambda: root)
    monkeypatch.setattr(
        "agentcore_cli.service_runtime.paths.install_role",
        lambda _r: "client",
    )

    assert path_cmd.cmd_path_install(Namespace(quiet=True, no_shell_rc=True, shell_rc="")) == 0
    link = home / ".local" / "bin" / "agentcore"
    assert link.is_symlink()
    assert link.resolve() == thin.resolve()
