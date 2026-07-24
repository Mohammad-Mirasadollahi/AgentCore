# Agent entry

**Law:** always-on rule `mcp-first-agentcore`.

## Session start

1. Resolve workspace guidance via MCP when available.
2. Apply always-on rules from the bundle.
3. Load the matching skill before heavy memory, graph, docs, or durable-write work.

## Skills

- `agentcore-session-bootstrap` — session start / MCP bootstrap
- `agentcore-memory` — recall or persist project memory
- `agentcore-code-graph` — symbols, callers, ownership, blast radius
- `agentcore-remove-dead-code` — prove and delete orphans after replace/retire
- `agentcore-durable-write` — memory / task / activity / decision records
- `agentcore-documentation-authoring` — Full-tier Markdown; write + fix-on-read
- `agentcore-standards-on-edit` — fix-on-write for docs and hard modules
- `agentcore-quality-audit` — session/edit quality debt; remediate high/medium
- `agentcore-docs-sync` — Body-tier drift / coverage / validate / note / draft / index
- `agentcore-source-contracts` — standards 49/50; fix-on-read for hard modules
- `agentcore-create-task` — durable follow-up Task
