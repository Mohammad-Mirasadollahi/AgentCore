---
doc_id: ac.doc.sea.one-command-cross-platform-agent-onboarding-continued
title: 41 - One-Command Cross-Platform Agent Onboarding (Continued)
doc_type: standard
status: active
schema_version: '1.0'
owner: platform-docs
summary: Continuation of one-command onboarding — first-connect scope wizard when tenant,
  workspace, and Usage Profile are missing; APIs; troubleshooting; implementation status.
tags:
- standard
- sea
- mcp
- onboarding
- connect
phase: 08-software-engineering-architecture
canonical_path: docs/08-software-engineering-architecture/41-one-command-cross-platform-agent-onboarding-continued.md
lifecycle_lane: current
concern_lane: standard
audience_lane:
- platform-engineering
- agents
authority: normative
visibility: internal
linked_symbols:
- backend/packages/agentcore_cli/connect_wizard.py::run_ssh_connect_wizard
- backend/packages/agentcore_cli/connect_wizard.py::prompt_usage_profile
- backend/packages/agentcore_cli/commands/connect.py::_ensure_usage_profile
- backend/packages/agentcore_cli/remote_client.py::remote_register_project
- backend/packages/agentcore_cli/install_root_marker.py::discover_remote_install_root
- backend/packages/agentcore_cli/commands/connect.py::_ensure_remote_source_path
- backend/packages/agentcore_cli/commands/connect.py::_remote_source_candidates
doc_version: 1.2.0
updated_at: '2026-07-28'
---

# 41 - One-Command Cross-Platform Agent Onboarding (Continued)

## Purpose

Continuation of [41-one-command-cross-platform-agent-onboarding.md](./41-one-command-cross-platform-agent-onboarding.md) after the soft size budget. Owns the **first-connect scope wizard** contract, connect HTTP APIs, troubleshooting, and implementation status.

## First connect when scope is missing

When an operator runs `agentcore connect` from an application checkout on a **TTY** and scope is not already configured, connect **must** collect the missing values interactively, then register the project and wire MCP. It does **not** invent tenant/workspace silently, and it does **not** author a new Usage Profile template on the client. The shipped catalog currently has a **single** Usage Profile (`programming-cursor-mcp`), which connect auto-selects.

### When the wizard runs

| Condition | Behavior |
| --- | --- |
| No `<checkout>/.agentcore/connect.yaml` (and no usable legacy home config) | Full SSH wizard + scope prompts |
| `connect.yaml` exists but `usage_profile` empty | Auto-select sole catalog profile; otherwise prompt (TTY) or require `--usage-profile` |
| `connect.yaml` already has `scope.*` + `usage_profile` + working SSH | Reuse; no re-prompt for tenant/workspace/profile |
| Non-interactive / no TTY and profile missing | Fail closed: pass `--usage-profile` (and scope flags as needed) |

`agentcore init` remains the **server/dogfood** path for pinning software roots on an AgentCore checkout. Remote **client** first connect does not require a prior `init` on the laptop; the wizard + `project register` establish scope on the AgentCore server.

### Prompts and defaults

```text
cd /opt/MyApp
agentcore connect
```

Typical interactive order:

1. Server host and SSH username
2. Tenant id (default `default` if the operator accepts the empty default)
3. Workspace id (default `default`)
4. Usage Profile — auto-selected when the catalog has one entry; otherwise numbered list
5. SSH password **once** (pubkey install; never stored)
6. Auto-discover AgentCore `remote_root` via `install-root` markers (not prompted)
7. Auto-discover `source.server_path` over SSH (client path, dogfood `remote_root`, `/opt/<project>`, …) — not prompted
8. Write/merge `<checkout>/.agentcore/connect.yaml`, register/activate project on the server, write IDE MCP configs

| Field | Source when missing | Notes |
| --- | --- | --- |
| `scope.tenant` | Wizard prompt | Operator-chosen id string |
| `scope.workspace` | Wizard prompt | Operator-chosen id string |
| `scope.project` | Current directory name | Override with `--project` |
| `usage_profile` | Sole catalog entry, else `prompt_usage_profile` | Select only — list with `agentcore profile list` |
| `server.remote_root` | `discover_remote_install_root` over SSH | Fail if no marker / common root found |
| `source.server_path` | SSH probe of candidate paths | Must exist on the AgentCore host for ingest; never ask on TTY |

### Flow

```mermaid
flowchart TD
  start[agentcore connect in app checkout] --> hasYaml{connect.yaml with SSH + scope + profile?}
  hasYaml -->|yes| wire[Wire MCP / refresh]
  hasYaml -->|no| wizard[SSH wizard prompts]
  wizard --> scope[Collect tenant workspace Usage Profile]
  scope --> key[Install pubkey once]
  key --> root[Discover remote_root markers]
  root --> write[Write connect.yaml]
  write --> reg[Remote project register and activate]
  reg --> wire
```

