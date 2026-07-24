---
doc_id: ac.doc.sea.one-command-agent-onboarding
title: 41 - One-Command Cross-Platform Agent Onboarding
doc_type: standard
status: active
schema_version: '1.0'
owner: platform-product
summary: Operator guide and specification for connecting any MCP-capable coding agent to a
  remote AgentCore server with one command. Covers interactive SSH key bootstrap, SSH stdio
  and Streamable HTTP transports, shared config, authentication, concurrency, and security.
tags:
- mcp
- onboarding
- cross-platform
- api
- coding-agent
- specification
- runbook
- ssh
phase: 08-software-engineering-architecture
canonical_path: docs/08-software-engineering-architecture/41-one-command-cross-platform-agent-onboarding.md
lifecycle_lane: current
concern_lane: standard
audience_lane:
- platform-engineering
- agents
authority: normative
visibility: internal
linked_symbols:
- backend/packages/agentcore_cli/connect_wizard.py::run_ssh_connect_wizard
- backend/packages/agentcore_cli/ssh_bootstrap.py::bootstrap_ssh_auth
- backend/packages/agentcore_cli/connect_flow.py::run_connect
- backend/packages/agentcore_cli/connect_config.py::write_or_merge_connect_yaml
doc_version: 1.1.0
updated_at: '2026-07-24'
---

# 41 - One-Command Cross-Platform Agent Onboarding

## Purpose

Connect any **MCP-capable coding agent** (Cursor, Windsurf, VS Code, Claude Code, Continue, Claude Desktop, …) to **AgentCore on a remote server** with one command:

```bash
agentcore connect
```

This document is the **operator guide** (examples included) and the **normative specification** for what is shipped.

Companion detail for SSH-only wiring: [40-remote-dev-client-mcp-wiring.md](./40-remote-dev-client-mcp-wiring.md).  
CLI reference: [36-agentcore-cli.md](./36-agentcore-cli.md).  
Server install: [39-local-install-runbook.md](./39-local-install-runbook.md).

## Two hosts (topology)

```text
┌──────────────────────────────┐         network          ┌──────────────────────────────┐
│ Dev host                     │ ◄──── SSH and/or HTTP ──► │ AgentCore server             │
│ - Application repository     │                           │ - bash install.sh            │
│ - Coding agent / IDE         │                           │ - Postgres + Neo4j (Compose) │
│ - agentcore on PATH          │                           │ - MCP stdio and/or HTTP      │
│ - ~/.agentcore/connect.yaml  │                           │ - optional profile API       │
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

This registers a local project, writes workspace MCP configs (stdio gateway on this checkout), and skips SSH/HTTP. Check state with `agentcore status`. Graph sync is off by default for `--local`; run `agentcore sync` when you want the code graph filled (requires a sync filter file; auto full vs incremental; scope/path defaults apply). Use `agentcore purge --yes` only to wipe corrupt graph data.

Command details (required flags, sync filters, what each run changes) → [42 - AgentCore CLI Command Reference](./42-agentcore-cli-command-reference.md) ([§ Sync filters](./42-agentcore-cli-command-reference.md#sync-filters)).

Equivalent YAML: `server.local: true` and `connect.prefer_http: false` in `~/.agentcore/connect.yaml`.

## Two transports (both shipped)

Both modes speak the **same MCP tools** and the **same project scope**. Only **how the IDE reaches the gateway** and **how you authenticate** change.

| | **SSH stdio (Phase A)** | **HTTP MCP (Phase B)** |
| --- | --- | --- |
| IDE config shape | `command: ssh` + `args` | `url` + `headers` |
| Auth | SSH **public key** (BatchMode) | Bearer token (scoped HMAC or shared) |
| Encryption | SSH tunnel | TLS only if you put a reverse proxy in front (plain HTTP is for private LAN labs) |
| Server process | Spawned per IDE session via SSH | Long-running `agentcore mcp serve-http` |
| Best when | Private LAN, OpenSSH available, strongest default security without TLS | Many clients want URL-only config; you terminate TLS at the edge |
| Fail closed | Needs working key login | Needs `serve-http` up + valid token |

Shared for both modes:

- `scope.tenant` / `scope.workspace` / `scope.project`
- `usage_profile` (default `programming-cursor-mcp`)
- `clients` (which IDE config files to write)
- optional `source` + ingest
- one command: `agentcore connect`

Selection rule inside `agentcore connect`:

1. If `prefer_http: true` (default) **and** HTTP URL + auth headers/token are available → write **HTTP** MCP configs.
2. Else if SSH BatchMode works (or the interactive wizard just installed a key) → write **SSH** MCP configs.
3. Else fail closed with a message to run `agentcore connect --edit` (or fix `connect.yaml`).

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
## Install CLI only (no need for Docker infra on the laptop)
bash install.sh --skip-infra
agentcore path install   # if needed
cd /opt/MyApp
agentcore connect
```

