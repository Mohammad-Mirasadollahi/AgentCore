# AgentCore install modules

Entrypoint options:

- **Empty machine:** [`../get-agentcore.sh`](../get-agentcore.sh) (curl|bash) — choose `release` or `main`, then runs root `install.sh`
- **Already cloned:** repository root [`../../install.sh`](../../install.sh) → [`load.sh`](load.sh)

| Module | Responsibility |
|--------|----------------|
| [`../get-agentcore.sh`](../get-agentcore.sh) | Fetch from GitHub (`release` = latest Release tag tarball; `main` = branch tip); preserve `.agentcore/`, `.env`, compose `.env.local`, `.venv` |
| [`common.sh`](common.sh) | Logging, root paths, state file, secret helpers, root/sudo runner |
| [`01_prerequisites.sh`](01_prerequisites.sh) | Check/install Python 3.12+, curl, git; Docker/Compose only when **server** (not client / `--skip-infra`) |
| [`02_venv.sh`](02_venv.sh) | Create `.venv`, install deps, editable `agentcore` CLI; seed `.env` + `agentcore.sync.yaml` from examples |
| [`03_compose_env.sh`](03_compose_env.sh) | Seed repo templates; create `backend/deployments/compose/.env.local` with generated secrets |
| [`04_docker_infra.sh`](04_docker_infra.sh) | `docker compose --profile core up` for Postgres + Neo4j, wait healthy |
| [`05_verify.sh`](05_verify.sh) | `agentcore doctor` + infra re-check; optional ai-toolstack |
| [`06_runtime_bringup.sh`](06_runtime_bringup.sh) | Prompted/flagged runtime: host MCP or Docker `mcp-gateway`; always re-ensure PATH |
| [`load.sh`](load.sh) | Source order + stage orchestration (`all`, `upgrade`, `stage`, …) |

Add new install steps in the smallest matching module. Keep root `install.sh` as flags + exit codes only.

**Upgrade:** `bash install.sh --upgrade` backs up `.agentcore/install-state.env`, re-runs stages, then `agentcore upgrade finalize`. Control-plane / client paths: `agentcore upgrade …` (see docs/08…/51-software-upgrade-server-and-client.md). To refresh code from GitHub first, re-run `get-agentcore.sh` with the same channel.

| Related | Path |
|---------|------|
| Operator guide | [`docs/08-software-engineering-architecture/39-local-install-runbook.md`](../../docs/08-software-engineering-architecture/39-local-install-runbook.md) |
| Upgrade guide | [`docs/08-software-engineering-architecture/51-software-upgrade-server-and-client.md`](../../docs/08-software-engineering-architecture/51-software-upgrade-server-and-client.md) |
| E2E smoke | [`tests/e2e/install/run-install-smoke.sh`](../../tests/e2e/install/run-install-smoke.sh) |
| Pytest smoke | [`tests/backend/tools/install/test_install_smoke.py`](../../tests/backend/tools/install/test_install_smoke.py) |
| Get/bootstrap tests | [`tests/backend/tools/install/test_get_agentcore.py`](../../tests/backend/tools/install/test_get_agentcore.py) |
