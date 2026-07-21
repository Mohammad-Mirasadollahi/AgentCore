#!/usr/bin/env python3
"""Accept server/tool aliases and flat backend args on mcp_execute_tool (ThinkingSOC)."""
from __future__ import annotations

import sys
from pathlib import Path

MARKER = "// thinkingSOC: mcp-lazy execute aliases"

HELPER = """
// thinkingSOC: mcp-lazy execute aliases
function __mcpLazyNormalizeExecuteInput(raw) {
  const tool_name = raw.tool_name ?? raw.tool;
  const server_name = raw.server_name ?? raw.server;
  const reserved = new Set(["tool_name", "server_name", "tool", "server", "arguments"]);
  let args = raw.arguments;
  if (args === void 0 || args === null) {
    args = {};
    for (const [k, v] of Object.entries(raw)) {
      if (!reserved.has(k)) args[k] = v;
    }
  }
  return { tool_name, server_name, args: args ?? {} };
}
"""

OLD_SCHEMA_HANDLER = """    {
      tool_name: z2.string().describe("Tool name from mcp_search_tools"),
      server_name: z2.string().describe("Server name from mcp_search_tools"),
      arguments: z2.record(z2.unknown()).optional().describe("Tool arguments")
    },
    async ({ tool_name, server_name, arguments: args }) => {
      const tool = registry.findTool(tool_name, server_name);
      __mcpLazyDebug("execute", "mcp_execute_tool", { tool_name, server_name });"""

NEW_SCHEMA_HANDLER = """    {
      tool_name: z2.string().optional().describe("Tool name from mcp_search_tools"),
      server_name: z2.string().optional().describe("Server name from mcp_search_tools"),
      tool: z2.string().optional().describe("Alias for tool_name"),
      server: z2.string().optional().describe("Alias for server_name"),
      arguments: z2.record(z2.unknown()).optional().describe("Tool arguments")
    },
    async (raw) => {
      const { tool_name, server_name, args } = __mcpLazyNormalizeExecuteInput(raw);
      if (!tool_name || !server_name) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({
                error: "mcp_execute_tool requires server_name and tool_name (aliases: server, tool). Use mcp_search_tools first.",
                received_keys: Object.keys(raw ?? {})
              })
            }
          ],
          isError: true
        };
      }
      const tool = registry.findTool(tool_name, server_name);
      __mcpLazyDebug("execute", "mcp_execute_tool", { tool_name, server_name });"""

BROKEN_SCHEMA_HANDLER = """    z2.object({
      tool_name: z2.string().optional().describe("Tool name from mcp_search_tools"),
      server_name: z2.string().optional().describe("Server name from mcp_search_tools"),
      tool: z2.string().optional().describe("Alias for tool_name"),
      server: z2.string().optional().describe("Alias for server_name"),
      arguments: z2.record(z2.unknown()).optional().describe("Tool arguments")
    }).passthrough(),
    async (raw) => {
      const { tool_name, server_name, args } = __mcpLazyNormalizeExecuteInput(raw);
      if (!tool_name || !server_name) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({
                error: "mcp_execute_tool requires server_name and tool_name (aliases: server, tool). Use mcp_search_tools first.",
                received_keys: Object.keys(raw ?? {})
              })
            }
          ],
          isError: true
        };
      }
      const tool = registry.findTool(tool_name, server_name);
      __mcpLazyDebug("execute", "mcp_execute_tool", { tool_name, server_name });"""


def patch_index_js(text: str) -> str:
    if MARKER in text and "__mcpLazyNormalizeExecuteInput" in text:
        if BROKEN_SCHEMA_HANDLER in text:
            text = text.replace(BROKEN_SCHEMA_HANDLER, NEW_SCHEMA_HANDLER, 1)
        elif NEW_SCHEMA_HANDLER.split("async (raw)")[0] in text:
            return text
        elif OLD_SCHEMA_HANDLER in text:
            pass
        else:
            return text

    if OLD_SCHEMA_HANDLER not in text and BROKEN_SCHEMA_HANDLER not in text:
        if NEW_SCHEMA_HANDLER.split("async (raw)")[0] in text:
            return text
        raise RuntimeError("mcp_execute_tool patch target not found in dist/index.js")

    if MARKER not in text:
        anchor = "function __mcpLazyDebug(phase, msg, data) {"
        if anchor not in text:
            raise RuntimeError("__mcpLazyDebug anchor not found — run patch-mcp-lazy-debug.py first")
        text = text.replace(anchor, HELPER + "\n" + anchor, 1)

    text = text.replace(OLD_SCHEMA_HANDLER, NEW_SCHEMA_HANDLER, 1)
    if BROKEN_SCHEMA_HANDLER in text:
        text = text.replace(BROKEN_SCHEMA_HANDLER, NEW_SCHEMA_HANDLER, 1)
    return text


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: patch-mcp-lazy-execute-aliases.py <path/to/mcp-lazy/dist/index.js>", file=sys.stderr)
        return 2
    target = Path(sys.argv[1])
    if not target.is_file():
        raise RuntimeError(f"not found: {target}")
    before = target.read_text(encoding="utf-8")
    after = patch_index_js(before)
    if after == before:
        print("already patched")
        return 0
    target.write_text(after, encoding="utf-8")
    print(f"patched {target}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
