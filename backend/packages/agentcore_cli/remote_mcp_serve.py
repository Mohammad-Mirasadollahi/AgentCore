"""MCP stdio entrypoint on the AgentCore server (invoked via SSH from dev hosts)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from agentcore_cli.remote_client import apply_compose_env_to_os
from agentcore_cli.util import repo_root


def _repo_root_for_serve() -> Path:
    env = os.environ.get("AGENTCORE_ROOT", "").strip()
    if env:
        return Path(env).resolve()
    return repo_root()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AgentCore MCP gateway on stdio (remote SSH entry)")
    parser.add_argument("tenant")
    parser.add_argument("workspace")
    parser.add_argument("project")
    parser.add_argument("--usage-profile", default="programming-cursor-mcp")
    args = parser.parse_args(argv)

    root = _repo_root_for_serve()
    os.environ["AGENTCORE_ROOT"] = str(root)
    environ = dict(os.environ)
    apply_compose_env_to_os(environ, root)
    os.environ.update(environ)

    from agentcore_cli.commands.mcp_cmd import cmd_mcp_serve

    ns = argparse.Namespace(
        tenant=args.tenant,
        workspace=args.workspace,
        project=args.project,
        usage_profile=args.usage_profile,
    )
    return cmd_mcp_serve(ns)


if __name__ == "__main__":
    raise SystemExit(main())
