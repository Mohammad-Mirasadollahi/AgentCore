"""Tests for remote dev client MCP wiring."""

from __future__ import annotations

import json
from pathlib import Path

from agentcore_cli.main import main
from agentcore_cli.mcp_client_targets import merge_mcp_servers_file, resolve_client_ids, write_fragment_to_clients
from agentcore_cli.remote_client import materialize_ssh_mcp_fragment, parse_env_file, remote_mcp_serve_command


def test_materialize_ssh_mcp_fragment_shape():
    frag = materialize_ssh_mcp_fragment(
        ssh_target="ops@agentcore.example",
        remote_root="/opt/AgentCore",
        tenant="t",
        workspace="w",
        project_id="p",
    )
    server = frag["mcpServers"]["agentcore-programming"]
    assert server["command"] == "ssh"
    assert server["args"][-7:] == [
        "ops@agentcore.example",
        "/opt/AgentCore/.venv/bin/python",
        "-m",
        "agentcore_cli.remote_mcp_serve",
        "t",
        "w",
        "p",
    ]


def test_remote_mcp_serve_command_windows():
    cmd = remote_mcp_serve_command("/opt/AgentCore", "a", "b", "c", remote_os="windows")
    assert cmd[0].endswith("Scripts/python.exe")


def test_parse_env_file(tmp_path: Path):
    env = tmp_path / ".env.local"
    env.write_text(
        "# comment\nAGENTCORE_POSTGRES_PORT=32232\nAGENTCORE_POSTGRES_USER=agentcore\n",
        encoding="utf-8",
    )
    assert parse_env_file(env)["AGENTCORE_POSTGRES_PORT"] == "32232"


def test_merge_mcp_servers_file_preserves_other_servers(tmp_path: Path):
    target = tmp_path / "mcp.json"
    target.write_text(
        json.dumps({"mcpServers": {"other": {"command": "echo", "args": []}}}) + "\n",
        encoding="utf-8",
    )
    fragment = materialize_ssh_mcp_fragment(
        ssh_target="u@h",
        remote_root="/opt/AgentCore",
        tenant="a",
        workspace="b",
        project_id="c",
    )
    merge_mcp_servers_file(target, fragment)
    merged = json.loads(target.read_text(encoding="utf-8"))
    assert "other" in merged["mcpServers"]
    assert "agentcore-programming" in merged["mcpServers"]


def test_client_wire_remote_dry_run(capsys):
    assert (
        main(
            [
                "client",
                "wire-remote",
                "--ssh",
                "u@host",
                "--remote-root",
                "/opt/AgentCore",
                "--tenant",
                "t",
                "--workspace",
                "w",
                "--project",
                "p",
                "--dry-run",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert "agentcore-programming" in payload["mcpServers"]
