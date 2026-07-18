from __future__ import annotations

import json
import os
from pathlib import Path
import socket
from typing import Any


FORBIDDEN_COMMON_PORTS = frozenset(
    {80, 443, 3000, 3001, 5432, 6379, 7474, 7687, 8000, 8080, 8501, 9000, 9200}
)

DEFAULT_PROFILE_PATH = (
    Path(__file__).resolve().parents[2] / "configs" / "port-profiles" / "agentcore-dev.json"
)


class PortProfileError(ValueError):
    pass


def load_profile(path: Path | None = None) -> dict[str, Any]:
    profile_path = path or DEFAULT_PROFILE_PATH
    if not profile_path.is_file():
        raise PortProfileError(f"port profile missing: {profile_path}")
    data = json.loads(profile_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise PortProfileError("port profile must be a JSON object")
    return data


def validate_profile(profile: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    ports = profile.get("ports")
    if not isinstance(ports, dict) or not ports:
        return ["ports map is required"]
    forbidden = set(profile.get("forbidden_defaults") or []) | set(FORBIDDEN_COMMON_PORTS)
    seen: dict[int, str] = {}
    for key, value in ports.items():
        if not str(key).startswith("AGENTCORE_") or not str(key).endswith("_PORT"):
            errors.append(f"invalid port key naming: {key}")
            continue
        if not isinstance(value, int) or not (1024 < value < 65535):
            errors.append(f"port out of range for {key}: {value}")
            continue
        if value in forbidden:
            errors.append(f"port {value} for {key} is a forbidden common default")
        if value in seen:
            errors.append(f"duplicate port {value} for {key} and {seen[value]}")
        else:
            seen[value] = str(key)
    owners = profile.get("service_owners") or {}
    if not isinstance(owners, dict) or not owners:
        errors.append("service_owners map is required")
    else:
        for service, port_key in owners.items():
            if port_key not in ports:
                errors.append(f"service_owners[{service}] references unknown key {port_key}")
    return errors


def resolve_ports(profile: dict[str, Any], environ: dict[str, str] | None = None) -> dict[str, int]:
    env = environ if environ is not None else os.environ
    ports = profile.get("ports") or {}
    resolved: dict[str, int] = {}
    for key, default in ports.items():
        raw = env.get(str(key), "").strip()
        if raw:
            try:
                resolved[str(key)] = int(raw)
            except ValueError as exc:
                raise PortProfileError(f"{key} must be an integer, got {raw!r}") from exc
        else:
            resolved[str(key)] = int(default)
    errors = validate_profile({"ports": resolved, "service_owners": profile.get("service_owners"), "forbidden_defaults": profile.get("forbidden_defaults")})
    if errors:
        raise PortProfileError("; ".join(errors))
    return resolved


def check_port_available(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True
