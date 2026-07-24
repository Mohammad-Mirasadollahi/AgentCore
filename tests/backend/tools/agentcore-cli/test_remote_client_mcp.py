"""Tests for remote dev client MCP wiring."""

from __future__ import annotations

import json
import shlex
from pathlib import Path

from agentcore_cli.main import main
from agentcore_cli.mcp_client_targets import merge_mcp_servers_file, resolve_client_ids, write_fragment_to_clients
from agentcore_cli.remote_client import (
    materialize_ssh_mcp_fragment,
    parse_env_file,
    remote_mcp_serve_command,
    remote_register_project,
    ssh_argv,
)


def test_ssh_argv_joins_remote_command_with_shell_quoting():
    argv = ssh_argv(
        "ops@host",
        ["bash", "-lc", "set -euo pipefail; cd /opt/AgentCore"],
        identity_file="~/.ssh/id_ed25519_agentcore",
    )
    assert argv[0] == "ssh"
    assert "-i" in argv
    assert argv[-2] == "ops@host"
    # Single remote string — OpenSSH must not see bare `set` as bash -c payload.
    assert argv[-1] == shlex.join(["bash", "-lc", "set -euo pipefail; cd /opt/AgentCore"])
    assert "pipefail" in argv[-1]


def test_ssh_argv_preserves_python_c_script():
    script = "import agentcore_cli; import agentcore_cli.remote_mcp_serve"
    argv = ssh_argv("root@192.168.1.150", ["/opt/AgentCore/.venv/bin/python", "-c", script])
    assert argv[-1] == shlex.join(["/opt/AgentCore/.venv/bin/python", "-c", script])


def test_materialize_ssh_mcp_fragment_shape():
    frag = materialize_ssh_mcp_fragment(
        ssh_target="ops@agentcore.example",
        remote_root="/opt/AgentCore",
        tenant="t",
        workspace="w",
        project_id="p",
        identity_file="/home/ops/.ssh/id_ed25519_agentcore",
    )
    server = frag["mcpServers"]["AgentCore-Programming"]
    assert server["command"] == "ssh"
    assert "-i" in server["args"]
    assert server["args"][-2] == "ops@agentcore.example"
    assert server["args"][-1] == shlex.join(
        [
            "/opt/AgentCore/.venv/bin/python",
            "-m",
            "agentcore_cli.remote_mcp_serve",
            "t",
            "w",
            "p",
        ]
    )


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
    assert "AgentCore-Programming" in merged["mcpServers"]


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
    assert "AgentCore-Programming" in payload["mcpServers"]


def test_remote_register_project_single_quiet_register(monkeypatch, capsys):
    """Connect must not run activate (duplicate JSON) or leak register JSON over SSH."""
    seen: list[list[str]] = []

    def fake_run_ssh(ssh_target, remote_command, *, identity_file=None, **_kwargs):
        assert ssh_target == "ops@host"
        seen.append(list(remote_command))
        return 0

    monkeypatch.setattr("agentcore_cli.remote_client.run_ssh", fake_run_ssh)
    remote_register_project(
        "ops@host",
        "/opt/AgentCore",
        "mir",
        "dev",
        "ThinkingSOC",
        project_name="ThinkingSOC",
        usage_profile="programming-cursor-mcp",
    )
    assert len(seen) == 1
    shell = seen[0][-1]
    assert "project register" in shell
    assert "project activate" not in shell
    assert ">/dev/null" in shell
    out = capsys.readouterr().out
    assert "registered" in out
    assert "ThinkingSOC" in out
    assert '"saved"' not in out
