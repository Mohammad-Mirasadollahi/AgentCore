---
doc_id: ac.doc.sea.agentcore-cli-command-reference
title: "42 - AgentCore CLI Command Reference"
doc_type: runbook
status: active
schema_version: "1.0"
owner: platform-product
summary: >-
  Operator reference for every agentcore subcommand: why it exists, required
  vs optional flags, examples, what files or stores change, and mandatory sync
  filter config (wildcards + built-in language excludes).
tags:
  - cli
  - agentcore
  - operator
  - runbook
  - mcp
phase: "08-software-engineering-architecture"
canonical_path: docs/08-software-engineering-architecture/42-agentcore-cli-command-reference.md
related_docs:
  - docs/08-software-engineering-architecture/36-agentcore-cli.md
  - docs/08-software-engineering-architecture/39-local-install-runbook.md
  - docs/08-software-engineering-architecture/41-one-command-cross-platform-agent-onboarding.md
  - docs/08-software-engineering-architecture/40-remote-dev-client-mcp-wiring.md
  - docs/08-software-engineering-architecture/35-usage-profile-and-cursor-mcp-onboarding.md
  - docs/07-code-knowledge-graph/35-wedge-operator-connect-runbook.md
doc_version: "1.1.0"
audience:
  - engineer
  - operator
lifecycle_lane: current
concern_lane: runbook
audience_lane:
  - platform-engineering
  - agents
authority: normative
visibility: internal
language: en
security_classification: internal
---

# 42 - AgentCore CLI Command Reference

## Purpose

This document is the **canonical operator reference** for the `agentcore` CLI: every shipped subcommand, why it exists, which flags are required, a copy-paste example, and what changes on disk or in stores when you run it.

For install / PATH / package layout, see [36-agentcore-cli.md](./36-agentcore-cli.md). For remote MCP onboarding flows, see [41](./41-one-command-cross-platform-agent-onboarding.md).

## How to read each command

| Field | Meaning |
| --- | --- |
| **Why** | Problem this command solves (reason it exists) |
| **Required** | Flags / preconditions that must be present or the command exits |
| **Optional** | Common optional flags |
| **Example** | Typical invocation |
| **What changes** | Files, env, graph data, or processes affected |
| **If you change X** | What happens when you re-run with different IDs or flags |

## Scope IDs (tenant / workspace / project)

AgentCore isolates graph and project state by three string IDs:

| ID | Role |
| --- | --- |
| `tenant` | Org / customer boundary |
| `workspace` | Team or environment inside a tenant |
| `project` | One application / repo under a workspace |

**You choose these IDs.** Nothing mints a tenant id from your username. Use lowercase letters, digits, and hyphens (slug style), e.g. `acme`, `eng`, `payments`.

### Where IDs are set

| Step | Command / file | Sets |
| --- | --- | --- |
| First time (recommended) | `agentcore init --tenant … --workspace … --path …` | `~/.agentcore/identity.yaml`, repo `.env`, software `paths`, optional merge into `connect.yaml`, local project state |
| Connect config | `~/.agentcore/connect.yaml` → `scope:` | Used when identity/env do not already pin scope |
| Per-command override | `--tenant` / `--workspace` / `--project` | Highest priority for that run only |
| Env | `AGENTCORE_TENANT_ID`, `AGENTCORE_WORKSPACE_ID`, `AGENTCORE_PROJECT_ID` | After CLI flags; often written by `init` into `.env` |

### Resolution order (everyday commands)

For `status`, `sync`, `purge` (and other commands that call operator defaults):

1. CLI flags (`--tenant` / `--workspace` / `--project`)
2. Env (`AGENTCORE_*` from shell or loaded `.env` / `.env.local`)
3. `~/.agentcore/identity.yaml`
4. `~/.agentcore/connect.yaml` → `scope`
5. Dogfood defaults (`tenant=agentcore`, `workspace=dev`, `project=<cwd name>`)

**If you change IDs** (new `--tenant` / re-run `init --force` with different values): later `sync` / MCP tools read and write a **different scope**. Old graph data under the previous IDs remains until you `purge` that old scope (or wipe stores). IDE MCP configs keep the env baked in at `connect` time until you re-run `connect`.

### Required vs optional scope flags

