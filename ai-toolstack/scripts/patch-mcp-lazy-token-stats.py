#!/usr/bin/env python3
"""Inject token-stats JSONL logging into local mcp-lazy dist/index.js."""
from __future__ import annotations

import sys
from pathlib import Path

MARKER = "// thinkingSOC: mcp-lazy token stats"
OLD_STATS_BLOCK = """// thinkingSOC: mcp-lazy token stats
const __tsStats = require(process.env.AI_TOOLSTACK_TOKEN_STATS_CJS || require("path").join(process.cwd(), "ai-toolstack/lib/mcp-lazy-token-stats.cjs"));
function __estimateTokens(n) { return Math.max(0, Math.round((n || 0) / 4)); }
"""
STATS_REQUIRE = """// thinkingSOC: mcp-lazy token stats
import { createRequire } from "module";
const __require = createRequire(import.meta.url);
const __tsStats = __require(process.env.AI_TOOLSTACK_TOKEN_STATS_CJS || __require("path").join(process.cwd(), "ai-toolstack/lib/mcp-lazy-token-stats.cjs"));
function __estimateTokens(n) { return Math.max(0, Math.round((n || 0) / 4)); }
"""

INJECTIONS: list[tuple[str, str]] = [
    (
        '__mcpLazyDebug("serve", "cache hit", { toolCount: registry.getToolCount(), elapsedMs: elapsed });',
        '__mcpLazyDebug("serve", "cache hit", { toolCount: registry.getToolCount(), elapsedMs: elapsed });\n'
        '    try { __tsStats.logSessionSchemaSavings(registry.getToolCount()); } catch (_) {}',
    ),
    (
        '__mcpLazyDebug("serve", "stale cache used", { toolCount: registry.getToolCount(), elapsedMs: elapsed });',
        '__mcpLazyDebug("serve", "stale cache used", { toolCount: registry.getToolCount(), elapsedMs: elapsed });\n'
        '    try { __tsStats.logSessionSchemaSavings(registry.getToolCount()); } catch (_) {}',
    ),
    (
        '      if (results.length === 0) {\n        const allServers = registry.getServerNames();',
        '      if (results.length === 0) {\n        const allServers = registry.getServerNames();',
    ),
]

# Patch search: empty and non-empty returns
SEARCH_EMPTY_OLD = """        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({
                results: [],
                suggestion: `No tools found for "${query}". Available servers: ${allServers.join(", ")}. Try different keywords.`
              })
            }
          ]
        };"""

SEARCH_EMPTY_NEW = """        const __searchEmptyText = JSON.stringify({
                results: [],
                suggestion: `No tools found for "${query}". Available servers: ${allServers.join(", ")}. Try different keywords.`
              });
        try { __tsStats.logSearch(query, limit, __searchEmptyText); } catch (_) {}
        return {
          content: [
            {
              type: "text",
              text: __searchEmptyText
            }
          ]
        };"""

SEARCH_HIT_OLD = """      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({ results })
          }
        ]
      };"""

SEARCH_HIT_NEW = """      const __searchHitText = JSON.stringify({ results });
      try { __tsStats.logSearch(query, limit, __searchHitText); } catch (_) {}
      return {
        content: [
          {
            type: "text",
            text: __searchHitText
          }
        ]
      };"""

EXEC_OK_OLD = """        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result)"""

EXEC_OK_NEW = """        const __execText = JSON.stringify(result);
        try { __tsStats.logExecute(server_name, tool_name, __execText, false, args ?? {}); } catch (_) {}
        return {
          content: [
            {
              type: "text",
              text: __execText"""

EXEC_ERR_OLD = """        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({
                error: message,"""

EXEC_ERR_NEW = """        const __execErrText = JSON.stringify({
                error: message,"""


EXEC_ARGS_OLD = "__tsStats.logExecute(server_name, tool_name, __execText, false);"
EXEC_ARGS_NEW = "__tsStats.logExecute(server_name, tool_name, __execText, false, args ?? {});"


def patch_index_js(text: str) -> str:
    if OLD_STATS_BLOCK in text:
        text = text.replace(OLD_STATS_BLOCK, STATS_REQUIRE + "\n", 1)

    if MARKER not in text:
        if not text.startswith("#!/usr/bin/env node"):
            raise RuntimeError("unexpected index.js format (no shebang)")
        first_nl = text.index("\n")
        insert_at = first_nl + 1
        if "// thinkingSOC: mcp-lazy verbose debug" in text:
            dbg_end = text.index("var __defProp", insert_at)
            text = text[:dbg_end] + STATS_REQUIRE + "\n" + text[dbg_end:]
        else:
            text = text[:insert_at] + STATS_REQUIRE + "\n" + text[insert_at:]

    replacements = [
        (SEARCH_EMPTY_OLD, SEARCH_EMPTY_NEW, "__searchEmptyText"),
        (SEARCH_HIT_OLD, SEARCH_HIT_NEW, "__searchHitText"),
        (EXEC_OK_OLD, EXEC_OK_NEW, "__execText"),
    ]
    for old, new, marker in replacements:
        if marker in text:
            continue
        if old not in text:
            raise RuntimeError(f"token-stats patch anchor missing: {old[:60]!r}...")
        text = text.replace(old, new, 1)

    for anchor, snippet in INJECTIONS:
        if snippet.strip() in text:
            continue
        if anchor not in text:
            raise RuntimeError(f"token-stats injection anchor missing: {anchor[:60]!r}...")
        text = text.replace(anchor, snippet, 1)

    if EXEC_ARGS_OLD in text:
        text = text.replace(EXEC_ARGS_OLD, EXEC_ARGS_NEW, 1)

    return text


def verify_patch(text: str) -> None:
    required = [
        "__tsStats.logSessionSchemaSavings",
        "__tsStats.logSearch",
        "__tsStats.logExecute",
        "logExecute(server_name, tool_name, __execText, false, args",
    ]
    missing = [marker for marker in required if marker not in text]
    if missing:
        raise RuntimeError(f"token-stats patch incomplete: missing {missing}")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: patch-mcp-lazy-token-stats.py <path/to/mcp-lazy/dist/index.js>", file=sys.stderr)
        return 2
    target = Path(sys.argv[1])
    if not target.is_file():
        raise RuntimeError(f"not found: {target}")
    before = target.read_text(encoding="utf-8")
    after = patch_index_js(before)
    verify_patch(after)
    if after == before:
        print("already patched (token-stats)")
        return 0
    target.write_text(after, encoding="utf-8")
    print(f"patched token-stats: {target}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
