---
doc_id: ac.doc.sea.remote-dev-client-mcp-wiring
title: 40 - Remote Dev Client MCP Wiring
doc_type: runbook
status: active
schema_version: '1.0'
owner: platform-engineering
summary: Cross-platform Python workflow to connect a dev machine (Windows, macOS, or Linux)
  running any MCP-capable coding agent to AgentCore on a remote server via SSH stdio.
tags:
- mcp
- cursor
- ssh
- client
- runbook
- cross-platform
phase: 08-software-engineering-architecture
canonical_path: docs/08-software-engineering-architecture/40-remote-dev-client-mcp-wiring.md
lifecycle_lane: current
concern_lane: ops
audience_lane:
- platform-engineering
- agents
authority: normative
visibility: internal
linked_symbols:
- backend/packages/agentcore_cli/mcp_client_targets.py::McpClientTarget
- scripts/client/wire-remote-mcp.py::main
related_docs:
- docs/08-software-engineering-architecture/35-usage-profile-and-cursor-mcp-onboarding.md
- docs/08-software-engineering-architecture/36-agentcore-cli.md
- docs/08-software-engineering-architecture/39-local-install-runbook.md
- docs/08-software-engineering-architecture/41-one-command-cross-platform-agent-onboarding.md
- docs/08-software-engineering-architecture/44-mcp-token-accounting.md
doc_version: 1.0.0
audience:
- engineer
- operator
language: en
security_classification: internal
updated_at: '2026-07-24'
---

# 40 - Remote Dev Client MCP Wiring

## Purpose

Operators often run **AgentCore on a dedicated server** (`install.sh`) while editing **application code** on another host—for example Windows with Cursor, connected over **Remote SSH** to a Linux workspace. This runbook describes the **cross-platform Python** path to wire that dev host to AgentCore MCP without shell-only scripts.

**Target UX (one command, API-first):** [41-one-command-cross-platform-agent-onboarding.md](./41-one-command-cross-platform-agent-onboarding.md). This document is **Phase A (interim)** until `agentcore connect` and HTTP MCP ship.

Implementation: `backend/packages/agentcore_cli/mcp_client_targets.py`, `remote_client.py`, `remote_mcp_serve.py`, and `agentcore client wire-remote`.

## Supported coding-agent clients

All targets use the same **MCP stdio** shape (`command` + `args` + optional `env`): `mcpServers.<name>`.

| `client_id` | Product | Config path (under `--project-dir` unless user scope) |
| --- | --- | --- |
| `cursor` | Cursor | `.cursor/mcp.json` |
| `windsurf` | Windsurf / Codeium | `.windsurf/mcp.json` |
| `vscode` | VS Code (workspace MCP file) | `.vscode/mcp.json` |
| `claude-code` | Claude Code | `.mcp.json` |
| `continue` | Continue | `.continue/mcp.json` |
| `fragment` | Portable copy (commit or hand-merge) | `.agentcore/mcp-servers.json` |
| `cursor-user` | Cursor user global | `~/.cursor/mcp.json` (requires `--include-user-clients`) |
| `claude-desktop` | Claude Desktop | OS-specific user config (requires `--include-user-clients`) |

List ids: `agentcore client list-mcp-clients`.

**Default:** `wire-remote` writes **all project-scoped** targets (`--clients all`). Narrow with e.g. `--clients cursor,vscode`.

Products that use a different schema (some JetBrains or Zed layouts) can copy from `.agentcore/mcp-servers.json` manually.

## Architecture

```text
[Cursor on Windows/macOS/Linux]
        │
        ▼ spawns MCP (stdio)
[Dev host: ssh → AgentCore server]
        │
        ▼ python -m agentcore_cli.remote_mcp_serve TENANT WORKSPACE PROJECT
[AgentCore server: MCP gateway + Postgres/Neo4j on localhost]
```

- The **IDE brand does not matter**; any MCP client that supports `command` + `args` stdio works.
- MCP gateway runs on the **AgentCore server** (where Compose and `.venv` live).
- The dev host only needs **OpenSSH client**, **Python 3.12+**, and the **`agentcore` CLI** (or the repo launcher script).

## Prerequisites