| Command family | Scope flags |
| --- | --- |
| `init` | **`--tenant`, `--workspace`, and at least one `--path` required.** `--project` optional (default: current directory name) |
| `paths` | Uses active identity; `add` / `remove` take path arguments |
| `status` / `sync` / `purge` | Optional scope flags if identity/env/connect already set; `sync` uses pinned software paths |
| `inventory` | **No dashed mode flags.** Word modes only (`detail`, `save <path>`). Scope from identity/env/connect; uses pinned software paths |
| `docs-standards` | **No dashed mode flags.** Word modes only (`detail`, `save <path>`). Scans repo `docs/**/*.md` against documentation standards |
| `stats` | **No dashed mode flags.** Word modes only (`detail`, `save <path>`). Scope from identity/env/connect; pinned software paths + sync filters |
| `project register|activate|show|effective` | **Required** (`--tenant` `--workspace` `--project`) |
| `cursor export`, `mcp serve`, `graph *`, `client wire-remote` | **Required** unless noted |

## First-time dogfood flow (same host)

```bash
cd /opt/AgentCore
bash install.sh                    # once
agentcore init --tenant acme --workspace eng --path /opt/AgentCore
agentcore connect --local
agentcore status
# Required before first sync:
# cp agentcore.sync.yaml.example agentcore.sync.yaml   # then edit (file is gitignored)
agentcore sync
```

