"""Live gate: RPM-session parallel ingest against Compose Neo4j.

Verifies auto file workers track RPM, LockedStore safety, and RpmSessionGate
start/end accounting while writing a real graph store.

Re-run:
  .venv/bin/python -m pytest \\
    tests/backend/services/code-graph-service/test_rpm_session_parallel_sync_live.py -m live -v
"""

from __future__ import annotations

import os
import re
import resource
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from urllib.request import Request, urlopen

import pytest

from code_graph_service.bootstrap import Settings, build_service
from code_graph_service.core import CodeGraphService, Scope
from code_graph_service.domain.embeddings import LocalEmbeddingStub
from code_graph_service.domain.enums import SymbolKind
from code_graph_service.llm_wiring import LlmBackedDocGenerator
from code_graph_service.locked_store import LockedStore, sync_max_file_workers
from code_graph_service.neo4j_store import Neo4jStore
from code_graph_service.postgres_store import PostgresStore
from llm_gateway import LiteLlmGateway, LlmGatewaySettings

from live_helpers import (
    NEO4J_BOLT_PORT,
    NEO4J_PASSWORD,
    NEO4J_USER,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    require_tcp,
    skip_on_live_connect_error,
)

pytestmark = pytest.mark.live


def _settings_rpm(rpm: int) -> LlmGatewaySettings:
    return LlmGatewaySettings(
        enabled=True,
        api_base="http://127.0.0.1:32400",
        api_base_override="",
        api_base_is_auto=True,
        api_key="",
        default_model="fake/model",
        timeout_seconds=30.0,
        num_retries=0,
        rpm=rpm,
        host="127.0.0.1",
        port=32400,
        drop_params=True,
        reasoning_enabled=False,
        reasoning_effort="",
    )


def _write_tree(root: Path, n_files: int) -> None:
    src = root / "src"
    src.mkdir(parents=True)
    for i in range(n_files):
        (src / f"mod_{i}.py").write_text(
            f"def fn_{i}(x):\n    return x + {i}\n",
            encoding="utf-8",
        )


@pytest.fixture
def local_litellm(monkeypatch):
    request_state = {"active": 0, "peak": 0, "released": False}
    request_condition = threading.Condition()

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length") or 0))
            with request_condition:
                request_state["active"] += 1
                request_state["peak"] = max(request_state["peak"], request_state["active"])
                if request_state["active"] >= 4:
                    request_state["released"] = True
                    request_condition.notify_all()
                else:
                    request_condition.wait_for(lambda: request_state["released"], timeout=10.0)
            time.sleep(0.6)
            with request_condition:
                request_state["active"] -= 1
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"{}")

        def log_message(self, _format, *_args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"

    class NetworkLiteLlm:
        drop_params = False

        @staticmethod
        def completion(**kwargs):
            request = Request(
                f"{kwargs['api_base']}/complete",
                data=b"{}",
                method="POST",
            )
            with urlopen(request, timeout=10.0):
                pass
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="live-doc"))],
                usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1, total_tokens=2),
                model=kwargs["model"],
                id=uuid.uuid4().hex,
            )

    monkeypatch.setitem(sys.modules, "litellm", NetworkLiteLlm())
    yield SimpleNamespace(base_url=base_url, request_state=request_state)
    server.shutdown()
    server.server_close()
    thread.join(timeout=2.0)


@pytest.fixture
def neo4j_service(monkeypatch, tmp_path: Path, local_litellm):
    require_tcp("127.0.0.1", NEO4J_BOLT_PORT)
    rpm = 4
    monkeypatch.setenv("AGENTCORE_LITELLM_RPM", str(rpm))
    monkeypatch.delenv("AGENTCORE_SYNC_MAX_FILE_WORKERS", raising=False)
    monkeypatch.setenv("AGENTCORE_LITELLM_DOCS_ENABLED", "true")
    monkeypatch.setenv("AGENTCORE_LITELLM_MODEL_DOCS", "fake/model")
    monkeypatch.setenv("AGENTCORE_LITELLM_DEFAULT_MODEL", "fake/model")

    try:
        store = Neo4jStore(
            uri=f"bolt://127.0.0.1:{NEO4J_BOLT_PORT}",
            user=NEO4J_USER,
            password=NEO4J_PASSWORD,
            ensure_schema=True,
        )
    except Exception as exc:  # noqa: BLE001
        skip_on_live_connect_error(exc)

    settings = _settings_rpm(rpm)
    settings = LlmGatewaySettings(**{**settings.__dict__, "api_base": local_litellm.base_url})
    gateway = LiteLlmGateway(settings=settings)
    service = CodeGraphService(
        LockedStore(store),
        docs=LlmBackedDocGenerator(gateway, settings=gateway.settings),
        embeddings=LocalEmbeddingStub(dims=16),
        llm=gateway,
    )
    scope = Scope("tenant-rpm-live", "ws-rpm-live", f"proj-{uuid.uuid4().hex[:10]}")
    tree = tmp_path / "repo"
    _write_tree(tree, n_files=4)
    yield service, scope, tree, gateway, rpm
    try:
        service.purge_scope(scope)
    except Exception:  # noqa: BLE001
        pass
    finally:
        store.close()


