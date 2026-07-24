---
name: agentcore-create-task
description: Create a durable AgentCore Task for follow-up engineering work.
---

# AgentCore create task

## When

- User or plan needs a durable follow-up Task in AgentCore.

## How

1. Prefer `agentcore_create_task` (`title`, optional `instructions`).
2. Or `agentcore_write` `resource=task` when that path is required.
3. Return the created task identity from the tool result.

## Do not

- Substitute chat checklists for durable Tasks when the user asked to track work in AgentCore.
