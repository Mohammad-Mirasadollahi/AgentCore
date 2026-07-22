"""MCP HTTP daemon process control."""

from __future__ import annotations

import os
import secrets
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from agentcore_cli.service_runtime.paths import (
    DEFAULT_MCP_HOST,
    DEFAULT_MCP_PORT,
    mcp_log_path,
    mcp_pid_path,
    mcp_secret_path,
)
from agentcore_cli.service_runtime.progress import (
    format_process_started_at,
    progress,
    wall_clock_now,
)


def prepare_mcp_env(root: Path) -> dict[str, str]:
    from agentcore_cli.cli_defaults import load_dotenv_files

    load_dotenv_files(root=root)
    env = os.environ.copy()
    env["AGENTCORE_ROOT"] = str(root)
    try:
        from agentcore_cli.remote_client import apply_compose_env_to_os

        apply_compose_env_to_os(env, root)
    except SystemExit:
        pass

    if not env.get("AGENTCORE_MCP_TOKEN_SECRET") and not env.get("AGENTCORE_MCP_HTTP_TOKEN"):
        secret_file = mcp_secret_path(root)
        if secret_file.is_file():
            token = secret_file.read_text(encoding="utf-8").strip()
        else:
            token = secrets.token_urlsafe(32)
            secret_file.parent.mkdir(parents=True, exist_ok=True)
            secret_file.write_text(token + "\n", encoding="utf-8")
            secret_file.chmod(0o600)
        env["AGENTCORE_MCP_TOKEN_SECRET"] = token
        os.environ["AGENTCORE_MCP_TOKEN_SECRET"] = token

    host = env.get("AGENTCORE_MCP_HTTP_HOST") or DEFAULT_MCP_HOST
    port = str(env.get("AGENTCORE_MCP_HTTP_PORT") or DEFAULT_MCP_PORT)
    env["AGENTCORE_MCP_HTTP_HOST"] = host
    env["AGENTCORE_MCP_HTTP_PORT"] = port
    if not env.get("AGENTCORE_MCP_HTTP_PUBLIC_URL"):
        env["AGENTCORE_MCP_HTTP_PUBLIC_URL"] = f"http://127.0.0.1:{port}"

    pythonpath = os.pathsep.join(
        [
            str(root / "backend" / "services" / "mcp-gateway-service" / "src"),
            str(root / "backend" / "packages"),
            str(root / "backend" / "services" / "core-data-service" / "src"),
            str(root / "backend" / "services" / "memory-service" / "src"),
            str(root / "backend" / "services" / "code-graph-service" / "src"),
            str(root / "backend" / "services" / "docs-sync-service" / "src"),
            env.get("PYTHONPATH", ""),
        ]
    ).strip(os.pathsep)
    env["PYTHONPATH"] = pythonpath
    return env


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def read_mcp_pid(root: Path) -> int | None:
    path = mcp_pid_path(root)
    if not path.is_file():
        return None
    try:
        pid = int(path.read_text(encoding="utf-8").strip())
    except ValueError:
        return None
    # Resolve through package so tests can monkeypatch ``service_runtime._pid_alive``.
    from agentcore_cli import service_runtime as runtime

    if not runtime._pid_alive(pid):
        path.unlink(missing_ok=True)
        return None
    return pid


def tcp_ok(host: str, port: int, *, timeout: float = 1.0) -> bool:
    probe_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    try:
        with socket.create_connection((probe_host, port), timeout=timeout):
            return True
    except OSError:
        return False


def mcp_status(root: Path) -> dict[str, Any]:
    env_host = os.environ.get("AGENTCORE_MCP_HTTP_HOST") or DEFAULT_MCP_HOST
    env_port = int(os.environ.get("AGENTCORE_MCP_HTTP_PORT") or DEFAULT_MCP_PORT)
    pid = read_mcp_pid(root)
    reachable = tcp_ok(env_host, env_port)
    out: dict[str, Any] = {
        "running": pid is not None,
        "pid": pid,
        "host": env_host,
        "port": env_port,
        "reachable": reachable,
        "log": str(mcp_log_path(root)),
        "ok": pid is not None and reachable,
    }
    if pid is not None:
        started = format_process_started_at(pid)
        if started:
            out["started_at"] = started
    return out


def start_mcp_http(root: Path) -> dict[str, Any]:
    existing = read_mcp_pid(root)
    if existing is not None:
        status = mcp_status(root)
        where = f"{status.get('host')}:{status.get('port')}"
        progress(f"MCP HTTP: already up (pid {existing} on {where})")
        return {
            "ok": True,
            "action": "already_running",
            "pid": existing,
            "started_at": wall_clock_now(),
            **status,
        }

    env = prepare_mcp_env(root)
    host = env["AGENTCORE_MCP_HTTP_HOST"]
    port = int(env["AGENTCORE_MCP_HTTP_PORT"])
    python = root / ".venv" / "bin" / "python"
    exe = str(python if python.is_file() else sys.executable)
    log_path = mcp_log_path(root)
    started_at = wall_clock_now()
    progress(f"MCP HTTP: starting on {host}:{port}")
    log_f = open(log_path, "a", encoding="utf-8")  # noqa: SIM115 — kept open for daemon
    try:
        proc = subprocess.Popen(
            [exe, "-m", "mcp_gateway_service", "--http", "--host", host, "--port", str(port)],
            cwd=str(root),
            env=env,
            stdout=log_f,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    finally:
        log_f.close()
    mcp_pid_path(root).write_text(str(proc.pid) + "\n", encoding="utf-8")
    progress(f"MCP HTTP: process launched (pid {proc.pid}); waiting until reachable")

    for _ in range(30):
        if proc.poll() is not None:
            raise SystemExit(
                f"error: MCP HTTP exited early (code={proc.returncode}); see {log_path}"
            )
        if tcp_ok(host, port):
            break
        time.sleep(0.2)
    else:
        progress(f"MCP HTTP: not reachable yet on port {port} — see {log_path}")
    if tcp_ok(host, port):
        progress(f"MCP HTTP: is up on {host}:{port}")
    return {
        "ok": True,
        "action": "started",
        "started_at": started_at,
        "pid": proc.pid,
        "host": host,
        "port": port,
        "log": str(log_path),
    }


def stop_mcp_http(root: Path) -> dict[str, Any]:
    from agentcore_cli import service_runtime as runtime

    pid = read_mcp_pid(root)
    if pid is None:
        progress("MCP HTTP: already stopped")
        return {"ok": True, "action": "already_stopped"}
    progress(f"MCP HTTP: stopping (pid {pid})")
    try:
        os.killpg(pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            mcp_pid_path(root).unlink(missing_ok=True)
            progress("MCP HTTP: already gone")
            return {"ok": True, "action": "already_stopped"}
    for _ in range(20):
        if not runtime._pid_alive(pid):
            break
        time.sleep(0.1)
    if runtime._pid_alive(pid):
        progress(f"MCP HTTP: still running after gentle stop; forcing stop (pid {pid})")
        try:
            os.killpg(pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    mcp_pid_path(root).unlink(missing_ok=True)
    progress("MCP HTTP: is stopped")
    return {"ok": True, "action": "stopped", "pid": pid}