@pytest.fixture
def postgres_service(monkeypatch, tmp_path: Path, local_litellm):
    require_tcp("127.0.0.1", POSTGRES_PORT)
    rpm = 4
    monkeypatch.setenv("AGENTCORE_LITELLM_RPM", str(rpm))
    monkeypatch.delenv("AGENTCORE_SYNC_MAX_FILE_WORKERS", raising=False)
    monkeypatch.setenv("AGENTCORE_LITELLM_DOCS_ENABLED", "true")
    monkeypatch.setenv("AGENTCORE_LITELLM_MODEL_DOCS", "fake/model")
    monkeypatch.setenv("AGENTCORE_LITELLM_DEFAULT_MODEL", "fake/model")
    url = (
        f"postgresql://agentcore:{POSTGRES_PASSWORD}@127.0.0.1:{POSTGRES_PORT}/agentcore"
    )
    try:
        store = PostgresStore(url, ensure_schema=True)
    except Exception as exc:  # noqa: BLE001
        skip_on_live_connect_error(exc)
    settings = _settings_rpm(rpm)
    settings = LlmGatewaySettings(**{**settings.__dict__, "api_base": local_litellm.base_url})
    gateway = LiteLlmGateway(settings=settings)
    service = CodeGraphService(
        LockedStore(store),
        docs=LlmBackedDocGenerator(gateway, settings=gateway.settings),
        embeddings=LocalEmbeddingStub(dims=16),
        llm=gateway,
    )
    scope = Scope("tenant-rpm-pg-live", "ws-rpm-pg-live", f"proj-{uuid.uuid4().hex[:10]}")
    tree = tmp_path / "repo"
    _write_tree(tree, n_files=4)
    yield service, scope, tree, gateway, rpm
    try:
        service.purge_scope(scope)
    except Exception:  # noqa: BLE001
        pass


def test_auto_workers_follow_live_rpm(monkeypatch):
    monkeypatch.delenv("AGENTCORE_SYNC_MAX_FILE_WORKERS", raising=False)
    monkeypatch.setenv("AGENTCORE_LITELLM_RPM", "2")
    monkeypatch.setattr("code_graph_service.locked_store.os.cpu_count", lambda: 16)
    assert sync_max_file_workers() == 2


@pytest.mark.timeout(180)
def test_parallel_ingest_rpm_sessions_against_neo4j(neo4j_service, monkeypatch):
    service, scope, tree, gateway, rpm = neo4j_service
    monkeypatch.setattr("code_graph_service.locked_store.os.cpu_count", lambda: 8)
    workers = sync_max_file_workers()
    assert workers == min(8, rpm)

    peak_inflight = {"n": 0}
    violations = {"n": 0}
    stop = threading.Event()

    def _watch() -> None:
        while not stop.is_set():
            snap = gateway.rpm_sessions_snapshot()
            inflight = int(snap.get("inflight_count") or 0)
            starts = int(snap.get("starts_in_window") or 0)
            peak_inflight["n"] = max(peak_inflight["n"], inflight)
            if inflight > rpm or starts > rpm:
                violations["n"] += 1
            time.sleep(0.02)

    watcher = threading.Thread(target=_watch, daemon=True)
    watcher.start()
    try:
        result = service.ingest_repo(
            scope,
            "live-agent",
            f"corr-rpm-{uuid.uuid4().hex[:8]}",
            f"idem-rpm-{uuid.uuid4().hex}",
            {
                "root_path": str(tree),
                "include_extensions": [".py"],
                "max_files": 20,
                "include_outcomes": True,
            },
        )
    finally:
        stop.set()
        watcher.join(timeout=2.0)

    assert result.files_discovered == 4
    assert result.files_failed == 0
    assert result.files_ingested + result.files_skipped == 4
    assert result.symbols_indexed >= 4
    assert violations["n"] == 0

    snap = gateway.rpm_sessions_snapshot()
    assert snap["inflight_count"] == 0
    assert snap["rpm"] == rpm
    assert len(snap["history"]) >= 4
    assert all(h["status"] in {"ok", "error", "cancelled"} for h in snap["history"])
    assert peak_inflight["n"] >= 2

    symbols = service.store.list_symbols(scope)
    files = [s for s in symbols if s.kind == SymbolKind.FILE]
    assert len(files) >= 4


