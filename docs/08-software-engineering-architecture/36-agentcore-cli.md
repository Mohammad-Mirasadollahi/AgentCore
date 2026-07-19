# AgentCore CLI

## Purpose

`agentcore` is the dedicated command for operators and developers to manage Usage Profiles, local project activation, Cursor MCP connection export, and the MCP gateway process. It is installed into the project virtualenv and linked onto the user PATH.

## Install (PATH)

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
| `agentcore mcp tools` | List tools for a profile |
| `agentcore mcp serve ...` | Run MCP gateway on stdio |
| `agentcore path install` | Symlink CLI onto `~/.local/bin` |
| `agentcore ports show` | Show resolved ports from the port profile (env overrides) |
| `agentcore ports check` | Port preflight: bind-check each port; exit 1 on conflict |

## Port preflight

Uses `backend/packages/port_profile` and the default profile at `backend/configs/port-profiles/agentcore-dev.json`.

```bash
agentcore ports show
agentcore ports check
agentcore ports check --profile /path/to/custom-port-profile.json
```

`ports check` prints JSON with per-key `{port, available}` and overall `ok`. Exit code is `0` when all ports are free, `1` when any bind fails. Environment variables named like the profile keys (e.g. `AGENTCORE_API_PORT`) override profile defaults before the check.

## Example — programming + Cursor MCP

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
- Local state: `.agentcore/projects/<tenant>/<workspace>/<project>.json`
- Tests: `tests/backend/tools/agentcore-cli/`
