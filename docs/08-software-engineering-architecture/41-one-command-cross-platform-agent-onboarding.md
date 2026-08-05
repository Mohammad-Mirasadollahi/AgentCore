---
doc_id: ac.doc.sea.one-command-agent-onboarding
title: 41 - One-Command Cross-Platform Agent Onboarding
doc_type: standard
status: active
schema_version: '1.0'
owner: platform-product
summary: Operator guide and specification for connecting any MCP-capable coding agent to a
  remote AgentCore server with one command over HTTPS (long-lived scoped access token with
  SHA-256 digest at rest, Argon2id bootstrap secret, auto-TLS). Covers the HTTPS connect
  wizard, Streamable HTTP MCP transport, same-host local stdio dogfood, shared config
  (client content-push sync; optional source.server_path for existing on-server trees),
  authentication, concurrency, and security. SSH has been removed from the AgentCore
  product (see doc 40, historical).
tags:
- mcp
- onboarding
- cross-platform
- api
- coding-agent
- specification
- runbook
- https
phase: 08-software-engineering-architecture
canonical_path: docs/08-software-engineering-architecture/41-one-command-cross-platform-agent-onboarding.md
lifecycle_lane: current
concern_lane: standard
audience_lane:
- platform-engineering
- agents
authority: normative
visibility: internal
related_docs:
- docs/08-software-engineering-architecture/36-agentcore-cli.md
- docs/08-software-engineering-architecture/39-local-install-runbook.md
- docs/08-software-engineering-architecture/40-remote-dev-client-mcp-wiring.md
- docs/08-software-engineering-architecture/52-client-tls-trust-and-verify.md
- docs/superpowers/specs/2026-07-25-thin-client-cli-design.md
- docs/superpowers/specs/2026-08-04-api-only-https-no-ssh-design.md
doc_version: 2.4.0
updated_at: '2026-08-05'
linked_symbols:
- backend/packages/agentcore_cli/connect_wizard.py::run_https_connect_wizard
- backend/packages/agentcore_cli/connect_wizard.py::prompt_usage_profile
- backend/packages/agentcore_cli/connect_wizard.py::prompt_api_key
- backend/packages/agentcore_cli/connect_flow/run.py::run_connect
- backend/packages/agentcore_cli/commands/connect.py::_ensure_api_key
- backend/packages/agentcore_cli/connect_config.py::write_or_merge_connect_yaml
- backend/packages/agentcore_cli/connect_http.py::persist_access_token
- backend/packages/agentcore_cli/connect_http.py::read_access_token_file
- backend/packages/agentcore_client/main.py::main
- backend/packages/agentcore_cli/connect_flow/source_path.py::source_path_for_connect
- backend/packages/agentcore_cli/commands/sync/client_remote.py::cmd_sync_client_remote
---

# 41 - One-Command Cross-Platform Agent Onboarding

## Purpose

Connect any **MCP-capable coding agent** (Cursor, Windsurf, VS Code, Claude Code, Continue, Claude Desktop, …) to **AgentCore on a remote server** with one command:

```bash
agentcore connect
```

This document is the **operator guide** (examples included) and the **normative specification** for what is shipped. HTTPS is the **only** remote transport — SSH has been removed from the AgentCore product (API-only HTTPS migration).

Historical SSH wiring (removed): [40-remote-dev-client-mcp-wiring.md](./40-remote-dev-client-mcp-wiring.md).  
CLI reference: [36-agentcore-cli.md](./36-agentcore-cli.md).  
Server install: [39-local-install-runbook.md](./39-local-install-runbook.md).  
Client TLS verify / CA trust: [52-client-tls-trust-and-verify.md](./52-client-tls-trust-and-verify.md).

## Two hosts (topology)

```text
┌──────────────────────────────┐         network          ┌──────────────────────────────┐
│ Dev host                     │ ◄──────── HTTPS ────────► │ AgentCore server             │
│ - Application repository     │                           │ - bash install.sh            │
│ - Coding agent / IDE         │                           │ - Postgres + Neo4j (Compose) │
│ - agentcore on PATH          │                           │ - MCP HTTP (Streamable)      │
│ - .agentcore/connect.yaml    │                           │ - profile / graph API        │
└──────────────────────────────┘                           └──────────────────────────────┘
```

