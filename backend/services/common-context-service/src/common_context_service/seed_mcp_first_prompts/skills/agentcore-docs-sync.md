---
name: agentcore-docs-sync
description: Run AgentCore docs-sync drift, status, Body-tier validate, note, draft, and index via MCP.
---

# AgentCore docs sync

## When

- Docs drift / coverage (docs-as-code).
- Body-tier validate / note / draft / index via MCP.

## How

1. **Before** writing or explaining product Markdown: `agentcore_docs_authoring_standards` + skill `agentcore-documentation-authoring` (Full-tier).
2. Which docs to open: `agentcore_docs_catalog` (optional `refresh`, filters).
3. Coverage/gaps: `agentcore_docs_status`.
4. Symbol drift: `agentcore_docs_drift_check` (`symbol`, optional `file_path`).
5. Write: `agentcore_docs_write` `mode` = `validate` | `note` | `draft` | `index`.
6. Committed docs: English only.
7. After Full-tier disk edits: gate with MCP `agentcore_quality_audit` and/or CLI `docs-standards` / `quality-audit`; refresh catalog when needed.

## Do not

- Treat `validate` as Full-tier compliance.
- Bypass docs-sync for governed docs-as-code when these tools are on the profile.
- Skip `agentcore_docs_authoring_standards` when asked how documentation writing works.
- Invent `DOCUMENTED_BY` from catalog tags alone.
