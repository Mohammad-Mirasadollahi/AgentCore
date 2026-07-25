"""Tests for agentcore status."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from agentcore_cli.commands.status import _overall, build_status_report, cmd_status
from agentcore_cli.connect_config import ConnectSettings
from agentcore_cli.parser import build_parser


def test_parser_status():
    parser = build_parser()
    args = parser.parse_args(["status"])
    assert args.command == "status"
    assert args.json is False


def test_overall_empty_vs_ready():
    assert (
        _overall(
            {
                "graph": {"ok": True, "symbol_count": 0, "pending_count": 0},
                "postgres": {},
                "neo4j": {},
            }
        )
        == "empty"
    )
    assert (
        _overall(
            {
                "graph": {"ok": True, "symbol_count": 3, "pending_count": 0},
                "postgres": {"configured": True, "reachable": True},
                "neo4j": {"configured": True, "reachable": True},
            }
        )
        == "ready"
    )
    assert (
        _overall(
            {
                "graph": {"ok": True, "symbol_count": 3, "pending_count": 2},
                "postgres": {},
                "neo4j": {},
            }
        )
        == "pending_sync"
    )
    assert (
        _overall(
            {
                "graph": {"ok": True, "symbol_count": 3, "pending_count": 0},
                "postgres": {"configured": True, "reachable": False},
                "neo4j": {"configured": True, "reachable": True},
            }
        )
        == "Postgres unreachable"
    )


def test_cmd_status_proxies_to_server_on_client_install(monkeypatch, tmp_path: Path):
    cfg = tmp_path / "connect.yaml"
    cfg.write_text("server:\n  ssh: alice@srv\n  remote_root: /opt/AgentCore\n", encoding="utf-8")
    seen: list[list[str]] = []

    monkeypatch.setattr(
        "agentcore_cli.service_runtime.paths.local_compose_stack_present",
        lambda _root: False,
    )
    monkeypatch.setattr(
        "agentcore_cli.connect_config.try_resolve_config_path",
        lambda explicit="", project_root=None: cfg,
    )
    monkeypatch.setattr(
        "agentcore_cli.connect_config.load_connect_settings",
        lambda **_k: ConnectSettings(ssh="alice@srv", remote_root="/opt/AgentCore", project="demo"),
    )
    monkeypatch.setattr(
        "agentcore_cli.connect_flow.ssh.run_ssh",
        lambda settings, remote_command, *, connect_timeout=15: seen.append(list(remote_command)) or 0,
    )
    assert cmd_status(Namespace(tenant="", workspace="", project="", json=False, verbose=False)) == 0
    assert seen
    assert seen[0][0].endswith("/agentcore")
    assert seen[0][1] == "status"


def test_build_status_report_smoke(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AGENTCORE_TENANT_ID", raising=False)
    monkeypatch.delenv("AGENTCORE_WORKSPACE_ID", raising=False)
    monkeypatch.delenv("AGENTCORE_PROJECT_ID", raising=False)
    monkeypatch.setattr("agentcore_cli.commands.status.load_dotenv_files", lambda **_: [])
    monkeypatch.setattr("agentcore_cli.cli_defaults.load_dotenv_files", lambda **_: [])
    monkeypatch.setattr("agentcore_cli.cli_defaults.peek_identity_scope", lambda: {})
    monkeypatch.setattr("agentcore_cli.cli_defaults.peek_connect_scope", lambda: {})
    monkeypatch.setattr(
        "agentcore_cli.commands.status._graph_snapshot",
        lambda *_a, **_k: {
            "ok": True,
            "backend": "memory",
            "symbol_count": 0,
            "edge_count": 0,
            "pending_count": 0,
            "pending_files": [],
            "last_sync_at": None,
        },
    )
    monkeypatch.setattr(
        "agentcore_cli.commands.status._postgres_probe",
        lambda: {"configured": False, "reachable": None},
    )
    monkeypatch.setattr(
        "agentcore_cli.commands.status._neo4j_probe",
        lambda: {"configured": False, "reachable": None},
    )
    report = build_status_report(cwd=tmp_path)
    assert report["status"] == "empty"
    assert "agentcore sync" in " ".join(report["hints"])
    assert report["scope"]["tenant"] == "agentcore"
