#!/usr/bin/env python3
"""Live MCP HTTP probe: unused_candidates on a tiny ingested fixture.

Uses a dedicated project scope so Neo4j load stays small (full AgentCore index
is too large for a bounded HTTP timeout). Requires ``agentcore service`` up.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx
import pytest
from usage_profile.mcp_tokens import mint_connect_token

ROOT = Path(__file__).resolve().parents[3]
SECRET = ROOT / ".agentcore" / "mcp-http.secret"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "dead_code_sample" / "live_main.py"
NOISE = Path(__file__).resolve().parent / "fixtures" / "other_noise" / "noise.py"
MCP_URL = os.environ.get("AGENTCORE_MCP_HTTP_PUBLIC_URL", "http://127.0.0.1:32500").rstrip("/")
if not MCP_URL.endswith("/mcp"):
    MCP_URL = f"{MCP_URL}/mcp"

TENANT = "mir"
WORKSPACE = "dev"
PROJECT = "deadcode-live"
PATH_PREFIX = "fixtures/dead_code_sample"


def _payload(result: dict) -> dict:
    sc = result.get("structuredContent")
    if isinstance(sc, dict):
        return sc
    for part in result.get("content") or []:
        if part.get("type") == "text":
            return json.loads(part.get("text") or "{}")
    raise AssertionError(f"no structured payload: {result!r}")


@pytest.mark.live
def test_live_unused_candidates_via_mcp_http():
    if not SECRET.is_file():
        pytest.skip(f"missing MCP secret at {SECRET}")
    if not FIXTURE.is_file():
        pytest.skip(f"missing fixture {FIXTURE}")
    if not NOISE.is_file():
        pytest.skip(f"missing fixture {NOISE}")

    secret = SECRET.read_text(encoding="utf-8").strip()
    os.environ["AGENTCORE_MCP_TOKEN_SECRET"] = secret
    token = mint_connect_token(
        tenant_id=TENANT, workspace_id=WORKSPACE, project_id=PROJECT, ttl_seconds=3600
    )
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def rpc(method: str, params: dict | None = None, rid: int = 1) -> dict:
        response = httpx.post(
            MCP_URL,
            headers=headers,
            json={"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}},
            timeout=120.0,
        )
        response.raise_for_status()
        body = response.json()
        assert "error" not in body, body
        return body

    init = rpc(
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "live-unused-candidates", "version": "0"},
        },
        1,
    )
    assert "result" in init, init

    listed = rpc("tools/list", {}, 2)
    names = {t.get("name") for t in (listed.get("result") or {}).get("tools") or []}
    assert names == {"mcp_search_tools", "mcp_execute_tool"}, names

    search = rpc(
        "tools/call",
        {
            "name": "mcp_search_tools",
            "arguments": {"query": "unused candidates ingest file", "limit": 15},
        },
        3,
    )
    search_payload = _payload(search.get("result") or {})
    hits = list(search_payload.get("results") or [])
    by_name = {str(h.get("tool_name") or ""): h for h in hits if isinstance(h, dict)}
    assert "agentcore_code_graph_unused_candidates" in by_name, search_payload
    assert "agentcore_code_graph_ingest_file" in by_name, search_payload
    server_name = str(by_name["agentcore_code_graph_unused_candidates"].get("server_name") or "")
    assert server_name

    def execute(tool_name: str, tool_args: dict, rid: int) -> dict:
        call = rpc(
            "tools/call",
            {
                "name": "mcp_execute_tool",
                "arguments": {
                    "tool_name": tool_name,
                    "server_name": server_name,
                    "arguments": tool_args,
                },
            },
            rid,
        )
        return _payload(call.get("result") or {})

    ingest = execute(
        "agentcore_code_graph_ingest_file",
        {
            "file_path": "fixtures/dead_code_sample/live_main.py",
            "language": "python",
            "source": FIXTURE.read_text(encoding="utf-8"),
        },
        4,
    )
    assert ingest.get("ok") is not False, ingest

    noise = execute(
        "agentcore_code_graph_ingest_file",
        {
            "file_path": "fixtures/other_noise/noise.py",
            "language": "python",
            "source": NOISE.read_text(encoding="utf-8"),
        },
        5,
    )
    assert noise.get("ok") is not False, noise

    payload = execute(
        "agentcore_code_graph_unused_candidates",
        {
            "scope_mode": "project_scan",
            "path_prefix": PATH_PREFIX,
            "min_confidence": 0.5,
            "max_results": 20,
            "include_uncertain": True,
            "triage": True,
        },
        6,
    )
    assert payload.get("scope_mode") == "project_scan", payload
    assert payload.get("path_prefix") == PATH_PREFIX, payload
    assert "index_coverage" in payload, payload
    hints = payload.get("kpi_hints") or {}
    assert "dead_code_candidates_surfaced" in hints
    assert "dead_code_candidates_skipped_uncertain" in hints
    assert hints.get("dead_code_candidates_resolved") == 0
    assert payload.get("triage_enabled") is True
    assert payload.get("triage_engine") == "local_rules"

    rows = list(payload.get("candidates") or []) + list(payload.get("skipped_uncertain") or [])
    assert rows, f"expected scored rows after fixture ingest: {payload}"
    assert all(
        str(r.get("path") or "").startswith(PATH_PREFIX) for r in rows
    ), {"rows": [{"symbol": r.get("symbol"), "path": r.get("path")} for r in rows]}
    assert not any("outside_orphan" in str(r.get("symbol") or "") for r in rows)

    orphan_rows = [
        r
        for r in rows
        if "old_helper_orphan" in str(r.get("symbol") or "")
        or str(r.get("symbol") or "").endswith("old_helper_orphan")
    ]
    assert orphan_rows, {
        "rows": [
            {
                "symbol": r.get("symbol"),
                "finding_kind": r.get("finding_kind"),
                "score": r.get("score"),
                "safe_to_delete": r.get("safe_to_delete"),
            }
            for r in rows
        ]
    }
    orphan = orphan_rows[0]
    assert orphan.get("finding_kind") == "unused_symbol"
    assert float(orphan.get("score") or 0) >= 0.5
    # Fresh ingest stamps updated_at≈now → recent_file_cap (score≤0.55, not safe_to_delete).
    assert "recent_file_cap" in (orphan.get("blockers") or []) or float(orphan.get("score") or 0) <= 0.55
    assert orphan.get("safe_to_delete") is not True

    # Entrypoint main / helper_used must not be safe_to_delete.
    live_safe = [
        r
        for r in (payload.get("candidates") or [])
        if any(x in str(r.get("symbol") or "") for x in ("live_main.main", "helper_used"))
        and r.get("safe_to_delete")
    ]
    assert not live_safe

    out = {
        "http_mcp_ok": True,
        "server_name": server_name,
        "project_id": PROJECT,
        "path_prefix": payload.get("path_prefix"),
        "graph_mode": payload.get("graph_mode"),
        "index_coverage": payload.get("index_coverage"),
        "kpi_hints": hints,
        "row_count": len(rows),
        "orphan": {
            "symbol": orphan.get("symbol"),
            "path": orphan.get("path"),
            "finding_kind": orphan.get("finding_kind"),
            "score": orphan.get("score"),
            "confidence": orphan.get("confidence"),
            "safe_to_delete": orphan.get("safe_to_delete"),
            "blockers": orphan.get("blockers"),
            "evidence_kinds": [e.get("kind") for e in (orphan.get("evidence") or [])],
        },
        "triage_engine": payload.get("triage_engine"),
        "outside_orphan_excluded": True,
    }
    artifact = ROOT / "tests" / "artifacts" / "code-graph-live" / "unused-candidates-live.json"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    sys.path[:0] = [str(ROOT / "backend" / "packages")]
    test_live_unused_candidates_via_mcp_http()
    print("HTTP_MCP_UNUSED_CANDIDATES_OK")
