import json
import os
from pathlib import Path

from agentcore_cli.main import main


def test_profile_list_and_show(capsys):
    assert main(["profile", "list"]) == 0
    out = capsys.readouterr().out
    assert "programming-cursor-mcp" in out
    assert main(["profile", "show", "programming-cursor-mcp"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["profile_id"] == "programming-cursor-mcp"


def test_project_lifecycle_and_cursor_export(tmp_path, monkeypatch):
    root = Path("/opt/AgentCore")
    monkeypatch.setenv("AGENTCORE_ROOT", str(root))
    import agentcore_cli.state as state

    monkeypatch.setattr(state, "default_state_root", lambda _root: tmp_path / "projects")

    assert (
        main(
            [
                "project",
                "register",
                "--tenant",
                "t",
                "--workspace",
                "w",
                "--project",
                "p",
                "--name",
                "Demo",
                "--usage-profile",
                "default",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "project",
                "activate",
                "--tenant",
                "t",
                "--workspace",
                "w",
                "--project",
                "p",
                "--usage-profile",
                "programming-cursor-mcp",
            ]
        )
        == 0
    )
    project = json.loads((tmp_path / "projects" / "t" / "w" / "p.json").read_text(encoding="utf-8"))
    assert project["usage_profile"] == "programming-cursor-mcp"

    out_file = tmp_path / "mcp.json"
    assert (
        main(
            [
                "cursor",
                "export",
                "--tenant",
                "t",
                "--workspace",
                "w",
                "--project",
                "p",
                "--out",
                str(out_file),
            ]
        )
        == 0
    )
    fragment = json.loads(out_file.read_text(encoding="utf-8"))
    assert "AgentCore-Programming" in fragment["mcpServers"]
    assert fragment["mcpServers"]["AgentCore-Programming"]["env"]["AGENTCORE_PROJECT_ID"] == "p"


def test_mcp_tools(capsys):
    assert main(["mcp", "tools", "--usage-profile", "programming-cursor-mcp"]) == 0
    assert "agentcore_memory_retrieve" in capsys.readouterr().out


def test_path_install(tmp_path, monkeypatch):
    root = Path("/opt/AgentCore")
    monkeypatch.setenv("AGENTCORE_ROOT", str(root))
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    source = root / ".venv" / "bin" / "agentcore"
    if not source.is_file():
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("#!/bin/sh\necho agentcore\n", encoding="utf-8")
        source.chmod(0o755)
    assert main(["path", "install"]) == 0
    target = home / ".local" / "bin" / "agentcore"
    assert target.is_symlink()
    assert os.path.realpath(target) == os.path.realpath(source)


def _write_mini_profile(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "ports": {
                    "AGENTCORE_API_PORT": 32100,
                    "AGENTCORE_ADMIN_PORT": 32101,
                },
                "service_owners": {
                    "api": "AGENTCORE_API_PORT",
                    "admin": "AGENTCORE_ADMIN_PORT",
                },
            }
        ),
        encoding="utf-8",
    )


def test_ports_show_and_check(tmp_path, monkeypatch, capsys):
    profile = tmp_path / "ports.json"
    _write_mini_profile(profile)
    monkeypatch.setenv("AGENTCORE_API_PORT", "32155")

    assert main(["ports", "show", "--profile", str(profile)]) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["ports"]["AGENTCORE_API_PORT"] == 32155
    assert shown["ports"]["AGENTCORE_ADMIN_PORT"] == 32101

    import agentcore_cli.commands.ports as ports_cmd

    monkeypatch.setattr(ports_cmd, "check_port_available", lambda port, host="127.0.0.1": True)
    assert main(["ports", "check", "--profile", str(profile)]) == 0
    ok_payload = json.loads(capsys.readouterr().out)
    assert ok_payload["ok"] is True
    assert ok_payload["ports"]["AGENTCORE_API_PORT"] == {"port": 32155, "available": True}

    monkeypatch.setattr(
        ports_cmd,
        "check_port_available",
        lambda port, host="127.0.0.1": port != 32155,
    )
    assert main(["ports", "check", "--profile", str(profile)]) == 1
    bad = json.loads(capsys.readouterr().out)
    assert bad["ok"] is False
    assert bad["ports"]["AGENTCORE_API_PORT"]["available"] is False
    assert bad["ports"]["AGENTCORE_ADMIN_PORT"]["available"] is True


def test_graph_smoke_ingest_explore(capsys, monkeypatch):
    monkeypatch.setenv("AGENTCORE_ROOT", "/opt/AgentCore")
    monkeypatch.setenv("AGENTCORE_GRAPH_CLI_BACKEND", "memory")
    sample = "/opt/AgentCore/samples/e2e-graph-probe/src"
    assert (
        main(
            [
                "graph",
                "smoke",
                "--tenant",
                "t",
                "--workspace",
                "w",
                "--project",
                "p",
                "--path",
                sample,
                "--query",
                "login password",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["hybrid_hits"] >= 1
    assert payload["explore_sections"] >= 1


def test_graph_watch_once(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTCORE_ROOT", "/opt/AgentCore")
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x=1\n", encoding="utf-8")
    assert (
        main(
            [
                "graph",
                "watch",
                "--tenant",
                "t",
                "--workspace",
                "w",
                "--project",
                "p",
                "--path",
                str(src),
                "--interval",
                "0.05",
                "--debounce",
                "0.01",
                "--max-wait",
                "0.1",
                "--once",
            ]
        )
        == 0
    )


def test_doctor_imports_mcp_gateway(capsys, monkeypatch):
    monkeypatch.setenv("AGENTCORE_ROOT", "/opt/AgentCore")
    assert main(["doctor"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["venv_python"] is True
    assert payload["import_mcp_gateway_service"] is True

