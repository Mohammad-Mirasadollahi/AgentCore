"""CLI generation-context includes hybrid_documentation pack."""

from __future__ import annotations

import json

from agentcore_cli.commands import graph as graph_cmd
from code_graph_service.core import CodeGraphService, Scope
from code_graph_service.testing import InMemoryStore


def test_cmd_graph_generation_context_prints_hybrid(monkeypatch, capsys):
    store = InMemoryStore()
    svc = CodeGraphService(store)
    scope = Scope("t", "w", "gen-ctx")
    svc.ingest_file(
        scope,
        "agent",
        "c",
        "idem",
        {
            "file_path": "src/x.py",
            "source": "def hello():\n    return 1\n",
            "language": "python",
        },
    )
    sid = f"sym:{scope.project_id}:src.x.hello"

    class _Args:
        symbol_id = sid
        qualified_name = ""
        max_symbols = 8

    monkeypatch.setattr(graph_cmd, "_graph_service", lambda: svc)
    monkeypatch.setattr(graph_cmd, "_graph_scope", lambda args: scope)
    code = graph_cmd.cmd_graph_generation_context(_Args())
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert "hybrid_documentation" in payload
    assert payload["hybrid_documentation"]["mode"] == "hybrid"
    assert payload["hybrid_documentation"]["coverage"]["ast"] is True
