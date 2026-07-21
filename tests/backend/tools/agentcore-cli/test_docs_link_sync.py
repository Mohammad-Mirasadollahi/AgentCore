"""Phase-2 docs link orchestrator (docs-sync + code-graph projection)."""

from __future__ import annotations

from pathlib import Path

from agentcore_cli.docs_link_sync import sync_human_docs
from agentcore_cli.markdown_frontmatter import parse_markdown_frontmatter, provisional_frontmatter
from code_graph_service.core import CodeGraphService, Scope
from code_graph_service.testing import InMemoryStore


SCOPE = Scope("t", "w", "docs-link")

AUTH_SOURCE = '''\
def login(user, password):
    return True
'''


LINKED_DOC = '''\
---
doc_id: doc-login-rules
title: Login rules
owner: platform
status: active
schema_version: "1.0"
linked_symbols:
  - src.auth.login
decision_refs: []
---

# Login rules

Human documentation for login.
'''


UNLINKED_DOC = '''\
---
doc_id: doc-overview
title: Overview
owner: platform
status: active
schema_version: "1.0"
linked_symbols: []
decision_refs: []
---

# Overview

No symbol links.
'''


def test_parse_and_provisional_frontmatter():
    fm, body = parse_markdown_frontmatter(LINKED_DOC)
    assert fm["doc_id"] == "doc-login-rules"
    assert "Human documentation" in body
    filled = provisional_frontmatter("docs/x.md", "# Hello\n\nBody", {})
    assert filled["doc_id"].startswith("doc-")
    assert filled["title"] == "Hello"
    assert filled["linked_symbols"] == []


def test_sync_human_docs_creates_anchor_and_edge(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("AGENTCORE_DOCS_SYNC_DATABASE_URL", raising=False)
    (tmp_path / "src").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "src" / "auth.py").write_text(AUTH_SOURCE, encoding="utf-8")
    (tmp_path / "docs" / "login.md").write_text(LINKED_DOC, encoding="utf-8")
    (tmp_path / "docs" / "overview.md").write_text(UNLINKED_DOC, encoding="utf-8")

    store = InMemoryStore()
    graph = CodeGraphService(store)
    graph.ingest_file(
        SCOPE,
        "test",
        "c1",
        "k1",
        {"file_path": "src/auth.py", "source": AUTH_SOURCE, "language": "python"},
    )

    result = sync_human_docs(
        graph_service=graph,
        graph_scope=SCOPE,
        root_path=tmp_path,
        filters={
            "docs_enabled": True,
            "doc_match_globs": ["**/*.md"],
            "doc_exclude_dirs": [],
            "doc_exclude_globs": [],
            "doc_paths": [],
            "max_files": 50,
        },
        actor="test",
        correlation_id="corr-1",
        repo_name="fixture",
    )
    assert result.docs_discovered == 2
    assert result.docs_indexed == 2
    assert result.links_created == 1
    assert result.anchors_registered == 1
    assert result.unresolved_tokens == []

    human_id = "doc:human:docs-link:doc-login-rules"
    human = store.get_symbol(human_id, SCOPE)
    login = store.get_symbol_by_qualified_name(SCOPE, "src.auth.login")
    assert login is not None
    edges = [
        e
        for e in store.list_edges(SCOPE)
        if e.rel_type == "DOCUMENTED_BY" and e.source_id == login.id and e.target_id == human.id
    ]
    assert len(edges) == 1

    # Unlinked overview still projected as a node, but no DOCUMENTED_BY from login to it.
    overview = store.get_symbol("doc:human:docs-link:doc-overview", SCOPE)
    assert overview is not None
    overview_edges = [e for e in store.list_edges(SCOPE) if e.target_id == overview.id and e.rel_type == "DOCUMENTED_BY"]
    assert overview_edges == []


def test_resolve_sync_filters_docs_vs_code(tmp_path: Path, monkeypatch):
    from agentcore_cli.sync_config import resolve_sync_filters

    monkeypatch.delenv("AGENTCORE_SYNC_DOC_PATHS", raising=False)
    monkeypatch.delenv("AGENTCORE_SYNC_DOC_MATCH", raising=False)
    monkeypatch.delenv("AGENTCORE_SYNC_EXCLUDE_DIRS", raising=False)
    (tmp_path / "agentcore.sync.yaml").write_text(
        "\n".join(
            [
                "code:",
                "  exclude:",
                "    - tests",
                "docs:",
                "  match:",
                "    - '**/*.md'",
                "  exclude:",
                "    - '**/CHANGELOG.md'",
                "",
            ]
        ),
        encoding="utf-8",
    )
    filters = resolve_sync_filters(root=tmp_path)
    assert "tests" in filters["exclude_dirs"]
    assert "docs" not in filters["exclude_dirs"]  # code exclude must not require docs
    assert filters["docs_enabled"] is True
    assert "**/*.md" in filters["doc_match_globs"]
    assert "**/CHANGELOG.md" in filters["doc_exclude_globs"]
    assert filters["include_paths"] == []

    (tmp_path / "agentcore.sync.yaml").write_text(
        "code:\n  exclude: []\ndocs:\n  match: []\n",
        encoding="utf-8",
    )
    filters2 = resolve_sync_filters(root=tmp_path)
    assert filters2["docs_enabled"] is False
    assert filters2["doc_match_globs"] == []

    # Legacy: bare exclude still defaults docs to **/*.md
    (tmp_path / "agentcore.sync.yaml").write_text("exclude: []\n", encoding="utf-8")
    filters3 = resolve_sync_filters(root=tmp_path)
    assert filters3["docs_enabled"] is True
    assert "**/*.md" in filters3["doc_match_globs"]
