---
name: agentcore-quality-audit
description: >-
  Run agentcore_quality_audit (MCP) or CLI; remediate high/medium findings same turn.
---

# AgentCore quality audit

## When

- Session start (after guidance resolve).
- After material code or product-doc edits.
- User asks what is broken / nonconforming / stale.
- Sync skipped nonconforming paths or wrote `.agentcore/quality-followup-tasks.json`.

## How

1. Call MCP `agentcore_quality_audit` (optional `severities=["high","medium"]`). Prefer MCP over inventing a local scan.
2. If `must_remediate` is true:
   - Docs findings → skill `agentcore-standards-on-edit` / `agentcore-documentation-authoring`; fix each path (soft size = split sibling; linking = evidence `linked_symbols`; revision = bump stamps with body).
   - Code never-ingested / stale → run `agentcore sync` for those paths (AST-only if cloud LLM blocked); do not leave debt silent.
3. Re-call `agentcore_quality_audit` until high/medium are clear, or create durable tasks (`create_tasks=true` or `agentcore_create_task`) with the finding list.
4. CLI fallback when MCP tool missing: `agentcore quality-audit` / `agentcore docs-standards`.

## Do not

- Skip the audit at session start when the tool is on the effective profile.
- Treat Body-tier docs-sync validate as Full-tier / quality-audit.
- Leave `docs.size_soft` or linking gaps as “warnings only” without remediation or a durable task.
- Assume AgentCore will edit the repo — you remediate; AgentCore reports and stores tasks.
