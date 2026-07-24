---
doc_id: ac.doc.ckg.code-intel-contracts
title: 25 - Code Intelligence Enhancements Data Contracts And Events
doc_type: contract
status: draft
schema_version: '1.0'
owner: code-graph-lead
summary: HTTP, MCP, and payload contracts for explore packs and change-risk reports, plus
  edge metadata shapes for ROUTES_TO and TESTED_BY.
tags:
- code-intelligence
- contracts
- mcp
- api
phase: 07-code-knowledge-graph
canonical_path: docs/07-code-knowledge-graph/25-code-intelligence-enhancements-data-contracts-and-events.md
lifecycle_lane: current
concern_lane: contract
audience_lane:
- platform-engineering
- agents
authority: normative
visibility: internal
linked_symbols: []
related_docs:
- ac.doc.ckg.code-intel-feature-spec
- ac.doc.ckg.code-intel-hld
- backend/services/code-graph-service/docs/phase-7-api-contract.md
doc_version: 1.0.0
audience:
- engineer
- agent
primary_entities:
- ExplorePack
- ChangeRiskReport
- CODE_REL
relations_declared:
- type: depends_on
  target: ac.doc.ckg.code-intel-feature-spec
- type: complements
  target: backend/services/code-graph-service/docs/phase-7-api-contract.md
chunk_hints:
  strategy: heading_h2
  max_tokens: 700
  overlap_tokens: 48
language: en
security_classification: internal
---

# 25 - Code Intelligence Enhancements Data Contracts And Events

## Purpose

Wire-level shapes for Code Intelligence Enhancements. Service contract file
remains authoritative for Phase 7 paths; this document owns explore /
detect-changes payloads and enrichment edge metadata.

## Scope Headers

Unchanged from Phase 7: `X-Tenant-Id`, `X-Workspace-Id`, project path param,
`Idempotency-Key` on ingest writes, `X-Actor-Id` on commands.

## HTTP Endpoints

| Method | Path | Body | Response |
| --- | --- | --- | --- |
| POST | `/api/v1/projects/{project_id}/graph/explore` | `ExploreRequest` | `ExplorePack` |
| POST | `/api/v1/projects/{project_id}/graph/detect-changes` | `DetectChangesRequest` | `ChangeRiskReport` |
| POST | `/api/v1/projects/{project_id}/graph/architecture-overview` | `{ "top_n"?: number }` | Architecture report |
| POST | `/api/v1/projects/{project_id}/graph/path` | `{ "from", "to", "max_depth"? }` | Shortest path |
| POST | `/api/v1/projects/{project_id}/graph/search:hybrid` | `{ "query", "top_k"? }` | RRF-ranked hits |
| POST | `/api/v1/projects/{project_id}/graph/pending-sync` | `{ "file_path"? , "file_paths"? }` | Freshness / pending (batch preferred) |
| GET | `/api/v1/projects/{project_id}/graph/freshness` | — | Freshness status |

### MCP tools (usage profile)

| Tool | maps_to |
| --- | --- |
| `agentcore_code_graph_explore` | `code_graph.explore` |
| `agentcore_code_graph_detect_changes` | `code_graph.detect_changes` |
| `agentcore_code_graph_architecture_overview` | `code_graph.architecture_overview` |
| `agentcore_code_graph_path` | `code_graph.path` |
| `agentcore_code_graph_hybrid_search` | `code_graph.hybrid_search` |
| `agentcore_code_graph_freshness` | `code_graph.freshness` |

### ExploreRequest

```json
{
  "query": "string",
  "top_k": 12,
  "max_depth": 2,
  "budget_chars": null
}
```

Constraints: `top_k` 1–40; `max_depth` 1–4; `budget_chars` optional 2000–100000.

### ExplorePack (response)

