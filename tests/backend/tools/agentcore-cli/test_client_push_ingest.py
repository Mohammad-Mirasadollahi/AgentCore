"""Tests for client content-push ingest (no on-server tree)."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

import pytest

from code_graph_service.core import CodeGraphService, Scope
from code_graph_service.domain.enums import SymbolKind
from code_graph_service.domain.hashing import content_hash
from code_graph_service.testing import InMemoryStore

from agentcore_cli.connect_flow.client_push import build_push_files


def test_ingest_pushed_sources_indexes_without_disk_root():
    service = CodeGraphService(InMemoryStore())
    scope = Scope("t", "w", "push")
    result = service.ingest_pushed_sources(
        scope,
        "tester",
        "corr-1",
        "push-key-1",
        {
            "files": [
                {
                    "file_path": "src/a.py",
                    "source": "def alpha():\n    return 1\n",
                    "language": "python",
                }
            ],
            "present_paths": ["src/a.py"],
            "include_outcomes": True,
        },
    )
    assert result.files_ingested == 1
    assert result.files_failed == 0
    names = {s.name for s in service.store.list_symbols(scope)}
    assert "alpha" in names


def test_ingest_pushed_sources_prunes_missing_present_paths():
    service = CodeGraphService(InMemoryStore())
    scope = Scope("t", "w", "prune")
    service.ingest_pushed_sources(
        scope,
        "tester",
        "corr-1",
        "push-key-1",
        {
            "files": [
                {"file_path": "a.py", "source": "def a():\n    return 1\n", "language": "python"},
                {"file_path": "b.py", "source": "def b():\n    return 2\n", "language": "python"},
            ],
            "present_paths": ["a.py", "b.py"],
        },
    )
    service.ingest_pushed_sources(
        scope,
        "tester",
        "corr-2",
        "push-key-2",
        {
            "files": [],
            "present_paths": ["a.py"],
        },
    )
    files = {
        s.file_path
        for s in service.store.list_symbols(scope)
        if s.kind == SymbolKind.FILE
    }
    assert files == {"a.py"}


def test_build_push_files_skips_unchanged_hashes(tmp_path: Path):
    (tmp_path / "agentcore.sync.yaml").write_text(
        "exclude_dirs: []\ninclude_extensions: [.py]\n",
        encoding="utf-8",
    )
    src = tmp_path / "src"
    src.mkdir()
    body = "def alpha():\n    return 1\n"
    (src / "a.py").write_text(body, encoding="utf-8")
    digest = content_hash(body, "python")["hash"]
    args = Namespace(
        exclude_dir=[],
        include_path=[],
        include_ext=[],
        max_files=50,
    )
    files, present, skipped = build_push_files(
        tmp_path,
        args,
        remote_hashes={"src/a.py": digest},
    )
    assert present == ["src/a.py"]
    assert files == []
    assert skipped == 1

    files2, _, skipped2 = build_push_files(tmp_path, args, remote_hashes={})
    assert len(files2) == 1
    assert files2[0]["file_path"] == "src/a.py"
    assert skipped2 == 0


def test_ingest_pushed_sources_rejects_path_traversal():
    from code_graph_service.domain.errors import ValidationError

    service = CodeGraphService(InMemoryStore())
    scope = Scope("t", "w", "sec")
    try:
        service.ingest_pushed_sources(
            scope,
            "tester",
            "corr",
            "key",
            {
                "files": [
                    {
                        "file_path": "../etc/passwd",
                        "source": "x = 1\n",
                        "language": "python",
                    }
                ],
            },
        )
        raised = False
    except ValidationError:
        raised = True
    assert raised


def test_ingest_pushed_sources_rejects_absolute_path():
    from code_graph_service.domain.errors import ValidationError

    service = CodeGraphService(InMemoryStore())
    scope = Scope("t", "w", "sec2")
    try:
        service.ingest_pushed_sources(
            scope,
            "tester",
            "corr",
            "key",
            {"files": [{"file_path": "/tmp/x.py", "source": "x=1\n", "language": "python"}]},
        )
        raised = False
    except ValidationError:
        raised = True
    assert raised


def test_ingest_pushed_sources_soft_fails_oversize_body():
    service = CodeGraphService(InMemoryStore())
    scope = Scope("t", "w", "sec3")
    big = "x" * 5000
    result = service.ingest_pushed_sources(
        scope,
        "tester",
        "corr",
        "key",
        {
            "files": [{"file_path": "a.py", "source": big, "language": "python"}],
            "max_file_bytes": 1024,
            "include_outcomes": True,
        },
    )
    assert result.files_ingested == 0
    assert result.files_failed == 1


def test_run_ingest_push_uses_http(monkeypatch):
    """Content-push always uses HTTP when graph_url + token are set (SSH removed)."""
    from agentcore_cli.connect_config import ConnectSettings
    from agentcore_cli.connect_flow import client_push as cp

    seen: list[str] = []

    def fake_http(settings, args, body):
        seen.append("http")
        return {"files_ingested": 0, "files_failed": 0}

    monkeypatch.setattr(cp, "_run_ingest_push_http", fake_http)
    settings = ConnectSettings(
        graph_url="http://g.internal:8080",
        api_token="tokentokentoken12",
    )
    out = cp._run_ingest_push(settings, Namespace(sync_mode=""), {"files": []})
    assert seen == ["http"]
    assert out["files_failed"] == 0


def test_run_ingest_push_without_graph_url_exits_with_hint():
    """No graph_url → clear SystemExit, never a silent push."""
    from agentcore_cli.connect_config import ConnectSettings
    from agentcore_cli.connect_flow import client_push as cp

    settings = ConnectSettings(graph_url="", api_token="")
    with pytest.raises(SystemExit, match="graph_url"):
        cp._run_ingest_push(settings, Namespace(sync_mode=""), {"files": []})


def test_client_push_sync_without_graph_url_exits_with_https_hint(tmp_path: Path):
    """client_push_sync must fail closed (mentioning graph_url/HTTPS)."""
    from agentcore_cli.connect_config import ConnectSettings
    from agentcore_cli.connect_flow.client_push import client_push_sync

    settings = ConnectSettings(graph_url="", api_token="", tenant="t", workspace="w", project="p")
    with pytest.raises(SystemExit, match="graph_url"):
        client_push_sync(settings, Namespace(), work=tmp_path)


def test_client_push_sync_no_transport_exits_with_https_hint(tmp_path: Path):
    from agentcore_cli.connect_config import ConnectSettings
    from agentcore_cli.connect_flow.client_push import client_push_sync

    settings = ConnectSettings(graph_url="", api_token="")
    with pytest.raises(SystemExit, match="HTTPS"):
        client_push_sync(settings, Namespace(), work=tmp_path)


def test_build_push_docs_includes_frontmatter_doc(tmp_path: Path):
    from agentcore_cli.connect_flow.client_push import _batches, build_push_docs

    (tmp_path / "agentcore.sync.yaml").write_text(
        "code:\n  exclude: []\ndocs:\n  match:\n    - '**/*.md'\n  exclude: []\n",
        encoding="utf-8",
    )
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "note.md").write_text(
        "---\n"
        "doc_id: ac.doc.test.note\n"
        "title: Note\n"
        "doc_type: note\n"
        "status: active\n"
        "schema_version: '1.0'\n"
        "owner: tests\n"
        "summary: test\n"
        "tags: [test]\n"
        "phase: test\n"
        "canonical_path: docs/note.md\n"
        "---\n"
        "\n"
        "# Note\n",
        encoding="utf-8",
    )
    args = Namespace(exclude_dir=[], include_path=[], include_ext=[], max_files=50)
    docs = build_push_docs(tmp_path, args)
    assert any(d["doc_id"] == "ac.doc.test.note" for d in docs)
    batches = _batches([], ["src/a.py"], docs=docs)
    assert len(batches) == 1
    assert batches[0]["docs"]
    assert batches[0]["present_paths"] == ["src/a.py"]


def test_fetch_remote_file_hashes_prefers_http(monkeypatch):
    import sys
    from types import ModuleType

    from agentcore_cli.connect_config import ConnectSettings
    from agentcore_cli.connect_flow import client_push as cp

    fake = ModuleType("httpx")

    class _Resp:
        status_code = 200

        @staticmethod
        def json():
            return {"hashes": {"a.py": "abc"}}

    def get(url, headers=None, timeout=None):
        assert "file-hashes" in url
        assert headers["Authorization"].startswith("Bearer ")
        return _Resp()

    fake.get = get  # type: ignore[attr-defined]
    fake.HTTPError = Exception  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "httpx", fake)

    settings = ConnectSettings(
        graph_url="http://g.internal:8080",
        api_token="tokentokentoken12",
        project="p",
        tenant="t",
        workspace="w",
    )
    assert cp._graph_http_ready(settings)
    hashes = cp.fetch_remote_file_hashes(settings, Namespace(project="p"))
    assert hashes == {"a.py": "abc"}


def test_cmd_ingest_push_applies_docs(monkeypatch):
    import io
    import sys

    from agentcore_cli.commands import ingest_push as mod

    class _Svc:
        def ingest_pushed_sources(self, *_a, **_k):
            class _R:
                def to_dict(self):
                    return {"files_ingested": 0, "files_failed": 0}

            return _R()

        def upsert_human_documentation(self, *_a, **_k):
            return None

    monkeypatch.setattr(mod, "_graph_service", lambda: _Svc())
    monkeypatch.setattr(
        mod,
        "_graph_scope",
        lambda *_a, **_k: Namespace(project_id="p", tenant_id="t", workspace_id="w"),
    )
    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO(
            '{"files":[],"docs":[{"doc_id":"ac.doc.x","relative_path":"docs/x.md",'
            '"body":"# X","title":"X","linked_symbol_tokens":[]}]}'
        ),
    )
    printed: list[dict] = []
    monkeypatch.setattr(mod, "print_json", lambda obj: printed.append(obj))
    assert mod.cmd_ingest_push(Namespace(embedding_refresh_mode="touched")) == 0
    assert printed[0]["docs"]["docs_upserted"] == 1
