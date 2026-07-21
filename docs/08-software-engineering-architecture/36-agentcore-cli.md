# AgentCore CLI

## Purpose

`agentcore` is the dedicated command for operators and developers to manage Usage Profiles, local project activation, Cursor MCP connection export, and the MCP gateway process. It is installed into the project virtualenv and linked onto the user PATH.

## Install (PATH)

Preferred (full local bootstrap including OS deps and Compose when needed):

```bash
bash install.sh
# or venv/PATH only:
bash install.sh --skip-infra
```

See [39-local-install-runbook.md](./39-local-install-runbook.md).

Venv-only helper (also used by install stage `02_venv`):

```bash
bash scripts/ensure-venv.sh
```

This will:

1. Create/refresh `.venv`
2. Install `requirements-dev.txt`
3. `pip install -e .` so `.venv/bin/agentcore` exists
4. Symlink `~/.local/bin/agentcore` → `.venv/bin/agentcore`
5. Append a PATH export to `~/.bashrc` or `~/.zshrc` when `~/.local/bin` is not already on PATH

Manual PATH install:

```bash
agentcore path install --shell-rc .bashrc
```

## Commands

| Command | Purpose |
|---------|---------|
| `agentcore doctor` | Check venv, imports, profiles, PATH |
| `agentcore profile list` | List Usage Profiles |
| `agentcore profile show <id>` | Show catalog JSON |
| `agentcore project register ...` | Create local project state under `.agentcore/projects/` |
| `agentcore project activate ...` | Activate a Usage Profile on a project |
| `agentcore project show / effective` | Inspect local state / resolved profile |
| `agentcore cursor export ...` | Write Cursor `mcpServers` fragment |
| `agentcore connect` | One-command onboarding from `~/.agentcore/connect.yaml` |
| `agentcore connect --init` | Write connect config template |
| `agentcore client wire-remote ...` | Dev host: SSH stdio MCP to remote AgentCore install |
| `agentcore client doctor-remote ...` | Check remote MCP serve entrypoint over SSH |
| `agentcore client list-mcp-clients` | Supported coding-agent MCP config targets |
| `agentcore mcp tools` | List tools for a profile |
| `agentcore mcp serve ...` | Run MCP gateway on stdio |
| `agentcore mcp serve-http` | Phase B Streamable HTTP MCP (concurrent agents) |
| `agentcore path install` | Symlink CLI onto `~/.local/bin` |
| `agentcore ports show` | Show resolved ports from the port profile (env overrides) |
| `agentcore ports check` | Port preflight: bind-check each port; exit 1 on conflict |
| `agentcore graph smoke` | Ingest + freshness + hybrid + explore (one process) |
| `agentcore graph ingest` | Ingest a source root |
| `agentcore graph freshness` | Pending-sync / freshness status |

Remote/onboarding: [40](./40-remote-dev-client-mcp-wiring.md) (SSH) · [41](./41-one-command-cross-platform-agent-onboarding.md) (one-command + HTTP).

| `agentcore graph explore` | Explore pack |
| `agentcore graph hybrid` | Hybrid search |
| `agentcore graph watch` | Batched pending-sync poll (`--debounce` / `--max-wait`; never per keystroke) |

Default graph CLI backend is in-memory (`AGENTCORE_GRAPH_CLI_BACKEND=memory`). Set
`AGENTCORE_GRAPH_CLI_BACKEND=neo4j` (plus Neo4j env) for durable Compose labs.
See [`../07-code-knowledge-graph/35-wedge-operator-connect-runbook.md`](../07-code-knowledge-graph/35-wedge-operator-connect-runbook.md).

## Port preflight

Uses `backend/packages/port_profile` and the default profile at `backend/configs/port-profiles/agentcore-dev.json`.

```bash
agentcore ports show
agentcore ports check
agentcore ports check --profile /path/to/custom-port-profile.json
```

`ports check` prints JSON with per-key `{port, available}` and overall `ok`. Exit code is `0` when all ports are free, `1` when any bind fails. Environment variables named like the profile keys (e.g. `AGENTCORE_API_PORT`) override profile defaults before the check.

Related: [40-remote-dev-client-mcp-wiring.md](./40-remote-dev-client-mcp-wiring.md) for dev hosts connecting to a remote AgentCore server.

Example — programming + Cursor MCP (same host):

```bash
agentcore project register \
  --tenant acme --workspace eng --project payments \
  --name "Payments" --usage-profile programming-cursor-mcp

agentcore cursor export \
  --tenant acme --workspace eng --project payments \
  --out ~/.cursor/agentcore-mcp.json
```

Merge the exported `mcpServers` into Cursor MCP settings, then reload MCP.

## Implementation home

- Package: `backend/packages/agentcore_cli/`
- Entry point: `pyproject.toml` → `agentcore = agentcore_cli.main:main`
- Layout: `main.py` (dispatch) · `parser.py` · `util.py` · `state.py` · `commands/` (`doctor`, `profile`, `project`, `cursor`, `client`, `mcp_cmd`, `path_cmd`, `ports`, `graph`) · `remote_client.py` · `remote_mcp_serve.py`
- Local state: `.agentcore/projects/<tenant>/<workspace>/<project>.json`
- Tests: `tests/backend/tools/agentcore-cli/`
