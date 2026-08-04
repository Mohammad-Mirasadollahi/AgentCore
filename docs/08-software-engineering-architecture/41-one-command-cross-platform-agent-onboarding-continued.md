---
doc_id: ac.doc.sea.one-command-cross-platform-agent-onboarding-continued
title: 41 - One-Command Cross-Platform Agent Onboarding (Continued)
doc_type: standard
status: active
schema_version: '1.0'
owner: platform-docs
summary: Continuation of one-command onboarding — first-connect scope wizard when tenant,
  workspace, and Usage Profile are missing; shared SSH source.server_path discovery plus
  automatic rsync stage to <install>-data/sources/<project>; sibling data root; APIs; troubleshooting.
tags:
- standard
- sea
- mcp
- onboarding
- connect
- sync
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
- backend/packages/agentcore_cli/connect_flow/source_path.py::ensure_remote_source_path
- backend/packages/agentcore_cli/connect_flow/source_path.py::remote_source_candidates
- backend/packages/agentcore_cli/connect_flow/source_path.py::stage_local_checkout
- backend/packages/agentcore_cli/connect_flow/source_path.py::staged_source_path
- backend/packages/agentcore_cli/commands/sync/client_remote.py::cmd_sync_client_remote
doc_version: 1.5.0
updated_at: '2026-08-04'
---

# 41 - One-Command Cross-Platform Agent Onboarding (Continued)

## Purpose

Continuation of [41-one-command-cross-platform-agent-onboarding.md](./41-one-command-cross-platform-agent-onboarding.md) after the soft size budget. Owns the **first-connect scope wizard** contract, the **shared SSH `source.server_path` resolver** (probe + optional rsync stage for connect and client remote sync), connect HTTP APIs, troubleshooting, and implementation status.

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
| `source.server_path` | SSH probe of candidate paths (shared with sync) | Must exist on the AgentCore host for ingest/sync; never ask on TTY |

### Invariant: shared `source.server_path` resolver

**Connect and client remote sync share one SSH discovery implementation** (`connect_flow.source_path.ensure_remote_source_path`). Agents must not reintroduce a sync-only fail-closed gap that ignores that resolver.

| Rule | Detail |
| --- | --- |
| One probe order | Client cwd → dogfood `remote_root` when applicable → `/opt/<project>` → `/srv/repos/<project>` → `<install>-data/sources/<project>` (legacy `/var/lib/agentcore/sources/` still probed) |
| Auto-stage | If no candidate exists, rsync to `<install>-data/sources/<project>` (`stage_local_checkout`); requires `rsync` on the client |
| Connect | Discovers or stages when missing, then persists into `.agentcore/connect.yaml` |
| `agentcore-client sync` / client remote sync | If CLI `--path` is absent and `source.server_path` is empty, runs the **same** resolver, persists the result, then SSH-syncs |
| Never | Silently fall back to AgentCore host identity pins (that would sync the wrong tree) |
| Fail closed | Only when SSH probe and rsync stage both fail |

```mermaid
flowchart TD
  syncCmd[agentcore-client sync] --> loadYaml[Load connect.yaml]
  loadYaml --> hasCli{CLI --path set?}
  hasCli -->|yes| sshSync[SSH agentcore sync --path]
  hasCli -->|no| hasSrc{source.server_path set?}
  hasSrc -->|yes| sshSync
  hasSrc -->|no| discover[ensure_remote_source_path SSH probes]
  discover -->|found| persist[write_or_merge connect.yaml]
  persist --> sshSync
  discover -->|none| stage[rsync stage to install-data/sources/project]
  stage -->|ok| persist
  stage -->|fail| failClosed[Fail closed]
```

| Step | Actor | Action | Outcome |
| --- | --- | --- | --- |
| 1 | Operator | Runs `agentcore-client sync` under the app checkout | Client remote path (no local Compose stack) |
| 2 | CLI | Loads `connect.yaml`; skips discovery if `--path` or `source.server_path` set | Path known without probe |
| 3 | CLI | Otherwise probes candidates over SSH | Same resolver as connect |
| 4 | CLI | If none found, rsync-stages checkout to `<install>-data/sources/<project>` | Tree exists on server |
| 5 | CLI | Merges `source.server_path` into yaml | Path reused next time |
| 6 | CLI | If path is under `<install>-data/sources/` (or legacy `/var/lib/…`), re-rsync before remote sync | Staged mirror stays fresh |
| 7 | CLI | Runs remote `agentcore sync --path …` | Graph ingest on server |

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
- A second identity via `agentcore init` unless you are dogfooding on the AgentCore checkout itself

### What is staged automatically

When SSH probes find no matching tree, connect / client sync **rsync** the client checkout to `<install>-data/sources/<project>` on the AgentCore host (excludes `.git`, `node_modules`, `.venv`, caches). Operators may still NFS/clone to `/opt/<project>` if they prefer a shared path; discovery prefers an existing probe hit before staging.

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
| Ingest / connect / sync fails: could not auto-discover or stage `source.server_path` | SSH/rsync failed after probes missed | Fix BatchMode SSH + install `rsync` on the client; re-run connect or sync |
| `agentcore-client sync`: remote sync needs explicit server-side path | Safety net after discovery/stage skipped | Re-run sync (auto-discover/stage+persist) or set `source.server_path` / pass `--path` |
| `agentcore: command not found` | PATH | New shell after install; `agentcore path install` |

## Implementation status

| Capability | Status |
| --- | --- |
| `agentcore connect` + `connect.yaml` | Shipped |
| Shared SSH `source.server_path` discovery (connect + client sync) | Shipped |
| Auto rsync stage to `<install>-data/sources/<project>` when probes miss | Shipped |
| Sibling `AgentCore-data` root for Postgres/Neo4j/usage/cache/backup | Shipped |
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
