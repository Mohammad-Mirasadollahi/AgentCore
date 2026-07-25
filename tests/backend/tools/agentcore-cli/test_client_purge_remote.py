"""Tests for client remote purge scope lock."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

import pytest

from agentcore_cli.connect_config import ConnectSettings
from agentcore_cli.connect_flow.remote_purge import (
    assert_cli_scope_matches_connect,
    remote_purge_from_args,
)


def _settings(**kwargs) -> ConnectSettings:
    base = dict(
        ssh="alice@srv",
        remote_root="/opt/AgentCore",
        tenant="mir",
        workspace="dev",
        project="ThinkingSOC",
    )
    base.update(kwargs)
    return ConnectSettings(**base)


def test_scope_mismatch_hard_fails():
    settings = _settings()
    with pytest.raises(SystemExit, match="does not match connect.yaml"):
        assert_cli_scope_matches_connect(
            Namespace(tenant="other", workspace="", project=""),
            settings,
        )


def test_remote_purge_does_not_call_local_and_locks_scope(monkeypatch):
    settings = _settings()
    seen: list[list[str]] = []

    def fake_run_ssh(s, remote_command, *, connect_timeout=15):
        seen.append(list(remote_command))
        # First call: sync-running check → 0; second: purge
        if remote_command[0] == "bash":
            return 0
        return 0

    monkeypatch.setattr("agentcore_cli.connect_flow.remote_purge.run_ssh", fake_run_ssh)
    args = Namespace(yes=True, tenant="mir", workspace="dev", project="ThinkingSOC")
    assert remote_purge_from_args(settings, args) == 0
    assert any(cmd[:2] == ["/opt/AgentCore/.venv/bin/agentcore", "purge"] for cmd in seen)
    purge_cmd = next(cmd for cmd in seen if cmd[:2] == ["/opt/AgentCore/.venv/bin/agentcore", "purge"])
    assert purge_cmd[purge_cmd.index("--tenant") + 1] == "mir"
    assert "--yes" in purge_cmd


def test_remote_purge_rejects_mismatch_before_ssh(monkeypatch):
    settings = _settings()
    called = {"n": 0}

    def boom(*_a, **_k):
        called["n"] += 1
        return 0

    monkeypatch.setattr("agentcore_cli.connect_flow.remote_purge.run_ssh", boom)
    with pytest.raises(SystemExit, match="does not match"):
        remote_purge_from_args(
            settings,
            Namespace(yes=True, tenant="evil", workspace="dev", project="ThinkingSOC"),
        )
    assert called["n"] == 0


def test_cmd_purge_client_role_routes_remote(monkeypatch, tmp_path: Path):
    from agentcore_cli.commands.sync.cmd import cmd_purge
    from agentcore_cli.connect_config import ConnectSettings

    cfg = tmp_path / "connect.yaml"
    cfg.write_text("server:\n  ssh: a@b\n  remote_root: /opt/AgentCore\n", encoding="utf-8")
    seen = {"n": 0}

    monkeypatch.setattr(
        "agentcore_cli.service_runtime.paths.install_role",
        lambda _r: "client",
    )
    monkeypatch.setattr(
        "agentcore_cli.commands.sync.cmd.repo_root",
        lambda: tmp_path,
    )
    monkeypatch.setattr(
        "agentcore_cli.connect_config.try_resolve_config_path",
        lambda explicit="", project_root=None: cfg,
    )
    monkeypatch.setattr(
        "agentcore_cli.connect_config.load_connect_settings",
        lambda **_k: ConnectSettings(
            ssh="a@b",
            remote_root="/opt/AgentCore",
            tenant="mir",
            workspace="dev",
            project="App",
        ),
    )

    def fake_remote(settings, args):
        seen["n"] += 1
        return 0

    monkeypatch.setattr(
        "agentcore_cli.connect_flow.remote_purge.remote_purge_from_args",
        fake_remote,
    )
    assert cmd_purge(Namespace(yes=True, tenant="", workspace="", project="")) == 0
    assert seen["n"] == 1
