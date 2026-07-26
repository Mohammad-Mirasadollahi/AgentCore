"""Live challenging probes for docs_drift_check vs real Neo4j DOCUMENTED_BY.

Requires AGENTCORE_* env (postgres + neo4j) matching the running AgentCore stack.
"""

from __future__ import annotations

import os
import uuid

import pytest

from mcp_gateway_service.backends import docs as docs_backend
from mcp_gateway_service.backends.platform import PlatformBackends
from mcp_gateway_service.server import McpGateway


def _live_env_ready() -> bool:
    return bool(
        os.environ.get("AGENTCORE_DATABASE_URL")
        and os.environ.get("AGENTCORE_NEO4J_URI")
        and os.environ.get("AGENTCORE_MCP_GRAPH_MODE", "neo4j") == "neo4j"
    )


@pytest.fixture(scope="module")
def live_backends() -> PlatformBackends:
    if not _live_env_ready():
        pytest.skip("live AgentCore postgres/neo4j env not configured")
    env = {
        **os.environ,
        "AGENTCORE_MCP_STORE_MODE": os.environ.get("AGENTCORE_MCP_STORE_MODE", "postgres"),
        "AGENTCORE_MCP_GRAPH_MODE": "neo4j",
        "AGENTCORE_MCP_GRAPH_SEED": "false",
    }
    backends = PlatformBackends.from_env(env)
    yield backends
    backends.close()


@pytest.fixture(scope="module")
def live_scope() -> dict[str, str]:
    return {
        "tenant_id": os.environ.get("AGENTCORE_TENANT_ID", "mir"),
        "workspace_id": os.environ.get("AGENTCORE_WORKSPACE_ID", "dev"),
        "project_id": os.environ.get("AGENTCORE_PROJECT_ID", "agentcore"),
    }


@pytest.mark.live
def test_live_drift_human_linked_short_name_no_false_missing(
    live_backends: PlatformBackends,
    live_scope: dict[str, str],
) -> None:
    """Challenge 1: short name + wrong file_path must not invent missing_doc."""
    result = docs_backend.docs_drift_check(
        live_backends,
        {
            "symbol": "build_symbol_doc_coverage",
            "file_path": "this/path/does/not/exist.py",
        },
        scope=live_scope,
        correlation_id=f"live-drift-human-{uuid.uuid4().hex[:8]}",
        base={"backend": "in_process"},
    )
    assert result["drift"] is False, result
    assert result["findings"] == []
    assert result["lookup_source"] == "graph"
    assert any(str(x.get("target_id", "")).startswith("doc:human:") for x in result["documented_by"])


@pytest.mark.live
def test_live_drift_quality_audit_human_link(
    live_backends: PlatformBackends,
    live_scope: dict[str, str],
) -> None:
    """Challenge 2: second real linked symbol from follow-up Task doc."""
    result = docs_backend.docs_drift_check(
        live_backends,
        {
            "symbol": "quality_audit",
            "file_path": "backend/services/mcp-gateway-service/src/mcp_gateway_service/backends/quality.py",
        },
        scope=live_scope,
        correlation_id=f"live-drift-qa-{uuid.uuid4().hex[:8]}",
        base={"backend": "in_process"},
    )
    assert result["drift"] is False, result
    assert result["lookup_source"] == "graph"
    targets = {str(x.get("target_id") or "") for x in result["documented_by"]}
    assert any("followup-task-lifecycle" in t or "automated-followup" in t or t.startswith("doc:human:") for t in targets)


@pytest.mark.live
def test_live_drift_idempotent_no_orphan_spam(
    live_backends: PlatformBackends,
    live_scope: dict[str, str],
) -> None:
    """Challenge 3: two calls must stay clean and not grow docs-sync orphans."""
    docs_scope = live_backends.docs_scope(live_scope)
    before = len(live_backends.docs.store.list_symbols(docs_scope))
    for i in range(2):
        result = docs_backend.docs_drift_check(
            live_backends,
            {"symbol": "build_symbol_doc_coverage", "file_path": f"junk/{i}.py"},
            scope=live_scope,
            correlation_id=f"live-drift-idem-{i}-{uuid.uuid4().hex[:8]}",
            base={"backend": "in_process"},
        )
        assert result["drift"] is False
        assert result["lookup_source"] == "graph"
    after = len(live_backends.docs.store.list_symbols(docs_scope))
    assert after == before


@pytest.mark.live
def test_live_drift_unknown_symbol_still_reports_missing(
    live_backends: PlatformBackends,
    live_scope: dict[str, str],
) -> None:
    """Challenge 4: truly unknown symbol still takes docs-sync path → missing_doc."""
    unique = f"never_linked_symbol_{uuid.uuid4().hex[:10]}"
    result = docs_backend.docs_drift_check(
        live_backends,
        {"symbol": unique, "file_path": f"src/{unique}.py"},
        scope=live_scope,
        correlation_id=f"live-drift-missing-{uuid.uuid4().hex[:8]}",
        base={"backend": "in_process"},
    )
    assert result["drift"] is True
    assert result["findings"]
    assert result.get("lookup_source") == "docs_sync"
    assert result["findings"][0]["drift_type"] == "missing_doc"


@pytest.mark.live
def test_live_mcp_gateway_tool_surface_drift_and_generation(
    live_backends: PlatformBackends,
    live_scope: dict[str, str],
) -> None:
    """Challenge 5: full MCP tool path — drift + generation_context agree on human layer."""
    gw = McpGateway(
        profile_id=os.environ.get("AGENTCORE_USAGE_PROFILE", "programming-cursor-mcp"),
        tenant_id=live_scope["tenant_id"],
        workspace_id=live_scope["workspace_id"],
        project_id=live_scope["project_id"],
        backends=live_backends,
    )
    drift = gw.call_tool(
        "agentcore_docs_drift_check",
        {
            "symbol": "build_symbol_doc_coverage",
            "file_path": "backend/services/code-graph-service/src/code_graph_service/domain/hybrid_doc_coverage.py",
        },
    )
    payload = drift["structuredContent"]
    assert payload["drift"] is False, payload
    assert payload["lookup_source"] == "graph"

    ctx = gw.call_tool(
        "agentcore_code_graph_generation_context",
        {
            "qualified_name": (
                "backend.services.code-graph-service.src.code_graph_service."
                "domain.hybrid_doc_coverage.build_symbol_doc_coverage"
            )
        },
    )
    hybrid = ctx["structuredContent"]["hybrid_documentation"]
    assert hybrid["preferred_layer"] == "human"
    assert hybrid["coverage"]["human"] is True
