"""Tests for connect security helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentcore_cli.connect_config import ConnectSettings
from agentcore_cli.connect_security import (
    atomic_write_text,
    reject_secrets_in_connect_doc,
    validate_connect_settings,
)
from agentcore_cli.mcp_client_targets import merge_mcp_servers_file


def test_reject_password_in_connect_doc():
    with pytest.raises(SystemExit):
        reject_secrets_in_connect_doc({"auth": {"password": "secret"}}, Path("/tmp/x.yaml"))


def test_validate_warns_on_root_ssh():
    settings = ConnectSettings(ssh="root@host", project="p")
    warnings = validate_connect_settings(settings)
    assert any("root" in w for w in warnings)


def test_atomic_merge_preserves_other_servers(tmp_path: Path):
    target = tmp_path / ".cursor" / "mcp.json"
    target.parent.mkdir(parents=True)
    target.write_text(
        json.dumps({"mcpServers": {"other": {"command": "echo", "args": []}}}) + "\n",
        encoding="utf-8",
    )
    fragment = {
        "mcpServers": {
            "agentcore-programming": {"command": "ssh", "args": ["u@h", "serve"]},
        }
    }
    merge_mcp_servers_file(target, fragment)
    merged = json.loads(target.read_text(encoding="utf-8"))
    assert "other" in merged["mcpServers"]
    assert "agentcore-programming" in merged["mcpServers"]


def test_atomic_write_text(tmp_path: Path):
    path = tmp_path / "out.json"
    atomic_write_text(path, "{}\n")
    assert path.read_text(encoding="utf-8") == "{}\n"
