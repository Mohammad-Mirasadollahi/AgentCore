"""Paths and constants for local AgentCore process control."""

from __future__ import annotations

from pathlib import Path

UNIT_NAME = "agentcore.service"
COMPOSE_SERVICES = ("postgres", "neo4j")
DEFAULT_MCP_HOST = "0.0.0.0"
DEFAULT_MCP_PORT = 32500


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
