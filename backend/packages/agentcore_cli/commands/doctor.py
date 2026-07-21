"""version / doctor commands."""

from __future__ import annotations

import argparse
import os
import shutil
import sys

from agentcore_cli import __version__
from agentcore_cli.util import print_json, repo_root
from usage_profile import list_profile_ids


def cmd_version(_: argparse.Namespace) -> int:
    print(f"agentcore {__version__}")
    print(f"root {repo_root()}")
    return 0


def cmd_doctor(_: argparse.Namespace) -> int:
    root = repo_root()
    venv_dir = os.environ.get("AGENTCORE_VENV_DIR", ".venv")
    venv_python = root / venv_dir / "bin" / "python"
    agentcore_bin = root / venv_dir / "bin" / "agentcore"
    ok = True
    checks = {
        "repo_root": str(root),
        "venv_dir": venv_dir,
        "venv_python": venv_python.is_file(),
        "agentcore_on_venv_path": agentcore_bin.is_file(),
        "which_agentcore": shutil.which("agentcore"),
        "profiles": list_profile_ids(),
    }
    for name in ("fastapi", "usage_profile", "agentcore_cli", "mcp_gateway_service"):
        try:
            if name == "mcp_gateway_service":
                sys.path.insert(0, str(root / "backend" / "services" / "mcp-gateway-service" / "src"))
            __import__(name if name != "mcp_gateway_service" else "mcp_gateway_service")
            checks[f"import_{name}"] = True
        except Exception as exc:  # noqa: BLE001
            checks[f"import_{name}"] = f"FAIL: {exc}"
            ok = False
    print_json(checks)
    return 0 if ok and checks["venv_python"] else 1
