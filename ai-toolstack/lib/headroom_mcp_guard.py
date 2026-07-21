#!/usr/bin/env python3
"""ThinkingSOC Headroom MCP entry — RTK lane bypass + optional headroom_read."""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

_LIB = Path(__file__).resolve().parent
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from compression_lanes import content_has_rtk_lane_marker, rtk_lane_bypass_result  # noqa: E402


def _patch_compress_bypass() -> None:
    from headroom.ccr import mcp_server as ccr

    if getattr(ccr, "_thinkingSOC_rtk_bypass_patched", False):
        return

    original_handle = ccr.HeadroomMCPServer._handle_compress

    async def guarded_handle(self: Any, arguments: dict[str, Any]) -> list[Any]:
        content = arguments.get("content") or ""
        if content_has_rtk_lane_marker(str(content)):
            payload = rtk_lane_bypass_result(str(content))
            from mcp.types import TextContent

            return [TextContent(type="text", text=json.dumps(payload, indent=2))]
        return await original_handle(self, arguments)

    ccr.HeadroomMCPServer._handle_compress = guarded_handle  # type: ignore[method-assign]
    ccr._thinkingSOC_rtk_bypass_patched = True


def main() -> int:
    try:
        from headroom.ccr.mcp_server import create_ccr_mcp_server
    except ImportError as exc:
        print(f"headroom_mcp_guard: MCP dependencies missing: {exc}", file=sys.stderr)
        return 1

    logging.basicConfig(level=logging.WARNING)
    _patch_compress_bypass()

    proxy_url = __import__("os").environ.get("HEADROOM_PROXY_URL") or None
    server = create_ccr_mcp_server(proxy_url=proxy_url)
    asyncio.run(server.run_stdio())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
