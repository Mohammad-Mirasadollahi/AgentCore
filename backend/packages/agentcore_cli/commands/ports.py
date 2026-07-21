"""Port profile preflight commands."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from agentcore_cli.util import print_json
from port_profile import PortProfileError, check_port_available, load_profile, resolve_ports
from port_profile.loader import DEFAULT_PROFILE_PATH


def _ports_profile_path(args: argparse.Namespace) -> Path | None:
    raw = str(getattr(args, "profile", "") or "").strip()
    return Path(raw) if raw else None


def cmd_ports_show(args: argparse.Namespace) -> int:
    path = _ports_profile_path(args)
    try:
        profile = load_profile(path)
        resolved = resolve_ports(profile)
    except PortProfileError as exc:
        raise SystemExit(f"error: {exc}") from exc
    print_json({"profile": str(path or DEFAULT_PROFILE_PATH), "ports": resolved})
    return 0


def cmd_ports_check(args: argparse.Namespace) -> int:
    path = _ports_profile_path(args)
    try:
        profile = load_profile(path)
        resolved = resolve_ports(profile)
    except PortProfileError as exc:
        raise SystemExit(f"error: {exc}") from exc
    ports: dict[str, dict[str, Any]] = {}
    ok = True
    for key, port in resolved.items():
        available = check_port_available(port)
        ports[key] = {"port": port, "available": available}
        if not available:
            ok = False
    print_json({"ok": ok, "ports": ports, "profile": str(path or DEFAULT_PROFILE_PATH)})
    return 0 if ok else 1
