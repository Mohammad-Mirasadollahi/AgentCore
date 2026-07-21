"""Shared CLI helpers."""

from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def repo_root() -> Path:
    env = os.environ.get("AGENTCORE_ROOT", "").strip()
    if env:
        return Path(env).resolve()
    # backend/packages/agentcore_cli/util.py → parents[3] = repo root
    return Path(__file__).resolve().parents[3]


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


def require_scope(args: argparse.Namespace) -> tuple[str, str, str]:
    tenant = str(args.tenant or "").strip()
    workspace = str(args.workspace or "").strip()
    project = str(args.project or "").strip()
    if not all((tenant, workspace, project)):
        raise SystemExit("error: --tenant, --workspace, and --project are required")
    return tenant, workspace, project


def add_scope_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--project", required=True)
