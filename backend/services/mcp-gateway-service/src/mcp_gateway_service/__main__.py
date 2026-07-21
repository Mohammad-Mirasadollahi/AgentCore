"""MCP gateway entrypoints: stdio (default) or HTTP."""

from __future__ import annotations

import argparse
import os
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m mcp_gateway_service")
    parser.add_argument(
        "--http",
        action="store_true",
        help="Serve Streamable HTTP / JSON-RPC MCP (Phase B)",
    )
    parser.add_argument("--host", default=os.environ.get("AGENTCORE_MCP_HTTP_HOST", "0.0.0.0"))
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("AGENTCORE_MCP_HTTP_PORT", "32500")),
    )
    args, _unknown = parser.parse_known_args(argv)
    if args.http:
        from .http_app import run_http_server

        run_http_server(host=str(args.host), port=int(args.port))
        return 0
    from .server import main as stdio_main

    return stdio_main()


if __name__ == "__main__":
    raise SystemExit(main())