On a TTY with no `~/.agentcore/connect.yaml`, `agentcore connect` runs the **interactive SSH wizard**: host, username, password (once), remote root, tenant/workspace. It generates `~/.ssh/id_ed25519_agentcore`, installs the pubkey on the server, writes `connect.yaml` (mode `600`), and wires MCP. Password is never stored.

Advanced template only: `agentcore connect --init` then hand-edit YAML.

Reload MCP / the IDE window after connect succeeds.

---

## Example 1 — SSH mode (recommended for private LAN)

Use this when the coding agent runs on a machine that can reach the AgentCore host over SSH.

### Server: nothing extra for MCP HTTP

SSH mode only needs a completed `install.sh` and a login that can run:

```text
/opt/AgentCore/.venv/bin/python -m agentcore_cli.remote_mcp_serve <tenant> <workspace> <project>
```

(that is what `agentcore connect` puts into MCP `ssh` args).

### Dev host: interactive key bootstrap (default)

```bash
cd /opt/MyApp
agentcore connect
# prompts: host, username, password, remote_root, tenant, workspace
```

Prefer a dedicated OS user (for example `ops`). The password is used **once** to install the AgentCore pubkey. After that, IDE MCP spawn uses **BatchMode + key only** — passwords do not work for IDE MCP spawn.

Re-enter host/user (and replace the pubkey):

```bash
agentcore connect --edit
```

`--edit` always rotates `~/.ssh/id_ed25519_agentcore`, installs the new pubkey, and best-effort removes the old pubkey line from remote `authorized_keys`.

Manual key install remains possible (`ssh-keygen` + `ssh-copy-id`) but is not required.

### Dev host: `~/.agentcore/connect.yaml`

The wizard writes this file. Hand-edit **scope / clients / remote_root / ingest** freely; re-run `agentcore connect` to apply. If you change `server.ssh` or `auth.ssh_key` and BatchMode breaks, run `agentcore connect --edit` — do not put OS passwords in YAML.

```yaml
server:
  ssh: ops@agentcore.example.internal
  remote_root: /opt/AgentCore

auth:
  ssh_key: ~/.ssh/id_ed25519_agentcore

scope:
  tenant: acme
  workspace: eng
  # project: defaults to current directory name (e.g. MyApp)

usage_profile: programming-cursor-mcp
clients: all

source:
  # Path visible ON THE AGENTCORE SERVER (NFS, clone, or sync) — not required to be the laptop path
  server_path: /srv/repos/MyApp

connect:
  register: true
  smoke_test: true
  prefer_http: false    # force SSH even if HTTP fields exist
  ingest: optional
```

### Dev host: run connect

```bash
cd /opt/MyApp
agentcore connect
```

Expected: merges `AgentCore-Programming` into project MCP files (for example `.cursor/mcp.json`, `.vscode/mcp.json`, …), prints `transport: ssh-stdio`, optional ingest.

What lands in MCP config (shape):

```json
{
  "mcpServers": {
    "AgentCore-Programming": {
      "command": "ssh",
      "args": [
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=15",
        "ops@agentcore.example.internal",
        "/opt/AgentCore/.venv/bin/python",
        "-m",
        "agentcore_cli.remote_mcp_serve",
        "acme",
        "eng",
        "MyApp"
      ]
    }
  }
}
```

---

## Example 2 — HTTP mode (URL + token)

Use this when you want IDE config without SSH spawn. On private LAN without TLS, treat this as a **lab** setup and firewall the MCP port.

### Server: start HTTP MCP

```bash
export AGENTCORE_MCP_TOKEN_SECRET='replace-with-a-long-random-secret'
export AGENTCORE_MCP_HTTP_PUBLIC_URL='http://agentcore.example.internal:32500'
## When Compose Postgres is up:
## export AGENTCORE_MCP_STORE_MODE=postgres
## export AGENTCORE_DATABASE_URL=...
agentcore mcp serve-http --host 0.0.0.0 --port 32500
```

