# AgentCore install modules

Entrypoint: repository root [`../../install.sh`](../../install.sh) → [`load.sh`](load.sh).

| Module | Responsibility |
|--------|----------------|
| [`common.sh`](common.sh) | Logging, root paths, state file, secret helpers, root/sudo runner |
| [`01_prerequisites.sh`](01_prerequisites.sh) | Check/install Python 3.12+, Docker, Compose, curl, git (+ optional Node) |
| [`02_venv.sh`](02_venv.sh) | Create `.venv`, install deps, editable `agentcore` CLI (via `scripts/ensure-venv.sh`) |
| [`03_compose_env.sh`](03_compose_env.sh) | Create `backend/deployments/compose/.env.local` with generated secrets |
| [`04_docker_infra.sh`](04_docker_infra.sh) | `docker compose --profile core up` for Postgres + Neo4j, wait healthy |
| [`05_verify.sh`](05_verify.sh) | `agentcore doctor` + infra re-check; optional ai-toolstack |
| [`load.sh`](load.sh) | Source order + stage orchestration |

Add new install steps in the smallest matching module. Keep root `install.sh` as flags + exit codes only.

| Related | Path |
|---------|------|
| Operator guide | [`docs/08-software-engineering-architecture/39-local-install-runbook.md`](../../docs/08-software-engineering-architecture/39-local-install-runbook.md) |
| E2E smoke | [`tests/e2e/install/run-install-smoke.sh`](../../tests/e2e/install/run-install-smoke.sh) |
| Pytest smoke | [`tests/backend/tools/install/test_install_smoke.py`](../../tests/backend/tools/install/test_install_smoke.py) |
