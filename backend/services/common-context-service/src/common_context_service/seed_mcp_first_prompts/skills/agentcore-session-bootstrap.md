---
name: agentcore-session-bootstrap
description: Bootstrap an AgentCore MCP session—ping, profile, resolve guidance, then code.
---

# AgentCore session bootstrap

## When

- Starting work on an AgentCore-connected project.
- After MCP reload or Usage Profile change.

## How

1. Lazy MCP: `mcp_search_tools` → `mcp_execute_tool`; start with `agentcore_ping`.
2. `agentcore_get_effective_profile` for allowed tools.
3. `agentcore_guidance_resolve` → apply `agents_entry` + `always_rules`.
4. Matching catalog skill → `agentcore_guidance_get_skill` before improvising.
5. Product docs → `agentcore_docs_authoring_standards` + `agentcore-documentation-authoring`.
6. Hard modules / package seams → `agentcore-source-contracts` (49/50).
7. **Quality debt:** `agentcore_quality_audit` → if `must_remediate`, skill `agentcore-quality-audit` (remediate or durable tasks) before coding further.
8. Only then memory / graph / docs / write tools or local edits.

## Do not

- Large refactors before guidance resolve when the tool exists.
- Assume tools without search or the effective profile.
- Skip `agentcore_quality_audit` at session start when it is on the effective profile.