| Step | Why |
| --- | --- |
| `init` | You pick durable IDs **and software path(s)** once so later commands stay short |
| `connect --local` | Write IDE MCP configs pointing at this checkout’s stdio gateway |
| `status` | Confirm Postgres/Neo4j/graph/MCP/paths before syncing |
| Sync filter file | `agentcore.sync.yaml` (or `.agentcore/sync.yaml`) must exist at each sync root — see [Sync filters](#sync-filters) |
| `sync` | Load each pinned software path into the code graph for that scope |

---

## Command catalog

### `agentcore version` / `agentcore --version`

| | |
| --- | --- |
| **Why** | Confirm which CLI binary and repo root you are using |
| **Required** | None |
| **Example** | `agentcore version` |
| **What changes** | Nothing (read-only) |

### `agentcore doctor`

| | |
| --- | --- |
| **Why** | Catch broken venv, missing imports, profiles, or PATH before deeper work |
| **Required** | None |
| **Example** | `agentcore doctor` |
| **What changes** | Nothing (diagnostics only) |

### `agentcore init`

| | |
| --- | --- |
| **Why** | Create your first tenant + workspace with **IDs you choose**, pin **software path(s)** to sync, register a project, and pin defaults for later commands |
| **Required** | `--tenant`, `--workspace`, at least one `--path` (existing directory; repeatable) |
| **Optional** | `--project` (default: cwd name), `--name` (display), `--project-name`, `--usage-profile`, `--force` |
| **Example** | `agentcore init --tenant acme --workspace eng --path /opt/MyApp --project payments` |
| **What changes** | Writes `~/.agentcore/identity.yaml` (scope + `paths`); upserts `AGENTCORE_*` and `AGENTCORE_SOFTWARE_PATHS` in repo `.env`; may merge scope into `~/.agentcore/connect.yaml`; writes `.agentcore/projects/<tenant>/<workspace>/<project>.json` including `paths` |
| **If you change IDs** | Without `--force`, re-run shows current scope/paths. With `--force`, identity/env/connect scope are replaced; graph data for the old scope is **not** deleted automatically |
| **Edit paths later** | `agentcore paths list` / `add` / `remove` — see below |

### `agentcore paths`

| | |
| --- | --- |
| **Why** | Show or edit the software root directories that `agentcore sync` indexes |
| **Subcommands** | `list`, `add <path…>`, `remove <path…>` |
| **Example** | `agentcore paths add /opt/OtherApp` · `agentcore paths remove /opt/OldApp` |
| **What changes** | Updates identity `paths`, project JSON `paths`, and `.env` `AGENTCORE_SOFTWARE_PATHS` |
| **On remove** | Prints a **warning**: previously synced graph data for removed trees **remains** until `agentcore purge --yes`. Removing a path only stops future sync from that root. Cannot remove the last path |

### `agentcore status`

| | |
| --- | --- |
| **Why** | One-shot health: resolved scope, infra probes, graph counts, MCP config presence, next-step hints |
| **Required** | None if defaults resolve; otherwise pass scope flags |
| **Optional** | `--tenant` `--workspace` `--project`, `--json`, `--verbose` |
| **Example** | `agentcore status` |
| **What changes** | Nothing (read-only). Exit hints may tell you to `init` / `sync` / start Compose |

### `agentcore inventory`

**Operator UX law (applies to everyone — humans and agents):** for `inventory`, do **not** use dashed flags for modes. Use word modes only. Prefer the verb **`save`** (never `out`) when writing a report file. Keep console output to **percentages + top 10 files with models**; put full file↔model lists only via `save`.

| | |
| --- | --- |
| **Why** | Show how much of the **client software** roots (pinned via `init` / `paths`) is already in AgentCore vs still outstanding, split into **Code** and **Docs** |
| **Required** | Sync filter file at each root (same as `sync`). At least one software path. Scope from identity/env/connect (no dashed scope flags on this command) |
| **Modes** | **Normal** (default): percents + **top 10** files with models. **Detail**: same top 10 with embed/docs models, status, and per-file symbol coverage. **Save**: write full file↔model lists to a path |
| **Example** | `agentcore inventory` · `agentcore inventory detail` · `agentcore inventory save /tmp/inventory-details.txt` · `agentcore inventory detail save /tmp/inventory-details.txt` |
| **What you see** | Code/Docs split into **done** (up to date), **edited** (was ingested, then changed / pending — needs `agentcore sync`), and **remaining** (never ingested); percents for each; **top 10** lists with `models=` and `reason=` (`content_changed` or `pending`). `save` writes the **full** lists |
| **What changes** | Nothing on the graph (read-only). `save` only writes the report file you named |

### `agentcore docs-standards`

**Operator UX law:** same word-mode pattern as `inventory` — no dashed mode flags; use `detail` and `save <path>` only.

| | |
| --- | --- |
| **Why** | Show which Markdown files under repo `docs/` fail AgentCore documentation standards (frontmatter, lanes, H1/title, Purpose H2, size budgets, design Mermaid) and what **percent of the tree** that is |
| **Required** | None (uses `AGENTCORE_ROOT` / package-derived repo root) |
| **Modes** | **Normal**: conforming/nonconforming percents + **top 10** nonconforming paths. **Detail**: same top 10 with issue codes. **Save**: write full nonconforming + conforming lists to a path |
| **Example** | `agentcore docs-standards` · `agentcore docs-standards detail` · `agentcore docs-standards save /tmp/docs-standards.txt` · `agentcore docs-standards detail save /tmp/docs-standards.txt` |
| **What you see** | Totals and percents; top nonconforming files; optional per-issue detail; `save` writes the full report |
| **What changes** | Nothing on the graph (read-only). `save` only writes the report file you named |
| **Normative refs** | `docs/00-master-plan/06-professional-documentation-standard.md`, `08-documentation-structure-and-machine-ingest-standard.md`, `09-documentation-classification-and-lanes.md` |

### `agentcore stats`

**Operator UX law:** same word-mode pattern as `inventory` — no dashed mode flags; use `detail` and `save <path>` only.

| | |
| --- | --- |
| **Why** | Count **code + docs** on pinned software roots, show **language mix** (files, bytes, % of code), and **processed vs remaining** percents (done / edited / remaining + LLM symbols) |
| **Required** | Sync filter file at each root (same as `sync` / `inventory`). At least one software path. Scope from identity/env/connect |
| **Modes** | **Normal**: totals + processing percents + per-language summary. **Detail**: same with per-language done/edited/remaining counts. **Save**: full report including per-root language tables |
| **Example** | `agentcore stats` · `agentcore stats detail` · `agentcore stats save /tmp/stats.txt` · `agentcore stats detail save /tmp/stats.txt` |
| **What you see** | Code/docs file counts and sizes; done/edited/remaining percents; each language’s share of code files (and bytes in detail/save) |
| **What changes** | Nothing on the graph (read-only). `save` only writes the report file you named |

### `agentcore connect`

| | |
| --- | --- |
| **Why** | Materialize coding-agent MCP configs from `~/.agentcore/connect.yaml` (SSH, HTTP, or same-host local) |
| **Required** | For normal connect: a connect config (create with `--init`). For `--local`: AgentCore checkout available |
| **Optional** | `--init`, `--local`, `--config`, `--project`, `--ssh`, `--server`, `--clients`, `--include-user-clients`, `--dry-run`, `--tenant`, `--workspace`, `--remote-root` |
| **Example (template)** | `agentcore connect --init` then edit `~/.agentcore/connect.yaml` |
| **Example (dogfood)** | `agentcore connect --local` (scope from `init` / identity / env — not hardcoded) |
| **Example (remote)** | `agentcore connect` from the app repo after editing connect.yaml |
| **What changes** | Writes/merges MCP JSON under project `.cursor/` / `.vscode/` (and optional user-global clients); may register project on server; may ingest/sync depending on connect options |
| **If you change scope in connect.yaml** | Re-run `connect` so MCP env and registration match the new scope |

### `agentcore sync`

| | |
| --- | --- |
| **Why** | Load or refresh the code graph for a repo root (auto chooses full vs incremental vs noop) |
| **Required** | Sync filter file at each sync root (see [Sync filters](#sync-filters)). At least one software path from `init` / `paths` (or override with `--path`). Scope defaults if identity/env already set |
| **Optional** | `--path` (repeatable override; default = pinned paths), bare `max-file <n>`, `--progress-interval`, `--allow-cloud-llm`, `--exclude-dir`, `--include-path`, `--include-ext`, scope flags |
| **Example** | `agentcore sync` or `agentcore sync --path /opt/MyApp` |
| **What changes** | Phase 1: upserts code symbols/edges/embeddings. Phase 2 (when `docs.match` is non-empty): indexes human Markdown in docs-sync and projects `DOCUMENTED_BY` for resolved `linked_symbols` |
| **If you change `--path` or scope** | You sync a different tree or different isolation bucket; previous scope data remains |
| **Software preflight** | If Compose/MCP are not fully running, an interactive TTY asks `Start software now? [y/N]`. `y`/`yes` runs `agentcore service start` first, then sync. Decline or non-TTY → exit with a hint to start services manually. After start, prints each component’s **start time to the second** (`postgres`, `neo4j`, `MCP HTTP`) |
| **Cloud LLM consent** | Non-private LLM routes (non-loopback host or non-local model prefix) fail closed until the operator consents. Interactive TTY shows **tenant**, **workspace**, **project**, **software path(s)**, API host, and models, then requires **two** yes answers: (1) allow cloud LLM for this run, (2) confirm the scope IDs in use. Sync starts only after both. `--allow-cloud-llm` skips both prompts (scripts). Non-TTY without the flag → exit with a hint |
| **Before sync** | Prints the same **Totals / Processing / By language** snapshot as `agentcore stats` (code+docs counts, done/edited/remaining, LLM symbols) so you see the work before consent and ingest |
| **Cold start** | Default local BGE embeddings may download/load a HuggingFace model on first sync (can take minutes). For a fast operator check: `AGENTCORE_EMBEDDING_PROVIDER=stub agentcore sync max-file 50` |
| **Progress** | While syncing, prints `%` / **code** or **docs** done/total / ETA / rate about every **30s** (override with `--progress-interval`). Phase 1 (code ingest) and Phase 2 (human docs link) each get their own progress block; the tracker resets rate/ETA between phases. **done/total** counts **new + changed** only (excludes already-indexed `unchanged_recheck`); full inventory totals stay in the Before sync stats. Each block is blank-line separated and includes wall-clock `at YYYY-MM-DD HH:MM:SS` plus `elapsed`. Also shows **graph prior** counts and **queue** (`new` / `changed` / `unchanged_recheck`). **ETA** uses a blend of **lifetime average** (`done/elapsed`, weight 0.65) and **recent-window average** (~60s, weight 0.35), lightly EWMA-smoothed — resists one slow file, still tracks sustained slowdowns; before any completion, rate is marked `provisional`. `agentcore status` shows a Live sync section if another sync is running |
| **Usage log** | Each sync writes one JSON file named by **execution time** (`YYYY-MM-DD_HH-MM-SS.json`) under `AGENTCORE_SYNC_USAGE_LOG_DIR` (default `.agentcore/sync-usage`). Record field `execution_at` is date+time to the second. Folder cap: `AGENTCORE_SYNC_USAGE_LOG_DIR_MAX_BYTES` (default **5 GiB**, FIFO deletes oldest files). Gitignored |
| **Filters** | Mandatory YAML + wildcards + built-in language excludes — [Sync filters](#sync-filters) |

### `agentcore llm test`

| | |
| --- | --- |
| **Why** | Verify which LiteLLM model the root `.env` resolves and that a one-shot completion works |
| **Required** | None (uses `AGENTCORE_LITELLM_*` from `.env`) |
| **Optional** | `--prompt` (default `Hi`), `--model` (override `AGENTCORE_LITELLM_DEFAULT_MODEL`) |
| **Example** | `agentcore llm test` |
| **What you see** | JSON with `ok`, `configured_model`, `model`, `api_base`, `api_key_configured`, `reply`, `usage` (or `error` on failure) |
| **What changes** | Nothing local; one provider completion request |

### `agentcore llm sessions`

| | |
| --- | --- |
| **Why** | Inspect in-flight / recent RPM LiteLLM sessions during sync or from the running code-graph service |
| **Required** | None |
| **Example** | `agentcore llm sessions` |
| **What changes** | Nothing (read-only) |

### `agentcore purge`

| | |
| --- | --- |
| **Why** | Wipe graph data for one scope so a clean `sync` can rebuild |
| **Required** | `--yes` (safety latch) |
| **Optional** | Scope flags |
| **Example** | `agentcore purge --yes` |
| **What changes** | Deletes graph content for that tenant/workspace/project (not your source files; not unrelated scopes) |
| **If you omit `--yes`** | Command refuses to wipe |

### `agentcore destroy-profile`

| | |
| --- | --- |
| **Why** | Remove a chosen scope **ID** and all **AgentCore profile / platform data** tied to it when you are done with that profile |
| **Required** | Interactive terminal: type **two different** confirmation phrases (not `--yes` flags). Scope from flags or identity/env defaults |
| **Optional** | `--tenant` `--workspace` `--project` |
| **Example** | `agentcore destroy-profile --tenant acme --workspace eng --project agentcore` then type `DELETE PROFILE DATA`, then type `acme/eng/agentcore` |
| **What is deleted (profile data only)** | Code-graph symbols/edges/embeddings for this scope; `.agentcore/projects/...` Usage Profile state; `~/.agentcore/identity.yaml` if it pins this scope; matching `AGENTCORE_*` scope keys in repo `.env`; matching `scope` in `connect.yaml`; AgentCore entries in this repo’s IDE `mcp.json` files |
| **What is NOT deleted** | Your **source code**, git history, unrelated files, or data for other tenant/workspace/project IDs |
| **If a confirmation is wrong or stdin is not a TTY** | Exits; **nothing** is deleted |
| **Afterward** | Run `agentcore init --tenant … --workspace … --path …` again to choose new IDs/roots, then `connect` / `sync` |

### `agentcore list-profiles`

| | |
| --- | --- |
| **Why** | See which local **tenant/workspace/project** profiles exist and which one is active (before destroy or switch) |
| **Required** | None |
| **Optional** | `--json`, `--verbose` |
| **Example** | `agentcore list-profiles` |
| **What you see** | Active scope; each registered profile’s IDs, Usage Profile id, status, display name; `*` marks the active row. Also surfaces identity-only pins with no project file yet |
| **Not the same as** | `agentcore profile list` (catalog of Usage Profile *templates*). `list-profiles` = your local instances |
| **What changes** | Nothing (read-only) |

### `agentcore profile list` / `agentcore profile show <id>`

| | |
| --- | --- |
| **Why** | Inspect Usage Profile catalog (which MCP tools / packs a profile enables) |
| **Required** | `show` needs `profile_id` |
| **Example** | `agentcore profile list` · `agentcore profile show programming-cursor-mcp` |
| **What changes** | Nothing (read-only) |

### `agentcore project register`

| | |
| --- | --- |
| **Why** | Create local project state without going through `init` (multi-project / explicit setup) |
| **Required** | `--tenant` `--workspace` `--project` |
| **Optional** | `--name`, `--usage-profile`, `--domain-pack`, `--feature-profile`, `--force` |
| **Example** | `agentcore project register --tenant acme --workspace eng --project payments --name "Payments" --usage-profile programming-cursor-mcp` |
| **What changes** | Writes `.agentcore/projects/<tenant>/<workspace>/<project>.json` |
| **If you change IDs** | Creates a **new** project file; does not migrate the old one |

### `agentcore project activate`

| | |
| --- | --- |
| **Why** | Bind a Usage Profile onto an existing project state |
| **Required** | Scope flags + `--usage-profile` |
| **Example** | `agentcore project activate --tenant acme --workspace eng --project payments --usage-profile programming-cursor-mcp` |
| **What changes** | Updates the project state file’s profile fields |

### `agentcore project show` / `agentcore project effective`

| | |
| --- | --- |
| **Why** | Inspect saved state vs resolved effective profile |
| **Required** | Scope flags |
| **Example** | `agentcore project show --tenant acme --workspace eng --project payments` |
| **What changes** | Nothing (read-only) |

### `agentcore cursor export`

| | |
| --- | --- |
| **Why** | Export an `mcpServers` JSON fragment for Cursor without full `connect` |
| **Required** | Scope flags |
| **Optional** | `--out` |
| **Example** | `agentcore cursor export --tenant acme --workspace eng --project payments --out ~/.cursor/agentcore-mcp.json` |
| **What changes** | Writes the `--out` file when provided; otherwise prints JSON |

### `agentcore mcp tools`

| | |
| --- | --- |
| **Why** | List MCP tool names for a Usage Profile (verify catalog wiring) |
| **Required** | None |
| **Optional** | `--usage-profile` (default `programming-cursor-mcp`) |
| **Example** | `agentcore mcp tools` |
| **What changes** | Nothing (read-only) |

### `agentcore mcp serve`

| | |
| --- | --- |
| **Why** | Run the MCP gateway on **stdio** for one project scope (what IDEs spawn) |
| **Required** | Scope flags |
| **Optional** | `--usage-profile` |
| **Example** | `agentcore mcp serve --tenant acme --workspace eng --project payments` |
| **What changes** | Long-running process; talks MCP on stdin/stdout. Does not rewrite IDE configs |

### `agentcore mcp serve-http`

| | |
| --- | --- |
| **Why** | Run Streamable HTTP MCP for concurrent agents (Phase B) |
| **Required** | Server env for token/public URL when used remotely (see doc 41) |
| **Optional** | `--host`, `--port`, `--usage-profile` |
| **Example** | `agentcore mcp serve-http --host 0.0.0.0 --port 32500` |
| **What changes** | Binds an HTTP listener; clients use bearer auth configured at connect time |

### `agentcore service start` / `stop` / `restart` / `status` / `detail`

| | |
| --- | --- |
| **Why** | One operator command for local Compose infra (postgres + neo4j) **and** the MCP HTTP backend daemon |
| **Required** | Prior `bash install.sh` (compose `.env.local` + Docker). Repo root or `AGENTCORE_ROOT` |
| **Optional** | `status --json` · `detail --json` |
| **Example** | `agentcore service start` · `agentcore service status` · `agentcore service detail` · `agentcore service restart` |
| **What changes** | Starts/stops Compose profile `core` services; backgrounds MCP HTTP (pid/log under `.agentcore/run/`). If no MCP token env is set, creates `.agentcore/mcp-http.secret` |
| **Status fields** | `status` / `detail` show **Restarted** (latest start among running postgres/neo4j/MCP HTTP) and **UpTime** since that time |
| **Exit** | `status` / `detail` exit `1` unless State is `all running`. Failed `start`/`restart` prints the MCP HTTP log tail automatically |
| **Diagnose** | When State is not `all running`, run `agentcore service detail` to see MCP HTTP log (and Compose logs for unhealthy containers) |

### `agentcore boot enable` / `disable`

| | |
| --- | --- |
| **Why** | Start AgentCore automatically on machine boot via systemd |
| **Required** | `systemctl` available; write access to unit path (system unit needs root/sudo; `--user` does not) |
| **Optional** | `--user` — install `~/.config/systemd/user/agentcore.service` instead of `/etc/systemd/system/` |
| **Example** | `sudo $(which agentcore) boot enable` · `agentcore boot enable --user` · `agentcore boot disable` |
| **What changes** | Writes a oneshot systemd unit that runs `agentcore service start` / `stop`, then `systemctl enable` / `disable`. User units may need `loginctl enable-linger $USER` to run at boot without an interactive login |
| **Note** | Distinct from `agentcore status` (graph/sync view). Use `agentcore service status` for process health |

### `agentcore client list-mcp-clients`

| | |
| --- | --- |
| **Why** | Show which IDE/agent MCP config targets the CLI knows how to write |
| **Required** | None |
| **Example** | `agentcore client list-mcp-clients` |
| **What changes** | Nothing |

### `agentcore client wire-remote`

| | |
| --- | --- |
| **Why** | On a **dev host**, write MCP configs that SSH into a remote AgentCore install and run `mcp serve` |
| **Required** | Scope flags, `--ssh`, `--remote-root` |
| **Optional** | `--out`, `--project-dir`, `--clients`, `--register`, `--dry-run`, … |
| **Example** | `agentcore client wire-remote --tenant acme --workspace eng --project payments --ssh ops@agentcore --remote-root /opt/AgentCore` |
| **What changes** | Merges MCP JSON on the client; optionally registers the project on the server |
| **Prefer today** | `agentcore connect` when `connect.yaml` is set (higher-level) |

### `agentcore client doctor-remote`

| | |
| --- | --- |
| **Why** | Verify SSH + remote Python/venv can reach the MCP serve entrypoint |
| **Required** | `--ssh`, `--remote-root` |
| **Example** | `agentcore client doctor-remote --ssh ops@agentcore --remote-root /opt/AgentCore` |
| **What changes** | Nothing (remote probe only) |

### `agentcore path install`

| | |
| --- | --- |
| **Why** | Put `agentcore` on `~/.local/bin` (and optionally shell rc PATH) |
| **Required** | Working `.venv/bin/agentcore` from install |
| **Optional** | `--shell-rc` (e.g. `.bashrc`) |
| **Example** | `agentcore path install --shell-rc .bashrc` |
| **What changes** | Symlink under `~/.local/bin`; may append PATH export to shell rc |

### `agentcore ports show` / `agentcore ports check`

| | |
| --- | --- |
| **Why** | Show or bind-check ports from the port profile before starting services |
| **Required** | None |
| **Optional** | `--profile` path |
| **Example** | `agentcore ports show` · `agentcore ports check` |
| **What changes** | Nothing persistent; `check` exits `1` if any port cannot bind |

### `agentcore graph ingest`

| | |
| --- | --- |
| **Why** | Explicit ingest of a path (lower-level than `sync`; useful in scripts/smokes) |
| **Required** | Scope flags, `--path` |
| **Optional** | `--max-files` |
| **Example** | `agentcore graph ingest --tenant acme --workspace eng --project payments --path .` |
| **What changes** | Same class of graph writes as sync for that path/scope |

### `agentcore graph freshness`

| | |
| --- | --- |
| **Why** | Show pending-sync / freshness for a scope |
| **Required** | Scope flags |
| **Optional** | `--mark-pending <file>` |
| **Example** | `agentcore graph freshness --tenant acme --workspace eng --project payments` |
| **What changes** | Read-only unless `--mark-pending` is set |

### `agentcore graph explore` / `agentcore graph hybrid`

| | |
| --- | --- |
| **Why** | Operator smoke for retrieve packs without an IDE |
| **Required** | Scope flags, `--query` |
| **Optional** | `--top-k` |
| **Example** | `agentcore graph explore --tenant acme --workspace eng --project payments --query "login auth"` |
| **What changes** | Nothing durable (query only) |

### `agentcore graph smoke`

| | |
| --- | --- |
| **Why** | One-process ingest + freshness + hybrid + explore for lab verification |
| **Required** | Scope flags, `--path` |
| **Optional** | `--query`, `--max-files` |
| **Example** | `agentcore graph smoke --tenant acme --workspace eng --project payments --path . --query "login"` |
| **What changes** | Performs an ingest into the graph CLI backend |

### `agentcore graph watch`

| | |
| --- | --- |
| **Why** | Batched pending-sync poll sidecar (debounced; **not** per-keystroke continuous indexing) |
| **Required** | Scope flags, `--path` |
| **Optional** | `--interval`, `--debounce`, `--max-wait`, `--once` |
| **Example** | `agentcore graph watch --tenant acme --workspace eng --project payments --path . --once` |
| **What changes** | May flush pending sync batches into the graph while running |

Default graph CLI backend is in-memory (`AGENTCORE_GRAPH_CLI_BACKEND=memory`). Set `AGENTCORE_GRAPH_CLI_BACKEND=neo4j` (plus Neo4j env) for durable Compose labs. See [wedge connect runbook](../07-code-knowledge-graph/35-wedge-operator-connect-runbook.md).

---

## Sync filters

`agentcore sync` **refuses to run** unless a filter file exists under the sync root (`--path`). Filters are **exclude-only**, with **separate** lists for code vs docs.

### Required files (any one)

| Path | Typical use |
| --- | --- |
| `agentcore.sync.yaml` | Local operator copy (**gitignored**; create via `cp` from example) |
| `agentcore.sync.yml` | Same as above |
| `.agentcore/sync.yaml` | Local-only override (under gitignored `.agentcore/`) |

Template (tracked): repo-root `agentcore.sync.yaml.example`.

```bash
cp agentcore.sync.yaml.example agentcore.sync.yaml
# edit code.exclude / docs.match / docs.exclude
agentcore sync --path .
```

### Preferred schema

| Section | Role |
| --- | --- |
| `code.exclude` | Skip noise from **code** discovery (dirs + globs) |
| `code.include_extensions` | Which language suffixes count as source (not a path allow-list) |
| `docs.match` | Wildcard set of human docs (default idea: `**/*.md`, `**/*.mdx`) |
| `docs.exclude` | Docs-only skips (independent from `code.exclude`) |

Do **not** list `docs` under `code.exclude` just to “enable” documentation — Markdown is not a code extension. Use `docs.match: []` or `docs.enabled: false` to disable Phase 2.

Path allow-lists (`include_paths`) are **legacy**; prefer exclude-only. Top-level `exclude` still maps to code excludes for older configs.

### Merge order (lowest → highest priority)

1. Repo `agentcore.sync.yaml` (or `.yml`) — **source of truth for excludes**
2. Local `.agentcore/sync.yaml` (if present; last key wins for overlapping top-level keys)
3. Env: `AGENTCORE_SYNC_EXCLUDE_DIRS`, `AGENTCORE_SYNC_DOC_MATCH`, `AGENTCORE_SYNC_DOC_EXCLUDE`, `AGENTCORE_SYNC_INCLUDE_EXTENSIONS`
4. CLI: `--exclude-dir`, `--include-ext` (and legacy `--include-path`)

There is **no hardcoded product exclude list in Python**. Operators edit `code.exclude` / `docs.exclude` in the YAML. Hidden directories whose names start with `.` are still skipped during tree walks as a filesystem safety (e.g. `.git`).

### Wildcards

Patterns use `fnmatch` with `**` = any depth. Leading `**/` matches zero or more directories.

| Pattern | Typical use |
| --- | --- |
| `**/*.md` | Every Markdown file under the sync root (`docs.match`) |
| `**/tests/**` | Skip tests trees (`code.exclude`) |
| `**/*.min.js` | Skip minified JS |
| `**/CHANGELOG.md` | Skip changelog from docs Phase 2 |

Brace expansion (`*.{ts,tsx}`) is **not** supported — list two patterns.

### Minimal example

```yaml
code:
  exclude:
    - tests
    - "**/__pycache__/**"
    - "**/__init__.py"
    - "**/generated/**"
    - "**/*.min.js"
  include_extensions:
    - .py
    - .ts
    - .tsx

docs:
  match:
    - "**/*.md"
    - "**/*.mdx"
  exclude:
    - "**/CHANGELOG.md"
```

### CLI / env extras

```bash
agentcore sync --exclude-dir generated --exclude-dir '**/*.spec.ts'
AGENTCORE_SYNC_EXCLUDE_DIRS='tests,**/generated/**' agentcore sync
AGENTCORE_SYNC_DOC_MATCH='**/*.md,**/*.mdx' agentcore sync
AGENTCORE_SYNC_DOC_EXCLUDE='**/CHANGELOG.md' agentcore sync
```

---

## Destructive and safety notes

| Action | Safety |
| --- | --- |
| `purge` | Requires `--yes`; scopes wipe only (graph data) |
| `paths remove` | Warns that graph data for removed trees **remains** until `purge`; cannot remove the last path |
| `destroy-profile` | Two different typed confirmations in a TTY; deletes profile/platform data for one scope; **never** source code |
| `init --force` | Overwrites identity pin; does not auto-purge old graph |
| Changing tenant/workspace/project | Isolates new data; old scope stays until purged or destroyed |
| `connect` | Overwrites/merges MCP config files for selected clients |

Do not put secrets in docs or chat examples. MCP bearer secrets belong in env / connect auth, not committed files.

## Implementation map

| Area | Path |
| --- | --- |
| Parser | `backend/packages/agentcore_cli/parser/` |
| Dispatch | `backend/packages/agentcore_cli/main.py` |
| Commands | `backend/packages/agentcore_cli/commands/` |
| Sync filter merge | `backend/packages/agentcore_cli/sync_config.py` |
| Software paths | `backend/packages/agentcore_cli/software_paths.py` |
| Docs link Phase 2 | `backend/packages/agentcore_cli/docs_link_sync.py` |
| File discovery | `backend/services/code-graph-service/src/code_graph_service/domain/repo_discovery.py` |
| Doc discovery | `backend/services/code-graph-service/src/code_graph_service/domain/doc_discovery.py` |
| Human doc projection | `backend/services/code-graph-service/src/code_graph_service/application/ingest/human_docs.py` |
| Operator exclude list | `agentcore.sync.yaml` / `agentcore.sync.yaml.example` |
| Scope defaults | `backend/packages/agentcore_cli/cli_defaults.py` |
| Identity | `backend/packages/agentcore_cli/identity.py` |
| Tests | `tests/backend/tools/agentcore-cli/` (incl. `test_sync_config.py`, `test_docs_link_sync.py`); `tests/backend/services/code-graph-service/test_human_docs_ingest.py` |

## Related Documents

- [36-agentcore-cli.md](./36-agentcore-cli.md) — install, PATH, package overview
- [39-local-install-runbook.md](./39-local-install-runbook.md) — `install.sh`
- [41-one-command-cross-platform-agent-onboarding.md](./41-one-command-cross-platform-agent-onboarding.md) — connect UX
- [40-remote-dev-client-mcp-wiring.md](./40-remote-dev-client-mcp-wiring.md) — SSH wire-remote
- [35-usage-profile-and-cursor-mcp-onboarding.md](./35-usage-profile-and-cursor-mcp-onboarding.md) — Usage Profiles
