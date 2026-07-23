---
doc_id: ac.doc.sea.agentcore-cli-command-reference-continued-continued-continued
title: 42 - AgentCore CLI Command Reference (Continued) (Continued) (Continued)
doc_type: standard
status: active
schema_version: '1.0'
owner: platform-docs
summary: Continuation of `docs/08-software-engineering-architecture/42-agentcore-cli-command-reference-continued-continued.md`
  — remaining sections after the soft size budget.
tags:
- standard
- sea
phase: 08-software-engineering-architecture
canonical_path: docs/08-software-engineering-architecture/42-agentcore-cli-command-reference-continued-continued-continued.md
lifecycle_lane: current
concern_lane: standard
audience_lane:
- platform-engineering
- agents
authority: normative
visibility: internal
linked_symbols:
- backend/packages/agentcore_cli/main.py::main
- backend/packages/agentcore_cli/sync_config.py::SyncConfigError
- backend/packages/agentcore_cli/software_paths.py::format_paths_env
- backend/packages/agentcore_cli/docs_link_sync.py::DocsLinkSyncResult
- backend/services/code-graph-service/src/code_graph_service/domain/repo_discovery.py::DiscoveredFile
- backend/services/code-graph-service/src/code_graph_service/domain/doc_discovery.py::DiscoveredDocFile
- backend/services/code-graph-service/src/code_graph_service/application/ingest/human_docs.py::human_doc_symbol_id
- backend/packages/agentcore_cli/cli_defaults.py::load_dotenv_files
- backend/packages/agentcore_cli/identity.py::identity_path
- tests/backend/services/code-graph-service/test_human_docs_ingest.py::login
- scripts/remediate_docs_standards.py::main
- scripts/split_soft_budget_docs.py::main
- tests/backend/tools/agentcore-cli/test_docs_standards.py::test_parser_docs_standards_word_modes
x: 1
---

# 42 - AgentCore CLI Command Reference (Continued) (Continued) (Continued)

## Purpose

Continuation of `docs/08-software-engineering-architecture/42-agentcore-cli-command-reference-continued-continued.md` — remaining sections after the soft size budget.

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
| **How to fix findings** | Follow normative procedure `docs/00-master-plan/10-documentation-standardization-procedure.md` (issue-code table, remediator, soft-budget split, evidence `linked_symbols`). Helpers: `scripts/remediate_docs_standards.py`, `scripts/split_soft_budget_docs.py`, library `agentcore_cli.commands.docs_standards.remediate` |
| **Done means** | `nonconforming_count = 0` and soft-budget warnings cleared for the remediation scope; tree lock in `tests/backend/tools/agentcore-cli/test_docs_standards.py` |
| **Normative refs** | `docs/00-master-plan/06-professional-documentation-standard.md`, `08-documentation-structure-and-machine-ingest-standard.md`, `09-documentation-classification-and-lanes.md`, **`10-documentation-standardization-procedure.md`** |

### `agentcore docs-suggest-links`

**Hybrid write path:** evidence-only suggestions for `linked_symbols`. Never invents `DOCUMENTED_BY` edges.

| | |
| --- | --- |
| **Why** | Propose `path::Symbol` tokens from Markdown path citations so human docs can link to code after review + `agentcore sync` Phase 2 |
| **Required** | None (repo root via `AGENTCORE_ROOT` / package). For `--path`, the file must exist |
| **Flags** | `--path FILE` (single file; always reported). `--docs-root DIR` (default `docs` when scanning). `--include-all` (report files with zero new suggestions). `--apply` (merge into YAML frontmatter). `--json` |
| **Example** | `agentcore docs-suggest-links` · `agentcore docs-suggest-links --path docs/foo.md` · `agentcore docs-suggest-links --docs-root backend/docs --include-all` · `agentcore docs-suggest-links --apply` · `agentcore docs-suggest-links --json` |
| **What you see** | Files with suggested new tokens; with `--include-all`, also already-linked / empty evidence. Apply reports `applied` vs `skipped_no_frontmatter` |
| **What changes** | Dry-run: nothing. `--apply`: frontmatter `linked_symbols` only when YAML frontmatter exists. Graph edges only after later `agentcore sync` resolve |
| **Exit code** | `0` when zero new suggestions; `1` when any suggested token remains (CI-friendly dry-run) |
| **Normative refs** | `docs/07-code-knowledge-graph/41-hybrid-documentation-coverage.md`, `docs/07-code-knowledge-graph/03-ingestion-and-living-documentation-workflow.md` |

### `agentcore docs-catalog`

**Retrieval helper:** cached frontmatter index (tags + closed lane enums). Does not invent `DOCUMENTED_BY`.

| | |
| --- | --- |
| **Why** | Let operators/agents narrow which Markdown to open using tags/lanes without loading full bodies |
| **Required** | None |
| **Flags** | `--refresh`, `--roots`, `--tag`, `--concern`, `--lifecycle`, `--audience`, `--phase`, `--doc-type`, `--query`, `--linked-only`, `--unlinked-only`, `--limit`, `--json` |
| **Example** | `agentcore docs-catalog --refresh` · `agentcore docs-catalog --roots handbook --tag api` · `agentcore docs-catalog --query hybrid --json` |
| **Cache** | `.agentcore/cache/docs-catalog.json` (override `AGENTCORE_DOCS_CATALOG_CACHE`; roots via `AGENTCORE_DOCS_CATALOG_ROOTS` or `--roots`) |
| **Vocabulary** | Observed from scanned frontmatter only — not a global hardcoded tag/lane list |
| **What changes** | `--refresh` rewrites the cache file only. **`agentcore sync` builds the catalog at the start** (best-effort; sync still continues if catalog build fails) |
| **Normative refs** | `docs/07-code-knowledge-graph/42-documentation-catalog-and-lane-cache.md` |

### `agentcore quality-audit`

**Operator UX law:** same word-mode pattern as `inventory` / `docs-standards` — no dashed mode flags; use `detail` and `save [<path>]`.

| | |
| --- | --- |
| **Why** | One command that **discovers and categorizes** docs + code quality problems: standards gate failures, soft/hard size budgets, missing `linked_symbols` when code paths are cited, design Mermaid without flow tables, invalid lanes, never-ingested code, stale edited code, low living-doc coverage |
| **Required** | None for docs half. Code half needs pinned software paths + sync filters (same as `inventory`); if unavailable, docs findings still print and code section is marked skipped |
| **Modes** | **Normal**: category counts + top findings. **Detail**: all findings with evidence. **Save**: write full text report (and JSON twin) to a path; bare `save` uses `.agentcore/quality-audit/YYYY-MM-DD_HH-MM-SS.txt` |
| **Example** | `agentcore quality-audit` · `agentcore quality-audit detail` · `agentcore quality-audit save` · `agentcore quality-audit detail save /tmp/qa.txt` |
| **Categories** | `docs.standards`, `docs.size_soft`, `docs.size_hard`, `docs.linking_gap`, `docs.flow_table_gap`, `docs.lane_invalid`, `code.never_ingested`, `code.stale_edited`, `code.low_symbol_docs` |
| **Exit code** | `0` when zero findings; `1` when any finding exists (CI-friendly) |
| **What changes** | Nothing on the graph. `save` only writes report files under the path you named (or `.agentcore/quality-audit/`) |
| **Normative refs** | `docs/00-master-plan/10-documentation-standardization-procedure.md` |

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

## Related Documents

- Continued command catalog: `docs/08-software-engineering-architecture/42-agentcore-cli-command-reference-part-4.md`