@pytest.mark.timeout(180)
def test_parallel_ingest_rpm_sessions_against_postgres(postgres_service, monkeypatch):
    test_parallel_ingest_rpm_sessions_against_neo4j(postgres_service, monkeypatch)


@pytest.mark.timeout(180)
def test_cli_progress_reports_nonzero_live_rpm(
    neo4j_service,
    monkeypatch,
    capsys,
    tmp_path: Path,
):
    from agentcore_cli.commands.sync import _sync_one_root

    service, scope, tree, _gateway, _rpm = neo4j_service
    (tree / "agentcore.sync.yaml").write_text(
        "code:\n  exclude: []\ndocs:\n  match: []\n  exclude: []\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "agentcore_cli.sync_progress.progress_path",
        lambda root=None: tmp_path / "sync-progress.json",
    )
    args = SimpleNamespace(
        exclude_dir=[],
        include_path=[],
        include_ext=[],
        progress_interval=0.05,
        max_files=5,
    )

    _sync_one_root(svc=service, scope=scope, root_path=tree, args=args)

    output = capsys.readouterr().out
    assert re.search(r"rpm inflight [1-4]/4", output), output
    assert "starts 4/4" in output


@pytest.mark.timeout(300)
def test_production_build_sends_five_files_concurrently(
    monkeypatch,
    tmp_path: Path,
    local_litellm,
):
    require_tcp("127.0.0.1", NEO4J_BOLT_PORT)
    monkeypatch.setenv("AGENTCORE_LITELLM_ENABLED", "true")
    monkeypatch.setenv("AGENTCORE_LITELLM_DOCS_ENABLED", "true")
    monkeypatch.setenv("AGENTCORE_LITELLM_DEFAULT_MODEL", "fake/model")
    monkeypatch.setenv("AGENTCORE_LITELLM_MODEL_DOCS", "fake/model")
    monkeypatch.setenv("AGENTCORE_LITELLM_API_BASE", local_litellm.base_url)
    monkeypatch.setenv("AGENTCORE_LITELLM_RPM", "5")
    monkeypatch.setenv("AGENTCORE_EMBEDDING_PROVIDER", "local_bge")
    monkeypatch.setenv("AGENTCORE_EMBEDDING_LOCAL_ENABLED", "true")
    monkeypatch.setenv("AGENTCORE_EMBEDDING_CACHE_DIR", "/opt/agentcore-models")
    monkeypatch.setenv("AGENTCORE_EMBEDDING_DEVICE", "cpu")
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setenv("TRANSFORMERS_OFFLINE", "1")
    settings = Settings(
        store_backend="neo4j",
        database_url="",
        neo4j_uri=f"bolt://127.0.0.1:{NEO4J_BOLT_PORT}",
        neo4j_user=NEO4J_USER,
        neo4j_password=NEO4J_PASSWORD,
        neo4j_database="neo4j",
    )
    service = build_service(settings)
    scope = Scope("tenant-rpm-production", "ws-rpm-production", f"proj-{uuid.uuid4().hex[:10]}")
    tree = tmp_path / "production-repo"
    _write_tree(tree, n_files=5)
    peak_inflight = 0
    stop = threading.Event()

    def watch_sessions() -> None:
        nonlocal peak_inflight
        while not stop.is_set():
            peak_inflight = max(
                peak_inflight,
                int(service.llm_sessions_snapshot().get("inflight_count") or 0),
            )
            time.sleep(0.01)

    watcher = threading.Thread(target=watch_sessions, daemon=True)
    watcher.start()
    wall_start = time.perf_counter()
    cpu_start = time.process_time()
    try:
        try:
            result = service.ingest_repo(
                scope,
                "live-agent",
                f"corr-production-{uuid.uuid4().hex[:8]}",
                f"idem-production-{uuid.uuid4().hex}",
                {
                    "root_path": str(tree),
                    "include_extensions": [".py"],
                    "max_files": 5,
                    "include_outcomes": True,
                },
            )
        finally:
            stop.set()
            watcher.join(timeout=2.0)
        wall_seconds = time.perf_counter() - wall_start
        cpu_seconds = time.process_time() - cpu_start
        assert result.files_discovered == 5
        assert result.files_ingested == 5
        assert result.files_failed == 0
        assert local_litellm.request_state["peak"] >= 4
        assert peak_inflight >= 4
        assert len(service.llm_sessions_snapshot()["history"]) >= 5
        print(
            f"resource metrics: wall={wall_seconds:.2f}s cpu={cpu_seconds:.2f}s "
            f"cpu/wall={cpu_seconds / max(wall_seconds, 0.001):.2f} "
            f"rss_kib={resource.getrusage(resource.RUSAGE_SELF).ru_maxrss} "
            f"http_peak={local_litellm.request_state['peak']} rpm_peak={peak_inflight}"
        )
    finally:
        try:
            service.purge_scope(scope)
        finally:
            service.store.close()
