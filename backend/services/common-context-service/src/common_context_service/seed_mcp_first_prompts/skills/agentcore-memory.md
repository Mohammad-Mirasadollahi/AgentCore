---
name: agentcore-memory
description: Retrieve or persist project memory through AgentCore MCP.
---

# AgentCore memory

## When

- Need durable project facts, decisions, or conventions.
- User asks to remember or recall something.

## How

1. Retrieve: `agentcore_memory_retrieve` (`query`, optional `include_history`).
2. Persist: `agentcore_write` `resource=memory` (`title`, `body`, optional `tags`, `confidence`).
3. Cite what AgentCore returned; do not invent memory.

## Do not

- Keep durable facts chat-only when write/retrieve tools are available.