| Location | Requirement |
| --- | --- |
| AgentCore server | Completed [39-local-install-runbook.md](./39-local-install-runbook.md); `agentcore doctor` OK |
| Dev host | SSH key login to server (`BatchMode=yes`); OpenSSH available (built in on Windows 10+, macOS, Linux) |
| Dev host Python | 3.12+; install CLI via `pip install -e .` from an AgentCore checkout **or** use `scripts/client/wire-remote-mcp.py` from a copied repo tree |

## Server-side (once)

On the AgentCore host after deploy:

```bash
cd /opt/AgentCore
bash install.sh --check   # or full install
agentcore doctor
```

No separate shell wrapper is required; SSH invokes:

```text
/opt/AgentCore/.venv/bin/python -m agentcore_cli.remote_mcp_serve TENANT WORKSPACE PROJECT
```

That module loads `backend/deployments/compose/.env.local`, sets MCP store URLs, and runs `agentcore mcp serve`.

## Dev host — install CLI

**Option A — editable install (recommended on dev laptop):**

```bash
git clone <repo> AgentCore && cd AgentCore
bash install.sh --skip-infra
agentcore path install
```

**Option B — launcher only (minimal copy):**

```bash
python3 /path/to/AgentCore/scripts/client/wire-remote-mcp.py doctor-remote \
  --ssh user@agentcore-host --remote-root /opt/AgentCore
```

## Wire MCP from your application repo

Run from the **application repository** root (the tree Cursor opens over Remote SSH):

```bash
agentcore client doctor-remote \
  --ssh user@agentcore-host \
  --remote-root /opt/AgentCore

agentcore client wire-remote \
  --ssh user@agentcore-host \
  --remote-root /opt/AgentCore \
  --tenant acme --workspace eng --project myapp \
  --register --project-name "My App" \
  --project-dir .
```

This merges `AgentCore-Programming` into **every selected client config** under `--project-dir` (default `--clients all`). Reload MCP in your agent / IDE.

### Flags reference

| Flag | Meaning |
| --- | --- |
| `--ssh` | SSH target `user@host` for the AgentCore server |
| `--remote-root` | AgentCore install path on that server |
| `--project-dir` | Application repo root |
| `--clients` | Comma-separated `client_id` values or `all` (default) |
| `--include-user-clients` | Also update user-global Cursor / Claude Desktop configs |
| `--out` | Single explicit JSON path (skips `--clients`; manual merge) |
| `--register` | Run `project register` + `activate` on the server |
| `--remote-os` | `unix` (default) or `windows` for venv layout on the server |
| `--remote-python` | Override path to remote venv Python |
| `--dry-run` | Print `mcpServers` JSON only |

## Windows notes

- Use **Windows OpenSSH Client** (`ssh` in PowerShell or Git Bash).
- Run `agentcore client …` from PowerShell after `install.sh --skip-infra` in a Windows clone, or run the wire command from the **Remote SSH Linux workspace** (simplest for Cursor Remote SSH).
- Cursor MCP spawn uses the **remote Linux** environment when the workspace is Remote SSH; wire **on that Linux host** from your app repo path.

## Code graph ingest

Ingest runs against paths visible on the **AgentCore server** (or shared storage):

```bash
ssh user@agentcore-host "cd /opt/AgentCore && ./.venv/bin/agentcore graph ingest \
  --tenant acme --workspace eng --project myapp --path /path/on/server/to/repo"
```

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| MCP stuck connecting | SSH password prompt | Use key-based auth; test `ssh -o BatchMode=yes user@host true` |
| `remote python missing` | No venv on server | Run `install.sh` on AgentCore host |
| `compose env missing` | No `.env.local` | Run install stage 03 or copy from example |
| Tools empty / errors | Project not registered | Re-run with `--register` |
| Wrong store | Env not loaded on server | Ensure Compose env exists; check `remote_mcp_serve` logs on stderr |

## Related documents

- [35-usage-profile-and-cursor-mcp-onboarding.md](./35-usage-profile-and-cursor-mcp-onboarding.md)
- [36-agentcore-cli.md](./36-agentcore-cli.md)
- [39-local-install-runbook.md](./39-local-install-runbook.md)
