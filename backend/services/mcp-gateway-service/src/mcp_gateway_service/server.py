from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

_PACKAGES = Path(__file__).resolve().parents[4] / "packages"
if str(_PACKAGES) not in sys.path:
    sys.path.insert(0, str(_PACKAGES))

from usage_profile import resolve_effective_profile  # noqa: E402

from .backends import PlatformBackends, dispatch_capability  # noqa: E402
from .lazy_facade import (  # noqa: E402
    LAZY_EXECUTE_TOOL,
    LAZY_SEARCH_TOOL,
    is_lazy_facade_tool,
    lazy_tools_list,
    normalize_execute_args,
    search_catalog,
    server_name_aliases,
)


PROTOCOL_VERSION = "2024-11-05"


class McpGatewayError(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class McpGateway:
    """MCP JSON-RPC surface driven by a Usage Profile and in-process AgentCore services."""

    def __init__(
        self,
        *,
        profile_id: str,
        tenant_id: str,
        workspace_id: str,
        project_id: str,
        backends: PlatformBackends | None = None,
    ) -> None:
        if not all(
            (
                str(profile_id).strip(),
                str(tenant_id).strip(),
                str(workspace_id).strip(),
                str(project_id).strip(),
            )
        ):
            raise McpGatewayError(-32602, "usage profile and scope env vars are required")
        self.effective = resolve_effective_profile(
            profile_id,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            project_id=project_id,
        )
        self._tools = {str(t["name"]): t for t in self.effective["mcp"]["tools"]}
        self.backends = backends or PlatformBackends.from_env()

    @property
    def server_name(self) -> str:
        return str(self.effective["mcp"]["server_name"])

    def tools_list(self) -> list[dict[str, Any]]:
        """Client-facing list: mcp-lazy facade only (full catalog via search)."""
        return lazy_tools_list(server_name=self.server_name)

    def catalog_tools(self) -> list[dict[str, Any]]:
        """Full Usage Profile tool catalog (not dumped into Cursor context)."""
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "inputSchema": tool["input_schema"],
            }
            for tool in self.effective["mcp"]["tools"]
        ]

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        arguments = arguments or {}
        if name == LAZY_SEARCH_TOOL:
            limit = arguments.get("limit", 5)
            try:
                limit_i = int(limit)
            except (TypeError, ValueError):
                limit_i = 5
            result = search_catalog(
                list(self.effective["mcp"]["tools"]),
                server_name=self.server_name,
                query=str(arguments.get("query") or ""),
                limit=limit_i,
            )
            return {
                "content": [{"type": "text", "text": json.dumps(result, sort_keys=True)}],
                "structuredContent": result,
                "isError": False,
            }
        if name == LAZY_EXECUTE_TOOL:
            tool_name, server_name, nested = normalize_execute_args(arguments)
            if not tool_name or not server_name:
                raise McpGatewayError(
                    -32602,
                    "mcp_execute_tool requires server_name and tool_name "
                    "(aliases: server, tool). Use mcp_search_tools first.",
                )
            if server_name not in server_name_aliases(self.server_name):
                raise McpGatewayError(
                    -32601,
                    f'Tool "{tool_name}" not found in server "{server_name}". '
                    "Use mcp_search_tools first.",
                )
            if is_lazy_facade_tool(tool_name):
                raise McpGatewayError(-32602, f"cannot execute facade tool via itself: {tool_name}")
            return self.call_tool(tool_name, nested)
        tool = self._tools.get(name)
        if tool is None:
            raise McpGatewayError(-32601, f"tool not allowed by usage profile: {name}")
        maps_to = str(tool["maps_to"])
        result = self._dispatch(maps_to, arguments)
        return {
            "content": [{"type": "text", "text": json.dumps(result, sort_keys=True)}],
            "structuredContent": result,
            "isError": False,
        }

    def _dispatch(self, maps_to: str, arguments: dict[str, Any]) -> dict[str, Any]:
        scope = self.effective["scope"]
        correlation_id = str(uuid4())
        if maps_to == "platform.ping":
            return {
                "maps_to": maps_to,
                "usage_profile": self.effective["profile_id"],
                "scope": scope,
                "correlation_id": correlation_id,
                "ok": True,
                "server_name": self.effective["mcp"]["server_name"],
                "tool_count": len(self._tools),
                "backend": "in_process",
                "store_mode": self.backends.store_mode,
                "mcp_protocol": PROTOCOL_VERSION,
            }
        if maps_to == "profile.effective":
            return {
                "maps_to": maps_to,
                "usage_profile": self.effective["profile_id"],
                "scope": scope,
                "correlation_id": correlation_id,
                "effective": self.effective,
                "backend": "in_process",
                "store_mode": self.backends.store_mode,
            }
        try:
            return dispatch_capability(
                self.backends,
                maps_to,
                arguments,
                scope=scope,
                usage_profile=self.effective["profile_id"],
                correlation_id=correlation_id,
            )
        except ValueError as exc:
            raise McpGatewayError(-32602, str(exc)) from exc
        except Exception as exc:  # pragma: no cover - service validation surface
            raise McpGatewayError(-32000, f"backend error: {exc}") from exc


def handle_message(gateway: McpGateway, message: dict[str, Any]) -> dict[str, Any] | None:
    """Handle one JSON-RPC MCP message. Notifications return None."""
    if "method" not in message and "id" not in message:
        raise McpGatewayError(-32600, "invalid request")
    method = message.get("method")
    req_id = message.get("id")
    params = message.get("params") or {}

    if method is None:
        raise McpGatewayError(-32600, "method required")

    if req_id is None and method.startswith("notifications/"):
        return None

    try:
        if method == "initialize":
            result = {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": gateway.effective["mcp"]["server_name"],
                    "version": gateway.effective["version"],
                },
            }
        elif method == "tools/list":
            result = {"tools": gateway.tools_list()}
        elif method == "tools/call":
            name = str(params.get("name") or "")
            arguments = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
            result = gateway.call_tool(name, arguments)
        elif method == "ping":
            result = {}
        else:
            raise McpGatewayError(-32601, f"method not found: {method}")
        return {"jsonrpc": "2.0", "id": req_id, "result": result}
    except McpGatewayError as exc:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": exc.code, "message": exc.message},
        }


def gateway_from_env() -> McpGateway:
    return McpGateway(
        profile_id=os.environ.get("AGENTCORE_USAGE_PROFILE", "default"),
        tenant_id=os.environ.get("AGENTCORE_TENANT_ID", ""),
        workspace_id=os.environ.get("AGENTCORE_WORKSPACE_ID", ""),
        project_id=os.environ.get("AGENTCORE_PROJECT_ID", ""),
    )


def main() -> int:
    try:
        gateway = gateway_from_env()
    except Exception as exc:
        # Keep stdio MCP process from dying without a clear stderr signal for IDE logs.
        print(f"error: MCP gateway failed to start: {exc}", file=sys.stderr)
        return 1
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            err = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "parse error"},
            }
            sys.stdout.write(json.dumps(err) + "\n")
            sys.stdout.flush()
            continue
        response = handle_message(gateway, message)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
    return 0
