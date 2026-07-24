# MCP-first AgentCore

When AgentCore MCP is connected (lazy: `mcp_search_tools` → `mcp_execute_tool`):

1. Call `agentcore_guidance_resolve` before substantive coding.
2. Prefer profile MCP tools over inventing local-only substitutes for AgentCore capabilities.
3. Persist/recall project facts with `agentcore_write` / `agentcore_memory_retrieve` — not chat-only.
4. Find symbols via code-graph first: structural (`callers`, directed `impact`, `community`, `call_path`) before wide Read/`rg`; escalate `explore` / hybrid when sparse or semantic. IDE LSP (`ide_references` / `ide_definition` / `ide_rename`) is local-semantic only (`reference_kind=ide_semantic`) — never dual-write into durable `CODE_REL`; reconcile via AST re-ingest.
5. Use docs-sync tools for drift, coverage, and governed doc drafts.
6. After replace/retire: remove proven orphans in the **same change** (unused imports, superseded symbols, exclusive tests, stale re-exports). Prefer `agentcore_code_graph_unused_candidates`; else explore + `rg`. Skip live-until-proven (dynamic registries, public HTTP/IAM/SDK exports, `tsoc-defer`). AgentCore does not delete files — you do.
7. How-to-write docs or product Markdown work: `agentcore_docs_authoring_standards` + skill `agentcore-documentation-authoring`. Docs-sync `validate` is Body-tier only — not Full-tier.
8. If a needed tool is missing from search: `agentcore_get_effective_profile`, report the gap, ask before unmanaged bypass.
9. English for identifiers, paths, and committed docs; honor other always-on bundle rules.
10. **Hard modules** (queues, dual-store durability, workers, state machines, trust boundaries, fail-open/fail-closed): keep a file-top module contract (role + SoT/invariants + allowed vs forbidden failures) per `docs/08-software-engineering-architecture/49-module-contract-docstrings-standard.md`. Skip trivial helpers. Skill `agentcore-source-contracts`.
11. Confusing **package/folder seams**: short README map (purpose + boundaries + 2–5 start-here files) per `docs/08-software-engineering-architecture/50-package-folder-readme-standard.md` — not a per-file encyclopedia. Skill `agentcore-source-contracts`.
12. **Fix-on-read (docs):** After Read of nonconforming product Markdown under `docs/` / `backend/docs/` / `frontend/docs/` / `ai-toolstack/docs/` / `deploy-toolkit`, load `agentcore-documentation-authoring` + `agentcore_docs_authoring_standards` and remediate **that file in the same turn**.
13. **Fix-on-read (module contracts):** After Read of a hard module with a missing/wrong contract header, load `agentcore-source-contracts` and fix the 3–6 line header **in the same turn**. Do not stamp helpers/DTOs/re-exports.
14. **Fix-on-write (standards):** On create/edit of product docs or hard-module/package-seam code, load `agentcore-standards-on-edit` and remediate **in the same turn**. For product Markdown: align body, bump `doc_version` (semver), set `updated_at` (UTC `YYYY-MM-DD`) — never stamp-only. Prefer drift/`linked_symbols` to choose docs. Sync may skip nonconforming docs; edit-time fix is how the corpus converges.
15. **Quality debt loop:** After `guidance_resolve` (session start) and after material edits: call `agentcore_quality_audit`. If `must_remediate`, load skill `agentcore-quality-audit` and clear high/medium findings (or create durable tasks) before treating work as done. Soft size and linking gaps are in scope — not optional noise.
