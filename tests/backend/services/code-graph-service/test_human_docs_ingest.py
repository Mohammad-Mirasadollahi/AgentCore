"""Human documentation discovery, resolve, and DOCUMENTED_BY projection."""

from __future__ import annotations

from pathlib import Path

from code_graph_service.core import CodeGraphService, DocStatus, Scope, SymbolKind
from code_graph_service.domain.doc_discovery import discover_documentation_files
from code_graph_service.domain.symbol_resolve import resolve_linked_symbol
from code_graph_service.testing import InMemoryStore

SCOPE = Scope("t", "w", "human-docs")


AUTH_SOURCE = '''\
def login(user, password):
    return check_password(password)

def check_password(password):
    return len(password) > 8
'''


def _ingest_auth(svc: CodeGraphService) -> None:
    svc.ingest_file(
        SCOPE,
        "test",
        "c1",
        "k-auth",
        {"file_path": "src/auth.py", "source": AUTH_SOURCE, "language": "python"},
    )


def test_discover_documentation_files_by_wildcard(tmp_path: Path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# A\n", encoding="utf-8")
    (tmp_path / "docs" / "nested").mkdir()
    (tmp_path / "docs" / "nested" / "b.md").write_text("# B\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "c.md").write_text("# C\n", encoding="utf-8")
    (tmp_path / "readme.md").write_text("# root\n", encoding="utf-8")
    (tmp_path / "skip").mkdir()
    (tmp_path / "skip" / "x.md").write_text("# X\n", encoding="utf-8")

    found = discover_documentation_files(
        tmp_path,
        match_globs=["**/*.md"],
        exclude_dirs=["skip"],
        exclude_globs=[],
    )
    rels = {f.relative_path for f in found}
    assert rels == {"docs/a.md", "docs/nested/b.md", "src/c.md", "readme.md"}


def test_discover_empty_match_disables(tmp_path: Path):
    (tmp_path / "a.md").write_text("# A\n", encoding="utf-8")
    assert discover_documentation_files(tmp_path, match_globs=[]) == []


def test_resolve_qualified_name_and_path_form():
    store = InMemoryStore()
    svc = CodeGraphService(store)
    _ingest_auth(svc)

    by_qn = resolve_linked_symbol(store, SCOPE, "src.auth.login")
    assert by_qn is not None
    assert by_qn.name == "login"

    by_path = resolve_linked_symbol(store, SCOPE, "src/auth.py::login")
    assert by_path is not None
    assert by_path.id == by_qn.id

    assert resolve_linked_symbol(store, SCOPE, "missing.fn") is None
    assert resolve_linked_symbol(store, SCOPE, "src/auth.py::nope") is None


def test_upsert_human_documentation_links_and_skips_unresolved():
    store = InMemoryStore()
    svc = CodeGraphService(store)
    _ingest_auth(svc)

    login = store.get_symbol_by_qualified_name(SCOPE, "src.auth.login")
    assert login is not None

    result = svc.upsert_human_documentation(
        SCOPE,
        doc_id="doc-login",
        relative_path="docs/login.md",
        body="Login rules.",
        title="Login",
        linked_symbol_tokens=["src.auth.login", "missing.fn", "src/auth.py::check_password"],
    )
    assert result["doc_symbol_id"] == "doc:human:human-docs:doc-login"
    assert login.id in result["linked_symbol_ids"]
    assert "missing.fn" in result["unresolved_tokens"]
    assert result["edges_written"] == 2

    human = store.get_symbol(result["doc_symbol_id"], SCOPE)
    assert human.kind == SymbolKind.DOCUMENTATION
    assert human.doc_status == DocStatus.HUMAN

    edges = [e for e in store.list_edges(SCOPE) if e.rel_type == "DOCUMENTED_BY" and e.target_id == human.id]
    sources = {e.source_id for e in edges}
    assert login.id in sources
    check = store.get_symbol_by_qualified_name(SCOPE, "src.auth.check_password")
    assert check is not None and check.id in sources


def test_human_doc_id_distinct_from_living_doc():
    store = InMemoryStore()
    svc = CodeGraphService(store)
    _ingest_auth(svc)

    login = store.get_symbol_by_qualified_name(SCOPE, "src.auth.login")
    living_id = f"doc:{SCOPE.project_id}:src.auth.login"
    living = store.get_symbol(living_id, SCOPE)
    assert living.doc_status == DocStatus.GENERATED

    human = svc.upsert_human_documentation(
        SCOPE,
        doc_id="doc-login",
        relative_path="docs/login.md",
        body="Human login doc.",
        linked_symbol_tokens=["src.auth.login"],
    )
    assert human["doc_symbol_id"] != living_id
    assert store.get_symbol(human["doc_symbol_id"], SCOPE).id != living.id

    documented = [
        e
        for e in store.list_edges(SCOPE)
        if e.rel_type == "DOCUMENTED_BY" and e.source_id == login.id
    ]
    targets = {e.target_id for e in documented}
    assert living_id in targets
    assert human["doc_symbol_id"] in targets


def test_md_not_in_source_discovery(tmp_path: Path):
    from code_graph_service.domain.repo_discovery import discover_source_files

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# A\n", encoding="utf-8")
    (tmp_path / "a.py").write_text("x=1\n", encoding="utf-8")
    found = discover_source_files(tmp_path, include_extensions=[".py"], exclude_dirs=[], exclude_globs=[])
    assert {f.relative_path for f in found} == {"a.py"}