```json
{
  "query": "string",
  "budget_chars": 28000,
  "used_chars": 12000,
  "seed_ids": ["sym:…"],
  "call_path_ids": ["sym:…"],
  "terms": ["AuthService"],
  "notes": ["budget_collapse:…"],
  "edge_confidence_policy": "exact|probable|ambiguous|unresolved on CALLS; …",
  "sections": [
    {
      "file_path": "src/auth.py",
      "skeletonized": false,
      "symbols": [
        {
          "id": "sym:…",
          "name": "login",
          "qualified_name": "…",
          "kind": "function",
          "signature": "def login(…)",
          "body": "…",
          "render": "full",
          "on_spine": true,
          "score": 1.2,
          "confidence_note": "…"
        }
      ]
    }
  ]
}
```

`render` ∈ `full` | `signature`.

### DetectChangesRequest

```json
{
  "changed_files": ["src/auth.py"],
  "include_flows": true
}
```

### ChangeRiskReport (response)

```json
{
  "changed_files": ["src/auth.py"],
  "risk_score": 0.62,
  "risk_level": "high",
  "summary": "string",
  "changed_functions": [
    {
      "symbol_id": "sym:…",
      "qualified_name": "…",
      "file_path": "…",
      "risk_score": 0.62,
      "risk_level": "high",
      "caller_count": 3,
      "test_count": 0,
      "flow_count": 1
    }
  ],
  "review_priorities": [],
  "test_gaps": [],
  "affected_flows": [
    {
      "entry": "mod.main",
      "depth": 2,
      "file_count": 2,
      "criticality": 0.4,
      "path_ids": ["sym:…"]
    }
  ]
}
```

`risk_level` ∈ `low` | `medium` | `high` | `critical`.

## MCP Tools

| Tool name | maps_to | Required args |
| --- | --- | --- |
| `agentcore_code_graph_explore` | `code_graph.explore` | `query` |
| `agentcore_code_graph_detect_changes` | `code_graph.detect_changes` | `changed_files` |
| `agentcore_code_graph_callers` | `code_graph.callers` | `symbol_id` or `qualified_name` |
| `agentcore_code_graph_impact` | `code_graph.impact` | `symbol_id` or `qualified_name` |
| `agentcore_code_graph_community` | `code_graph.community` | `symbol_id` or `qualified_name` |

Profile: `backend/configs/usage-profiles/programming-cursor-mcp.json`.
Dispatch: `mcp_gateway_service.backends.dispatch`.

Agent guidance: prefer structural `callers` / directed `impact` / `community` for
fan-in and blast questions; use `explore` for semantic “how does X work”; use
`detect_changes` for review/PR deltas. Follow `escalate_hint` before raw Read.

See also Codebase-Memory hybrid pack `44`–`47`.

## Edge Metadata Contracts

### ROUTES_TO

```json
{
  "framework": "fastapi|flask_or_fastapi|django|express",
  "method": "GET|POST|…|ANY",
  "path": "/users/{id}",
  "handler": "get_user",
  "line": 12,
  "provenance": "framework_route"
}
```

### HTTP_CALLS / ASYNC_CALLS

```json
{
  "method": "GET|POST|…|ANY",
  "url_or_path": "/api/v1/users",
  "path": "/api/v1/users",
  "framework": "httpx|requests|fetch|axios|…",
  "line": 18,
  "provenance": "http_client_call"
}
```

### TESTED_BY

```json
{
  "reason": "file_stem|name_convention",
  "provenance": "test_convention"
}
```

## Events

Wave 1 does not introduce new outbox event types. Route/test enrichment occurs
inside `FileIngested` ingest transactions. Wave 2 may add:

- `CommunitiesRecomputed` (payload: algorithm, community_count, seed)
- `ArchitectureReportGenerated` (artifact ref)

Until then, clients must not depend on those types.

## Compatibility

- Additive endpoints and MCP tools are non-breaking for Phase 7 clients.
- New `rel_type` / `kind` values must be ignored by older readers that filter
  known enums defensively.
- Breaking rename of explore fields requires a new contract version note.

## Related Documents

- Phase 7 API: `backend/services/code-graph-service/docs/phase-7-api-contract.md`
- LLD: [`24`](24-code-intelligence-enhancements-low-level-design.md)
