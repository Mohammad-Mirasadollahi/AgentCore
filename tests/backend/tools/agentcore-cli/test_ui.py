"""Tests for CLI terminal styling helpers."""

from __future__ import annotations

from agentcore_cli import ui


def test_paint_disabled_without_tty(monkeypatch):
    monkeypatch.setattr(ui, "_use_color", lambda: False)
    assert ui.ok("ready") == "ready"
    assert ui.scope_line("a", "b", "c") == "a / b / c"


def test_summarize_paths_relative():
    paths = ui.summarize_paths(
        ["/opt/AgentCore/.cursor/mcp.json", "/opt/AgentCore/.vscode/mcp.json"],
        relative_to="/opt/AgentCore",
    )
    assert paths == [".cursor/mcp.json", ".vscode/mcp.json"]
