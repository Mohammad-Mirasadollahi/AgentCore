"""Client checkout sync routes over SSH when Compose stack is absent."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

from agentcore_cli.commands import sync as sync_cmd
from agentcore_cli.connect_config import ConnectSettings
from agentcore_cli.connect_flow import remote_sync_from_args


def test_remote_sync_from_args_builds_ssh_command(monkeypatch):
    seen: list[list[str]] = []

    def fake_run(settings, remote_command, *, connect_timeout=15):
        seen.append(list(remote_command))
        return 0

    monkeypatch.setattr("agentcore_cli.connect_flow._run_ssh", fake_run)
    settings = ConnectSettings(
        ssh="user@host",
        remote_root="/opt/AgentCore",
        tenant="t1",
        workspace="w1",
        project="p1",
        source_server_path="/opt/src",
    )
    args = Namespace(
        tenant=None,
        workspace=None,
        project=None,
        path=None,
        max_files=100,
        force=True,
        allow_cloud_llm=False,
    )
    assert remote_sync_from_args(settings, args) == 0
    assert seen
    cmd = seen[0]
    assert cmd[0] == "/opt/AgentCore/.venv/bin/agentcore"
    assert cmd[1] == "sync"
    assert "--path" in cmd and "/opt/src" in cmd
    assert "--force" in cmd
    assert "--max-files" in cmd and "100" in cmd


def test_cmd_sync_client_remote_helper(monkeypatch, tmp_path: Path):
    cfg = tmp_path / "connect.yaml"
    cfg.write_text(
        "server:\n  ssh: alice@srv\n  remote_root: /opt/AgentCore\n"
        "scope:\n  project: demo\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "agentcore_cli.connect_config.try_resolve_config_path",
        lambda explicit="": cfg,
    )
    monkeypatch.setattr("agentcore_cli.util.repo_root", lambda: tmp_path)

    def fake_remote(settings, args):
        assert settings.ssh == "alice@srv"
        assert args.force is True
        return 0

    monkeypatch.setattr(
        "agentcore_cli.connect_flow.remote_sync_from_args",
        fake_remote,
    )
    args = SimpleNamespace(force=True, path=None, tenant=None, workspace=None, project=None)
    assert sync_cmd._cmd_sync_client_remote(args) == 0


def test_cmd_sync_client_remote_without_connect_exits(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(
        "agentcore_cli.connect_config.try_resolve_config_path",
        lambda explicit="": None,
    )
    monkeypatch.setattr("agentcore_cli.util.repo_root", lambda: tmp_path)
    try:
        sync_cmd._cmd_sync_client_remote(SimpleNamespace())
        raised = False
    except SystemExit as exc:
        raised = True
        assert "Client installs" in str(exc)
    assert raised


def test_cmd_sync_routes_remote_when_role_client_even_with_compose(
    monkeypatch, tmp_path: Path
):
    compose = tmp_path / "backend" / "deployments" / "compose"
    compose.mkdir(parents=True, exist_ok=True)
    (compose / "compose.yaml").write_text("name: x\n", encoding="utf-8")
    (compose / ".env.local").write_text("A=1\n", encoding="utf-8")
    state = tmp_path / ".agentcore"
    state.mkdir(parents=True, exist_ok=True)
    (state / "install-state.env").write_text("role=client\n", encoding="utf-8")

    monkeypatch.setattr("agentcore_cli.util.repo_root", lambda: tmp_path)
    called: list[bool] = []

    def fake_remote(args):
        called.append(True)
        return 0

    def boom_start(_root):
        raise AssertionError("must not offer local start on client")

    monkeypatch.setattr(
        "agentcore_cli.commands.sync.cmd.cmd_sync_client_remote",
        fake_remote,
    )
    monkeypatch.setattr(
        "agentcore_cli.service_runtime.ensure_running_or_offer_start",
        boom_start,
    )
    args = SimpleNamespace(
        force=True,
        path=None,
        tenant=None,
        workspace=None,
        project=None,
        cpu_percent=None,
        allow_cloud_llm=False,
    )
    assert sync_cmd.cmd_sync(args) == 0
    assert called == [True]
