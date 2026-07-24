---
name: agentcore-remove-dead-code
description: Prove and delete orphaned symbols, imports, and exclusive tests after a replace or retire.
---

# AgentCore remove dead code

## When

- After implement/replace/retire leaves old symbols, imports, re-exports, or exclusive tests.
- Cleanup request in the scope already touched.
- Unused-candidate MCP / explore shows safe deletes nearby.

## How

1. Prefer `agentcore_code_graph_unused_candidates` (`scope_mode=changed_symbols` or neighborhood). Else explore + `rg` on bare names and import paths.
2. Treat each candidate as **live until proven**: dynamic loaders, string registries, public HTTP/IAM/SDK exports, tests-only refs, entrypoints, `tsoc-defer`.
3. Delete only proven-unused symbols **and** their exclusive tests, fixtures, barrels, and docs that only described them.
4. Do not widen into unrelated refactors or repo-wide hunts.
5. Verify with the smallest check that would fail if the delete were wrong.
6. Optional: `agentcore_write` Activity/WorkLog for removed paths (cleanup KPIs).
7. List skipped uncertain symbols + blockers in the chat summary.

## Do not

- Ask AgentCore to delete files — it only surfaces candidates.
- Delete public APIs, plugin hooks, or `tsoc-defer` stopgaps without an explicit root-cause fix.
- Count unproven deletes as successful cleanup.
