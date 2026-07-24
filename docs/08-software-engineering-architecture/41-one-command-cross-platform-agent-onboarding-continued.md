---
doc_id: ac.doc.sea.one-command-cross-platform-agent-onboarding-continued
title: 41 - One-Command Cross-Platform Agent Onboarding (Continued)
doc_type: standard
status: active
schema_version: '1.0'
owner: platform-docs
summary: Continuation of `docs/08-software-engineering-architecture/41-one-command-cross-platform-agent-onboarding.md`
  — remaining sections after the soft size budget.
tags:
- standard
- sea
phase: 08-software-engineering-architecture
canonical_path: docs/08-software-engineering-architecture/41-one-command-cross-platform-agent-onboarding-continued.md
lifecycle_lane: current
concern_lane: standard
audience_lane:
- platform-engineering
- agents
authority: normative
visibility: internal
linked_symbols: []
doc_version: 1.0.0
updated_at: '2026-07-24'
---

# 41 - One-Command Cross-Platform Agent Onboarding (Continued)

## Purpose

Continuation of `docs/08-software-engineering-architecture/41-one-command-cross-platform-agent-onboarding.md` — remaining sections after the soft size budget.

## APIs (when `server.url` is set)

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/projects/{project_id}/connect/bootstrap` | Register + activate + MCP descriptor |
| `POST` | `/api/v1/projects/{project_id}/connect/sources` | Register server path / git |
| `POST` | `/api/v1/projects/{project_id}/connect/ingest` | Request ingest |
| `GET` | `/api/v1/projects/{project_id}/connect/status` | Status |
| `GET` | `/health` | Liveness |

Details: [usage-profile-api.md](../../backend/services/project-profile-service/docs/usage-profile-api.md).

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| MCP hangs on connect | SSH password prompt | Install key; test `ssh -o BatchMode=yes … true` |
| `HTTP smoke failed` | `serve-http` down or bad token | Start `agentcore mcp serve-http`; check `AGENTCORE_MCP_TOKEN_SECRET` |
| Tools empty / wrong project | Wrong scope | Check `tenant` / `workspace` / project id (= cwd name unless set) |
| Ingest skipped / failed | Path not on server | Set `source.server_path` to a path that exists on AgentCore host |
| `agentcore: command not found` | PATH | New shell after install; `agentcore path install` |

## Implementation status

| Capability | Status |
| --- | --- |
| `agentcore connect` + `connect.yaml` | Shipped |
| SSH stdio transport | Shipped |
| HTTP MCP (`serve-http`, port `32500`) | Shipped |
| Bootstrap / sources / ingest / status APIs | Shipped |
| Multi-client MCP file merge | Shipped |
| Prefer HTTP with SSH fallback | Shipped |

## Related documents

- [35-usage-profile-and-cursor-mcp-onboarding.md](./35-usage-profile-and-cursor-mcp-onboarding.md)
- [40-remote-dev-client-mcp-wiring.md](./40-remote-dev-client-mcp-wiring.md)
- [36-agentcore-cli.md](./36-agentcore-cli.md)
- [39-local-install-runbook.md](./39-local-install-runbook.md)
- [backend/services/mcp-gateway-service/README.md](../../backend/services/mcp-gateway-service/README.md)


## Related Documents

- Parent document: `docs/08-software-engineering-architecture/41-one-command-cross-platform-agent-onboarding.md`