| Step | Actor | Action | Outcome |
| --- | --- | --- | --- |
| 1 | Operator | Runs `agentcore connect` under the app repo | Starts client onboarding |
| 2 | CLI | Detects missing config / incomplete scope | Enters interactive wizard on TTY |
| 3 | Operator | Enters host, user, tenant, workspace | Scope ids chosen; profile auto if sole |
| 4 | CLI | Password once → pubkey; discover `remote_root` + `source.server_path` | SSH BatchMode ready; ingest path set |
| 5 | CLI | Writes `connect.yaml`; `project register` / `activate` on server | Scope exists in AgentCore state |
| 6 | CLI | Merges MCP client configs | IDE can talk to AgentCore after reload |

### Non-interactive equivalent

```bash
agentcore connect --usage-profile programming-cursor-mcp \
  --tenant acme --workspace eng \
  --ssh ops@agentcore.example.internal
```

Or set `scope` + `usage_profile` in `.agentcore/connect.yaml` and re-run `agentcore connect`.

### What is not created here

- New Usage Profile **templates** (catalog ships with the CLI; choose an existing id)
- An on-server copy of the laptop app tree (connect discovers an existing server path; clone/rsync/NFS separately if missing)
- A second identity via `agentcore init` unless you are dogfooding on the AgentCore checkout itself

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
| Connect exits: Usage Profile required | Empty catalog / multi-profile without flag | Pass `--usage-profile ID` or run interactively; `agentcore profile list` |
| Ingest / connect fails: could not auto-discover `source.server_path` | No matching tree on server | Clone/rsync the app onto the host (`/opt/<name>` or dogfood AgentCore root), then re-run connect |
| `agentcore: command not found` | PATH | New shell after install; `agentcore path install` |

## Implementation status

| Capability | Status |
| --- | --- |
| `agentcore connect` + `connect.yaml` | Shipped |
| SSH stdio transport | Shipped |
| Interactive scope + Usage Profile on first connect | Shipped |
| HTTP MCP (`serve-http`, port `32500`) | Shipped |
| Bootstrap / sources / ingest / status APIs | Shipped |
| Multi-client MCP file merge | Shipped |
| Prefer HTTP with SSH fallback | Shipped |

## Coding-agent files written

With `--clients all` (default), connect merges into project-scoped files under the app repo:

| `client_id` | Path |
| --- | --- |
| `cursor` | `.cursor/mcp.json` |
| `windsurf` | `.windsurf/mcp.json` |
| `vscode` | `.vscode/mcp.json` |
| `claude-code` | `.mcp.json` |
| `continue` | `.continue/mcp.json` |
| `fragment` | `.agentcore/mcp-servers.json` |

User-global targets (`cursor-user`, `claude-desktop`) only with `--include-user-clients`.

## Concurrent agents

| Layer | Behavior |
| --- | --- |
| **SSH** | Each IDE session is a separate SSH + stdio MCP process |
| **HTTP** | Each session is a separate authenticated HTTP client; gateway is multi-request / concurrent |
| **Data** | Same `tenant/workspace/project` shares Postgres/Neo4j stores |
| **Different products** | Use different `scope.project` values |

## Security (operator rules)

1. **Never** put OS passwords or database passwords in `connect.yaml` or `mcp.json`.
2. SSH: interactive wizard uses password **once** to install a dedicated AgentCore key; afterward **keys only** — BatchMode must succeed without a prompt. Re-auth with `agentcore connect edit` (replaces pubkey).
3. HTTP without TLS: private network + firewall on the MCP port; prefer reverse-proxy TLS for anything beyond a closed lab.
4. Prefer scoped tokens (`AGENTCORE_MCP_TOKEN_SECRET`) over a single shared `AGENTCORE_MCP_HTTP_TOKEN`.
5. Keep `connect.yaml` mode `600`; do not commit live bearer tokens.
6. Prefer non-root SSH users on the AgentCore host.

## Related Documents

- Parent: [41-one-command-cross-platform-agent-onboarding.md](./41-one-command-cross-platform-agent-onboarding.md)
- [35-usage-profile-and-cursor-mcp-onboarding.md](./35-usage-profile-and-cursor-mcp-onboarding.md)
- [40-remote-dev-client-mcp-wiring.md](./40-remote-dev-client-mcp-wiring.md)
- [36-agentcore-cli.md](./36-agentcore-cli.md)
- [39-local-install-runbook.md](./39-local-install-runbook.md)
- [backend/services/mcp-gateway-service/README.md](../../backend/services/mcp-gateway-service/README.md)
