"""Local-dev process control: Compose core infra + MCP HTTP daemon + systemd boot.

Public API is re-exported here so callers keep using ``agentcore_cli.service_runtime``.
"""

from __future__ import annotations

from agentcore_cli.service_runtime.boot import (
    agentcore_bin,
    boot_disable,
    boot_enable,
    boot_status,
    systemctl as _systemctl,
    unit_body,
    unit_path,
)
from agentcore_cli.service_runtime.compose import (
    compose_base_cmd,
    compose_logs_tail,
    compose_status,
    container_started_at,
    run_cmd as _run,
    start_compose,
    stop_compose,
)
from agentcore_cli.service_runtime.lifecycle import (
    ensure_running_or_offer_start,
    restart_all,
    service_state,
    start_all,
    status_all,
    stop_all,
)
from agentcore_cli.service_runtime.logs import collect_detail, dump_json, read_log_tail
from agentcore_cli.service_runtime.mcp import (
    mcp_status,
    pid_alive as _pid_alive,
    prepare_mcp_env,
    read_mcp_pid,
    start_mcp_http,
    stop_mcp_http,
    tcp_ok as _tcp_ok,
)
from agentcore_cli.service_runtime.paths import (
    COMPOSE_SERVICES,
    DEFAULT_MCP_HOST,
    DEFAULT_MCP_PORT,
    UNIT_NAME,
    compose_dir,
    compose_env_file,
    compose_file,
    mcp_log_path,
    mcp_pid_path,
    mcp_secret_path,
    run_dir,
)
from agentcore_cli.service_runtime.progress import (
    format_docker_started_at as _format_docker_started_at,
    format_process_started_at,
    progress as _progress,
    stack_restarted_at,
    uptime_seconds_since,
    wall_clock_now,
)

__all__ = [
    "COMPOSE_SERVICES",
    "DEFAULT_MCP_HOST",
    "DEFAULT_MCP_PORT",
    "UNIT_NAME",
    "_format_docker_started_at",
    "_pid_alive",
    "_progress",
    "_run",
    "_systemctl",
    "_tcp_ok",
    "agentcore_bin",
    "boot_disable",
    "boot_enable",
    "boot_status",
    "collect_detail",
    "compose_base_cmd",
    "compose_dir",
    "compose_env_file",
    "compose_file",
    "compose_logs_tail",
    "compose_status",
    "container_started_at",
    "dump_json",
    "ensure_running_or_offer_start",
    "format_process_started_at",
    "mcp_log_path",
    "mcp_pid_path",
    "mcp_secret_path",
    "mcp_status",
    "prepare_mcp_env",
    "read_log_tail",
    "read_mcp_pid",
    "restart_all",
    "run_dir",
    "service_state",
    "stack_restarted_at",
    "start_all",
    "start_compose",
    "start_mcp_http",
    "status_all",
    "stop_all",
    "stop_compose",
    "stop_mcp_http",
    "unit_body",
    "unit_path",
    "uptime_seconds_since",
    "wall_clock_now",
]
