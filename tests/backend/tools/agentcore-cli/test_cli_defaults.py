"""Tests for operator CLI defaults (env / connect.yaml / dogfood)."""

from __future__ import annotations

import json
from pathlib import Path

from agentcore_cli.cli_defaults import load_dotenv_files, resolve_operator_scope
from agentcore_cli.parser import build_parser


def test_resolve_operator_scope_defaults(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AGENTCORE_TENANT_ID", raising=False)
    monkeypatch.delenv("AGENTCORE_WORKSPACE_ID", raising=False)
    monkeypatch.delenv("AGENTCORE_PROJECT_ID", raising=False)
    monkeypatch.setattr("agentcore_cli.cli_defaults.peek_connect_scope", lambda: {})
    monkeypatch.setattr("agentcore_cli.cli_defaults.peek_identity_scope", lambda: {})
    monkeypatch.setattr("agentcore_cli.cli_defaults.load_dotenv_files", lambda **_: [])
    tenant, workspace, project = resolve_operator_scope(cwd=tmp_path)
    assert tenant == "agentcore"
    assert workspace == "dev"
    assert project == tmp_path.name


def test_resolve_operator_scope_env_wins(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("agentcore_cli.cli_defaults.peek_connect_scope", lambda: {})
    monkeypatch.setattr("agentcore_cli.cli_defaults.load_dotenv_files", lambda **_: [])
    monkeypatch.setenv("AGENTCORE_TENANT_ID", "acme")
    monkeypatch.setenv("AGENTCORE_WORKSPACE_ID", "eng")
    monkeypatch.setenv("AGENTCORE_PROJECT_ID", "payments")
    tenant, workspace, project = resolve_operator_scope(cwd=tmp_path)
    assert (tenant, workspace, project) == ("acme", "eng", "payments")


def test_resolve_operator_scope_cli_wins(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("agentcore_cli.cli_defaults.peek_connect_scope", lambda: {"tenant": "from-yaml"})
    monkeypatch.setattr("agentcore_cli.cli_defaults.load_dotenv_files", lambda **_: [])
    monkeypatch.setenv("AGENTCORE_TENANT_ID", "from-env")
    tenant, workspace, project = resolve_operator_scope(
        tenant="from-cli",
        workspace="w",
        project="p",
        cwd=tmp_path,
    )
    assert tenant == "from-cli"
    assert workspace == "w"
    assert project == "p"


def test_load_dotenv_files_fills_missing(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("AGENTCORE_TENANT_ID", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("AGENTCORE_TENANT_ID=from-dotenv\n", encoding="utf-8")
    monkeypatch.setattr("agentcore_cli.util.repo_root", lambda: tmp_path)
    loaded = load_dotenv_files(root=tmp_path)
    assert env_file in loaded
    assert os_environ_tenant() == "from-dotenv"


def os_environ_tenant() -> str:
    import os

    return os.environ.get("AGENTCORE_TENANT_ID", "")


def test_parser_sync_defaults_path_and_optional_scope():
    parser = build_parser()
    args = parser.parse_args(["sync"])
    assert args.command == "sync"
    assert args.path is None  # uses pinned software paths from init
    assert args.tenant == ""
    assert args.max_files == 2000
    purge = parser.parse_args(["purge", "--yes"])
    assert purge.yes is True