| Role | What lives there | Example names in this doc |
| --- | --- | --- |
| **Dev host** | Your app code + IDE MCP config files | hostname `devbox.example.internal`, app path `/opt/MyApp` |
| **AgentCore server** | Platform install + stores + MCP gateway | hostname `agentcore.example.internal`, install `/opt/AgentCore` |

Replace example hostnames and paths with your own. Do not commit real secrets.

### Same host (dogfood / develop AgentCore)

When the coding agent opens the **AgentCore checkout itself** and Postgres/Neo4j are already local from `install.sh`:

```bash
cd /opt/AgentCore
agentcore init --tenant acme --workspace eng --path /opt/AgentCore   # you choose the IDs + roots
agentcore connect --local
agentcore status
## Requires agentcore.sync.yaml at each sync root (see doc 42 § Sync filters)
agentcore sync
```

This registers a local project, writes workspace MCP configs (stdio gateway on this checkout), and skips HTTPS entirely. Check state with `agentcore status`. Graph sync is off by default for `--local`; run `agentcore sync` when you want the code graph filled (requires a sync filter file; auto full vs incremental; scope/path defaults apply). Use `agentcore purge --yes` only to wipe corrupt graph data.

Command details (required flags, sync filters, what each run changes) → [42 - AgentCore CLI Command Reference](./42-agentcore-cli-command-reference.md) ([§ Sync filters](./42-agentcore-cli-command-reference.md#sync-filters)).

Equivalent YAML: `server.local: true` and `connect.prefer_http: false` in `<checkout>/.agentcore/connect.yaml`.

## Two modes (both shipped)

Both modes speak the **same MCP tools** and the **same project scope**. Only **how the IDE reaches the gateway** changes.

| | **Local stdio (same-host dogfood)** | **Streamable HTTP (remote, HTTPS)** |
| --- | --- | --- |
| IDE config shape | `command` + `args` (stdio, this checkout) | `url` + `headers` |
| Auth | None (same-host process) | Bearer access token (long-lived scoped; re-bootstrap on expiry) |
| Encryption | N/A (local process) | HTTPS (TLS; auto-generated CA for private deployments) |
| Server process | Spawned per IDE session on this checkout | Long-running `agentcore mcp serve-http` |
| Best when | Developing/dogfooding the AgentCore checkout itself | Any remote AgentCore server |
| Fail closed | N/A | Needs `serve-http` up + valid `server.mcp_http_url` + token |

Shared for both modes:

- `scope.tenant` / `scope.workspace` / `scope.project`
- `usage_profile` (default `programming-cursor-mcp`)
- `clients` (which IDE config files to write)
- optional `source` + ingest
- one command: `agentcore connect`

Selection rule inside `agentcore connect`:

1. If `--local` (or `server.local: true`) → local stdio MCP on this checkout; no network transport.
2. Else if HTTP URL + auth headers/token are available → write **Streamable HTTP** MCP configs.
3. Else fail closed with a message to run `agentcore connect edit` (or fix `connect.yaml`).

## One-time setup checklist

### A) AgentCore server (once)

```bash
cd /opt/AgentCore
bash install.sh
agentcore doctor
```

Open a new shell so `agentcore` is on `PATH` ([36](./36-agentcore-cli.md)).

### B) Dev host (once)

```bash
## Install CLI only (no Docker infra on the laptop) — PATH name: agentcore-client only
bash install.sh --role client
## alias: bash install.sh --skip-infra
agentcore-client path install   # if needed; links ~/.local/bin/agentcore-client (removes bare agentcore)
cd /opt/MyApp
agentcore-client connect
```

On **client-only** hosts, use **`agentcore-client`** (there is no bare `agentcore` on PATH). Help lists only connect / profile / process commands. Use `agentcore-client sync`, `agentcore-client status`, and `agentcore-client purge --yes` for **your** connected scope on the server (scope locked to `connect.yaml`). Server-admin commands stay on the AgentCore server (or a `both` install under bare `agentcore`).

On a TTY with no `<checkout>/.agentcore/connect.yaml`, `agentcore connect` runs the **interactive HTTPS wizard**: server URL, tenant / workspace, **Usage Profile**, and a one-time bootstrap secret. It writes `connect.yaml` (mode `600`), mints a long-lived scoped access token via the bootstrap call (server stores only the SHA-256 digest), and wires MCP. The bootstrap secret is never stored on the client. Legacy `~/.agentcore/connect.yaml` is still read if present.

**Missing scope on first connect:** if tenant, workspace, Usage Profile (and related connect fields) are not already present, the wizard **must** collect them before wiring MCP — see [First connect when scope is missing](./41-one-command-cross-platform-agent-onboarding-continued.md#first-connect-when-scope-is-missing) in the continued document. Usage Profile is **selected** from the installed catalog (not authored during client install). Project id defaults to the current directory name.

Advanced template only: `agentcore connect init` then hand-edit YAML.

Reload MCP / the IDE window after connect succeeds.

Re-run the wizard (new server URL, rotate the bootstrap secret, or scope changed):

```bash
agentcore connect edit
```

### Quick Setup — where the access token goes (client)

Do **not** put the raw bearer token in `connect.yaml`. `agentcore-client connect` (and `connect edit`) **always prompts for an API key** on a TTY:

- If `.agentcore/access_token` (or `AGENTCORE_TOKEN`) already has a key → **Enter keeps it**; paste a new `ac1.*` value to replace.
- If none exists → paste is **required** (connect fails closed without it).
- The chosen key is written to `<checkout>/.agentcore/access_token` (mode `600`).

| Prefer | What you do | Path / name |
| --- | --- | --- |
| 1 (connect wizard) | Answer the API key prompt (keep or paste) | Writes `<checkout>/.agentcore/access_token` |
| 2 (install-minted key) | Paste the once-shown `ac1.*` key at that prompt | Same file — one line, no quotes |
| 3 (env / non-interactive) | Export the env named by `auth.token_env` | Default `AGENTCORE_TOKEN` (override with `AGENTCORE_CONNECT_TOKEN`) |
| Recover | Re-run connect / edit | Paste a new key, or set `AGENTCORE_CONNECT_BOOTSTRAP_SECRET` for register/CA |

Token lookup when loading `connect.yaml` (before the interactive prompt):

1. Env named by `auth.token_env` (default `AGENTCORE_TOKEN`), or `AGENTCORE_CONNECT_TOKEN`
2. Else `<checkout>/.agentcore/access_token` (sibling of `connect.yaml`)

A user-supplied API key is **not** overwritten if bootstrap also mints a token. `connect.yaml` only names the env (`auth.token_env`); it must not store the secret. Gitignore `.agentcore/access_token`. TLS trust/verify: [52](./52-client-tls-trust-and-verify.md). Server mint during install: [39](./39-local-install-runbook.md#server-auth-secrets-jwt--bootstrap--optional-api-key).

Minimal client checklist:

```bash
# On the app checkout (client host)
cd /opt/MyApp
bash /opt/AgentCore/install.sh --role client   # once
agentcore-client connect                      # prompts API key (required); optional bootstrap
agentcore-client doctor
# Reload MCP / IDE window
```

---

## Example 1 — HTTPS mode (remote AgentCore server)

Use this whenever the coding agent connects to an AgentCore server over the network.

### Server: start HTTP MCP

```bash
export AGENTCORE_MCP_TOKEN_SECRET='replace-with-a-long-random-secret'
export AGENTCORE_MCP_HTTP_PUBLIC_URL='https://agentcore.example.internal:32500'
## When Compose Postgres is up:
## export AGENTCORE_MCP_STORE_MODE=postgres
## export AGENTCORE_DATABASE_URL=...
agentcore mcp serve-http --host 0.0.0.0 --port 32500
```

Keep this process running (systemd/supervisor in real deployments). Put a TLS-terminating reverse proxy (or the auto-generated CA) in front — plain `http://` is rejected unless `AGENTCORE_ALLOW_INSECURE_HTTP=1` is set for an explicit lab/loopback override.

Optional: run project-profile HTTP API for bootstrap (`server.url` in connect.yaml). Port profile default for project-profile is `AGENTCORE_PROJECT_PROFILE_PORT` (`32194`).

### Dev host: `<checkout>/.agentcore/connect.yaml`

```yaml
server:
  url: https://agentcore.example.internal:32194
  mcp_http_url: https://agentcore.example.internal:32500

auth:
  # Optional API token for bootstrap if your profile API requires it:
  token_env: AGENTCORE_TOKEN

scope:
  tenant: acme
  workspace: eng

usage_profile: programming-cursor-mcp
clients: all

source:
  server_path: /srv/repos/MyApp

connect:
  register: true
  smoke_test: true
  prefer_http: true
  ingest: optional
```

Credentials: see [Quick Setup — where the access token goes](#quick-setup--where-the-access-token-goes-client). Prefer `.agentcore/access_token` or:

```bash
export AGENTCORE_TOKEN='...'
```

The MCP bearer token is **minted by bootstrap** (single long-lived scoped access token; no refresh token) when the profile API is set, and written into IDE `headers` — not as a database password. On the server, only the token's SHA-256 digest is persisted (`project_profile.access_tokens`). When the token expires or is revoked, re-run `agentcore connect` / `agentcore connect edit`.

### Dev host: run connect

```bash
cd /opt/MyApp
agentcore connect
```

Expected: prints `transport: streamable_http (https://agentcore.example.internal:32500/mcp)`.

What lands in MCP config (shape):

```json
{
  "mcpServers": {
    "AgentCore-Programming": {
      "url": "https://agentcore.example.internal:32500/mcp",
      "headers": {
        "Authorization": "Bearer ac1....",
        "X-Tenant-Id": "acme",
        "X-Workspace-Id": "eng",
        "X-Project-Id": "MyApp",
        "X-Usage-Profile": "programming-cursor-mcp"
      }
    }
  }
}
```

Do **not** commit files that contain live bearer tokens. Prefer gitignoring generated MCP JSON or redacting before commit.

---

## Shared config reference (`<checkout>/.agentcore/connect.yaml`)

| Key | Required | Meaning |
| --- | --- | --- |
| `server.remote_root` | Optional | AgentCore install path (informational; default `/opt/AgentCore`) |
| `server.url` | Optional | project-profile API base for bootstrap / ingest |
| `server.mcp_http_url` | For remote mode | Public base of MCP HTTP (port `32500` by default); must be `https://` |
| `auth.token_env` | Optional | Env var name for the bearer (default `AGENTCORE_TOKEN`); prefer `.agentcore/access_token` over inline secrets |
| `scope.tenant` / `workspace` | Yes | Platform scope |
| `scope.project` | Optional | Defaults to **cwd directory name** |
| `usage_profile` | Optional | Default `programming-cursor-mcp` |
| `clients` | Optional | `all` or comma list (`cursor,vscode,…`) |
| `source.server_path` | Optional (NFS/clone / explicit `--path`) | On-server tree when set. Default `agentcore-client sync` uses **content-push** (`ingest-push`) and does not require this. Details: [41-continued](./41-one-command-cross-platform-agent-onboarding-continued.md) |
| `source.git` | Optional | `{ remote, branch }` registration |
| `connect.prefer_http` | Optional | Default `true` |
| `connect.register` | Optional | Default `true` |
| `connect.smoke_test` | Optional | Default `true` |
| `connect.ingest` | Optional | `off` \| `optional` \| `always` |

Environment overrides (examples): `AGENTCORE_CONNECT_URL`, `AGENTCORE_CONNECT_MCP_HTTP_URL`, `AGENTCORE_CONNECT_TENANT`, `AGENTCORE_CONNECT_PROJECT`, `AGENTCORE_CONNECT_LOCAL`.

CLI:

```bash
agentcore connect init
agentcore connect
agentcore connect --project myapp --clients cursor,vscode
agentcore connect --dry-run
agentcore client list-mcp-clients
```

## Related Documents

- Continued: [41-one-command-cross-platform-agent-onboarding-continued.md](./41-one-command-cross-platform-agent-onboarding-continued.md)
- Normative HTTPS/auth: [2026-08-04-api-only-https-no-ssh-design.md](../superpowers/specs/2026-08-04-api-only-https-no-ssh-design.md)
- Historical SSH wiring: [40-remote-dev-client-mcp-wiring.md](./40-remote-dev-client-mcp-wiring.md)
- CLI: [36-agentcore-cli.md](./36-agentcore-cli.md)
- Install: [39-local-install-runbook.md](./39-local-install-runbook.md)