Keep this process running (systemd/supervisor in real deployments).

Optional: run project-profile HTTP API for bootstrap (`server.url` in connect.yaml). Port profile default for project-profile is `AGENTCORE_PROJECT_PROFILE_PORT` (`32194`).

### Dev host: `~/.agentcore/connect.yaml`

```yaml
server:
  url: http://agentcore.example.internal:32194
  mcp_http_url: http://agentcore.example.internal:32500

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

Export API token if needed:

```bash
export AGENTCORE_TOKEN='...'
```

The MCP bearer token is **minted by bootstrap** (scoped `ac1.…` HMAC) when `AGENTCORE_MCP_TOKEN_SECRET` is set on the server, and written into IDE `headers` — not as a database password.

### Dev host: run connect

```bash
cd /opt/MyApp
agentcore connect
```

Expected: prints `transport: streamable_http (http://agentcore.example.internal:32500/mcp)`.

What lands in MCP config (shape):

```json
{
  "mcpServers": {
    "AgentCore-Programming": {
      "url": "http://agentcore.example.internal:32500/mcp",
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

## Example 3 — Both configured (HTTP preferred, SSH fallback)

```yaml
server:
  url: http://agentcore.example.internal:32194
  mcp_http_url: http://agentcore.example.internal:32500
  ssh: ops@agentcore.example.internal
  remote_root: /opt/AgentCore

auth:
  token_env: AGENTCORE_TOKEN
  ssh_key: ~/.ssh/id_ed25519_agentcore

scope:
  tenant: acme
  workspace: eng

connect:
  prefer_http: true
```

- If HTTP MCP is healthy and bootstrap returns headers → **HTTP**.
- If HTTP is down / incomplete → **SSH** (when `ssh` is set).
- Force SSH anytime with `prefer_http: false`.

---

## Shared config reference (`~/.agentcore/connect.yaml`)

| Key | Required | Meaning |
| --- | --- | --- |
| `server.ssh` | For SSH mode | `user@host` of AgentCore server |
| `server.remote_root` | For SSH mode | AgentCore install path (default `/opt/AgentCore`) |
| `server.url` | Optional | project-profile API base for bootstrap / ingest |
| `server.mcp_http_url` | For HTTP mode | Public base of MCP HTTP (port `32500` by default) |
| `auth.ssh_key` | Recommended for SSH | Path to private key |
| `auth.token_env` | Optional | Env var name holding API bearer for bootstrap |
| `scope.tenant` / `workspace` | Yes | Platform scope |
| `scope.project` | Optional | Defaults to **cwd directory name** |
| `usage_profile` | Optional | Default `programming-cursor-mcp` |
| `clients` | Optional | `all` or comma list (`cursor,vscode,…`) |
| `source.server_path` | Optional | Code path **on AgentCore server** for ingest |
| `source.git` | Optional | `{ remote, branch }` registration |
| `connect.prefer_http` | Optional | Default `true` |
| `connect.register` | Optional | Default `true` |
| `connect.smoke_test` | Optional | Default `true` |
| `connect.ingest` | Optional | `off` \| `optional` \| `always` |

Environment overrides (examples): `AGENTCORE_CONNECT_SSH`, `AGENTCORE_CONNECT_URL`, `AGENTCORE_CONNECT_MCP_HTTP_URL`, `AGENTCORE_CONNECT_TENANT`, `AGENTCORE_CONNECT_PROJECT`.

CLI:

```bash
agentcore connect --init
agentcore connect
agentcore connect --project myapp --clients cursor,vscode
agentcore connect --dry-run
agentcore client list-mcp-clients
```

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
2. SSH: interactive wizard uses password **once** to install a dedicated AgentCore key; afterward **keys only** — BatchMode must succeed without a prompt. Re-auth with `agentcore connect --edit` (replaces pubkey).
3. HTTP without TLS: private network + firewall on the MCP port; prefer reverse-proxy TLS for anything beyond a closed lab.
4. Prefer scoped tokens (`AGENTCORE_MCP_TOKEN_SECRET`) over a single shared `AGENTCORE_MCP_HTTP_TOKEN`.
5. Keep `connect.yaml` mode `600`; do not commit live bearer tokens.
6. Prefer non-root SSH users on the AgentCore host.

## Related Documents

- Continued in `docs/08-software-engineering-architecture/41-one-command-cross-platform-agent-onboarding-continued.md`
