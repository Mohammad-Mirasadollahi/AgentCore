"""Paths and constants for local AgentCore process control."""

from __future__ import annotations

from pathlib import Path

UNIT_NAME = "agentcore.service"
COMPOSE_SERVICES = ("postgres", "neo4j")
DEFAULT_MCP_HOST = "0.0.0.0"
DEFAULT_MCP_PORT = 32500
# Host MCP builds postgres/neo4j stores before uvicorn binds; cold start is ~4–8s
# and can exceed the old 6s poll budget under load after compose restart.
MCP_HTTP_READY_TIMEOUT_SEC = 60.0


def run_dir(root: Path) -> Path:
    path = root / ".agentcore" / "run"
    path.mkdir(parents=True, exist_ok=True)
    return path


def mcp_pid_path(root: Path) -> Path:
    return run_dir(root) / "mcp-http.pid"


def mcp_log_path(root: Path) -> Path:
    return run_dir(root) / "mcp-http.log"


def mcp_secret_path(root: Path) -> Path:
    return root / ".agentcore" / "mcp-http.secret"


def compose_dir(root: Path) -> Path:
    return root / "backend" / "deployments" / "compose"


def compose_file(root: Path) -> Path:
    return compose_dir(root) / "compose.yaml"


def compose_env_file(root: Path) -> Path:
    return compose_dir(root) / ".env.local"


def local_compose_stack_present(root: Path) -> bool:
    """True when this checkout can run local Compose (server install)."""
    return compose_file(root).is_file() and compose_env_file(root).is_file()


def missing_local_stack_message(root: Path) -> str:
    env = compose_env_file(root)
    return (
        f"error: no local AgentCore server stack (missing {env}).\n"
        "Client installs skip Compose (Postgres/Neo4j) on purpose.\n"
        "  • Run `agentcore sync` on the AgentCore server, or\n"
        "  • Configure `.agentcore/connect.yaml` (`agentcore connect`) "
        "so this CLI can sync over SSH, or\n"
        "  • Re-install this host as server: bash install.sh --role server"
    )
