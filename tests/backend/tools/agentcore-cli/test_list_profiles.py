"""Tests for list-profiles / list_projects."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from agentcore_cli import state
from agentcore_cli.commands.list_profiles import cmd_list_profiles
from agentcore_cli.identity import write_identity
from agentcore_cli.parser import build_parser


def test_parser_list_profiles():
    parser = build_parser()
    args = parser.parse_args(["list-profiles", "--json"])
    assert args.command == "list-profiles"
    assert args.json is True


def test_list_projects_reads_state_files(tmp_path: Path):
    root = state.default_state_root(tmp_path)
    state.save_project(
        root,
        {
            "tenant_id": "acme",
            "workspace_id": "eng",
            "project_id": "payments",
            "name": "Payments",
            "usage_profile": "programming-cursor-mcp",
            "domain_pack": "programming",
            "feature_profile": "cursor-mcp",
            "status": "active",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-02T00:00:00Z",
        },
    )
    items = state.list_projects(root)
    assert len(items) == 1
    assert items[0]["tenant_id"] == "acme"
    assert items[0]["project_id"] == "payments"
    assert items[0]["usage_profile"] == "programming-cursor-mcp"


def test_cmd_list_profiles_marks_active(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setattr("agentcore_cli.commands.list_profiles.repo_root", lambda: tmp_path)
    monkeypatch.setattr("agentcore_cli.identity.Path.home", lambda: tmp_path)
    monkeypatch.setattr("agentcore_cli.cli_defaults.load_dotenv_files", lambda **_: [])
    monkeypatch.setattr("agentcore_cli.cli_defaults.peek_connect_scope", lambda: {})
    monkeypatch.delenv("AGENTCORE_TENANT_ID", raising=False)
    monkeypatch.delenv("AGENTCORE_WORKSPACE_ID", raising=False)
    monkeypatch.delenv("AGENTCORE_PROJECT_ID", raising=False)

    root = state.default_state_root(tmp_path)
    state.save_project(
        root,
        {
            "tenant_id": "acme",
            "workspace_id": "eng",
            "project_id": "app",
            "name": "App",
            "usage_profile": "programming-cursor-mcp",
            "status": "active",
        },
    )
    write_identity(tenant="acme", workspace="eng", project="app", display_name="Ali")

    code = cmd_list_profiles(Namespace(json=False, verbose=False))
    assert code == 0
    out = capsys.readouterr().out
    assert "acme" in out
    assert "eng" in out
    assert "app" in out
    assert "tenant" in out
    assert "workspace" in out
    assert "project" in out
    assert "programming-cursor-mcp" in out
    assert "*" in out
