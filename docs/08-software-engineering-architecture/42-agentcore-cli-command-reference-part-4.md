---
doc_id: ac.doc.sea.agentcore-cli-command-reference-part-4
title: 42 - AgentCore CLI Command Reference (Continued) (Continued) (Continued) (Part 4)
doc_type: standard
status: active
schema_version: '1.0'
owner: platform-docs
summary: Remaining `agentcore` command catalog entries split from `docs/08-software-engineering-architecture/42-agentcore-cli-command-reference-continued-continued-continued.md`
  to satisfy the soft body-size budget.
tags:
- standard
- sea
phase: 08-software-engineering-architecture
canonical_path: docs/08-software-engineering-architecture/42-agentcore-cli-command-reference-part-4.md
lifecycle_lane: current
concern_lane: standard
audience_lane:
- platform-engineering
- agents
authority: normative
visibility: internal
linked_symbols:
- backend/packages/agentcore_cli/main.py::main
- backend/packages/agentcore_cli/commands/mcp_tokens.py::cmd_mcp_tokens
- backend/packages/agentcore_cli/mcp_token_report.py::build_report
- backend/packages/agentcore_cli/mcp_usage_log.py::append_mcp_usage_event
- backend/services/mcp-gateway-service/src/mcp_gateway_service/server.py::handle_message
- backend/packages/agentcore_cli/sync_config.py::SyncConfigError
- backend/packages/agentcore_cli/software_paths.py::format_paths_env
- backend/packages/agentcore_cli/docs_link_sync.py::DocsLinkSyncResult
- backend/services/code-graph-service/src/code_graph_service/domain/repo_discovery.py::DiscoveredFile
- backend/services/code-graph-service/src/code_graph_service/domain/doc_discovery.py::DiscoveredDocFile
- backend/services/code-graph-service/src/code_graph_service/application/ingest/human_docs.py::human_doc_symbol_id
- backend/packages/agentcore_cli/cli_defaults.py::load_dotenv_files
- backend/packages/agentcore_cli/identity.py::identity_path
- tests/backend/services/code-graph-service/test_human_docs_ingest.py::login
- tests/backend/tools/agentcore-cli/test_mcp_tokens.py::test_estimate_connect_lazy_cheaper_than_full
doc_version: 1.0.0
updated_at: '2026-07-24'
---

# 42 - AgentCore CLI Command Reference (Continued) (Continued) (Continued) (Part 4)

## Purpose

Remaining `agentcore` command catalog entries split from `docs/08-software-engineering-architecture/42-agentcore-cli-command-reference-continued-continued-continued.md` to satisfy the soft body-size budget.

## Command catalog (continued)

### `agentcore mcp tools`

| | |
| --- | --- |
| **Why** | List MCP tool names for a Usage Profile (verify catalog wiring) |
| **Required** | None |
| **Optional** | `--usage-profile` (default `programming-cursor-mcp`) |
| **Example** | `agentcore mcp tools` |
| **What changes** | Nothing (read-only) |

### `agentcore mcp tokens`

| | |
| --- | --- |
| **Why** | Estimate how many tokens AgentCore MCP injects on connect (`tools/list` lazy facade vs full catalog), list heavy tool payload estimates, and summarize logged MCP usage by **client id** and **scope id** over a time range |
| **Required** | None |
| **Optional** | `--usage-profile` · `--since` / `-s` (`24h`, `7d`, `30d`, ISO; default `7d`) · `--until` / `-u` · `--clients` (`all` or `cursor,vscode,…`) · `--id` (`all` or `tenant/workspace/project[,…]`) · `--project-dir` · `--include-user-clients` · `--format text\|json` |
| **Example** | `agentcore mcp tokens --since 24h` · `agentcore mcp tokens --clients cursor,vscode --id mir/dev/agentcore` · `agentcore mcp tokens -f json` |
| **What changes** | Nothing (read-only). Gateway appends `.agentcore/mcp-usage/events.jsonl` on `initialize` / `tools/list` / `tools/call` when an IDE is connected (`AGENTCORE_MCP_CLIENT_ID` stamped at wire/connect time) |
| **Token unit** | Approx UTF-8 bytes/4 (same heuristic as sync usage) |
| **Normative design** | [44-mcp-token-accounting.md](./44-mcp-token-accounting.md) |

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
| **Optional** | `start --json` · `stop --json` · `restart --json` · `status --json` · `detail --json` |
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

### `agentcore graph generation-context`

| | |
| --- | --- |
| **Why** | Print the generation context pack for a seed symbol, including `hybrid_documentation` (human → living → rationale → AST) |
| **Required** | Scope flags, and either `--symbol-id` or `--qualified-name` |
| **Optional** | `--max-symbols` (default 12) |
| **Example** | `agentcore graph generation-context --tenant acme --workspace eng --project payments --qualified-name src.auth.login` |
| **What changes** | Nothing durable (read-only). Does not invent graph edges |

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
| **What changes** | May flush pending sync **banners** into freshness state while running; does not replace explicit ingest. Any future flush-to-ingest path must honor Client Skip/Ingest preference — see [`../07-code-knowledge-graph/51-client-standards-gate-and-watcher-policy.md`](../07-code-knowledge-graph/51-client-standards-gate-and-watcher-policy.md) |

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
## edit code.exclude / docs.match / docs.exclude
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

- Previous chunk: `docs/08-software-engineering-architecture/42-agentcore-cli-command-reference-continued-continued-continued.md`
- Upgrade CLI catalog (normative): [51-software-upgrade-server-and-client.md](./51-software-upgrade-server-and-client.md#cli-catalog-agentcore-upgrade)
- Overview: [36-agentcore-cli.md](./36-agentcore-cli.md)
