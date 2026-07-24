---
name: agentcore-code-graph
description: Search AgentCore code knowledge graph before wide local search.
---

# AgentCore code graph

## When

- Locating symbols, owners, callers, related modules, or blast radius.
- Planning a change with graph-guided context.

## How

1. Structural first: `agentcore_code_graph_callers`, `agentcore_code_graph_impact` (`direction`), `agentcore_code_graph_community`, `agentcore_code_graph_call_path` — before wide Read/`rg`. These use `reference_kind=structural`.
2. Semantic / “how does X work” / survey: `agentcore_code_graph_explore`; follow `escalate_hint.next_tools` when present.
3. Name/meaning lookup only: `agentcore_code_graph_hybrid_search` or `agentcore_code_graph_search`.
4. Related human Markdown: `agentcore_docs_catalog` (tags/lanes/query) then Read matches — never invent `DOCUMENTED_BY`.
5. Seed pack: `agentcore_code_graph_generation_context`; prefer `hybrid_documentation` (human → living → rationale → AST), including `MODULE_CONTRACT` / package README maps when present.
6. Reviews/PRs: `agentcore_code_graph_detect_changes` with changed paths.
7. Architecture: `agentcore_code_graph_architecture_overview` or `agentcore_code_graph_path`.
8. IDE-precise rename/refs/definition (local LSPs): `agentcore_code_graph_ide_references` / `ide_definition` / `ide_rename` (`reference_kind=ide_semantic`). Reconcile via rename or `agentcore_code_graph_reconcile_after_edit` — never durable `CODE_REL` from LSP. `available=false` → configure `AGENTCORE_LSP_CMD_*`.
9. Escalate to Read/`rg` only for pending-sync, low-confidence edges, empty graph, or after structural + explore/hybrid fails; report degraded mode.
10. After replace/retire → skill `agentcore-remove-dead-code` in the same change.

## Do not

- Prefer workspace crawl when graph tools are healthy.
- Re-verify explore packs with wide Grep when verbatim source already returned.
- Treat catalog hits as graph edges.
- Skip `escalate_hint` and dump full files.
- Confuse structural neighbors with IDE find-refs, or dual-write LSP into the durable graph.
