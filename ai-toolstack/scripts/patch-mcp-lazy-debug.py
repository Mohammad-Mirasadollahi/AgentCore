#!/usr/bin/env python3
"""Inject verbose debug logging and stale-cache fast path into local mcp-lazy."""
from __future__ import annotations

import sys
from pathlib import Path

MARKER = "// thinkingSOC: mcp-lazy verbose debug"
STALE_MARKER = "// thinkingSOC: stale cache fast path"

DEBUG_HELPER = """
// thinkingSOC: mcp-lazy verbose debug
function __mcpLazyDebug(phase, msg, data) {
  if (process.env.MCP_LAZY_VERBOSE !== "1" && process.env.MCP_LAZY_DEBUG !== "1") return;
  const ts = new Date().toISOString();
  const extra = data !== void 0 ? " " + JSON.stringify(data) : "";
  console.error("[mcp-lazy DEBUG " + ts + "][" + phase + "] " + msg + extra);
}
"""

CACHE_BLOCK_OLD = """  if (cached && cached.fingerprint === fingerprint) {
    for (const entry of cached.tools) {
      registry.addTool(entry);
    }
    const elapsed = Date.now() - startMs;
    console.error(`mcp-lazy: loaded ${registry.getToolCount()} tools from cache in ${elapsed}ms`);
    __mcpLazyDebug("serve", "cache hit", { toolCount: registry.getToolCount(), elapsedMs: elapsed });
  } else {
    const result = await discoverTools2(servers);
    __mcpLazyDebug("serve", "cache miss — running discovery", { serverNames });
    for (const entry of result.tools) {
      registry.addTool(entry);
    }
    const successCount = result.results.filter((r) => r.status === "fulfilled" && r.toolCount > 0).length;
    for (const r of result.results) {
      if (r.status === "rejected") {
        console.error(`Warning: could not connect to ${r.serverName}: ${r.error}`);
      }
    }
    const elapsed = Date.now() - startMs;
    console.error(`mcp-lazy: discovered ${registry.getToolCount()} tools from ${successCount} servers in ${elapsed}ms`);
    saveToolCache2(fingerprint, registry.getAllTools());
  }"""

CACHE_BLOCK_OLD_NO_DEBUG = """  if (cached && cached.fingerprint === fingerprint) {
    for (const entry of cached.tools) {
      registry.addTool(entry);
    }
    const elapsed = Date.now() - startMs;
    console.error(`mcp-lazy: loaded ${registry.getToolCount()} tools from cache in ${elapsed}ms`);
  } else {
    const result = await discoverTools2(servers);
    for (const entry of result.tools) {
      registry.addTool(entry);
    }
    const successCount = result.results.filter((r) => r.status === "fulfilled" && r.toolCount > 0).length;
    for (const r of result.results) {
      if (r.status === "rejected") {
        console.error(`Warning: could not connect to ${r.serverName}: ${r.error}`);
      }
    }
    const elapsed = Date.now() - startMs;
    console.error(`mcp-lazy: discovered ${registry.getToolCount()} tools from ${successCount} servers in ${elapsed}ms`);
    saveToolCache2(fingerprint, registry.getAllTools());
  }"""

CACHE_BLOCK_NEW = """  if (cached && cached.fingerprint === fingerprint) {
    for (const entry of cached.tools) {
      registry.addTool(entry);
    }
    const elapsed = Date.now() - startMs;
    console.error(`mcp-lazy: loaded ${registry.getToolCount()} tools from cache in ${elapsed}ms`);
    __mcpLazyDebug("serve", "cache hit", { toolCount: registry.getToolCount(), elapsedMs: elapsed });
  // thinkingSOC: stale cache fast path
  } else if (cached && Array.isArray(cached.tools) && cached.tools.length > 0) {
    for (const entry of cached.tools) {
      registry.addTool(entry);
    }
    const elapsed = Date.now() - startMs;
    console.error(`mcp-lazy: loaded ${registry.getToolCount()} tools from stale cache in ${elapsed}ms (servers.json changed; refreshing in background)`);
    __mcpLazyDebug("serve", "stale cache used", { toolCount: registry.getToolCount(), elapsedMs: elapsed });
    discoverTools2(servers).then((result) => {
      if (result.tools.length > 0) {
        saveToolCache2(computeServerFingerprint2(servers), result.tools);
        console.error(`mcp-lazy: background cache refresh complete (${result.tools.length} tools)`);
      }
    }).catch((err) => {
      const message = err instanceof Error ? err.message : String(err);
      console.error(`Warning: background cache refresh failed: ${message}`);
    });
  } else {
    const result = await discoverTools2(servers);
    __mcpLazyDebug("serve", "cache miss — running discovery", { serverNames });
    for (const entry of result.tools) {
      registry.addTool(entry);
    }
    const successCount = result.results.filter((r) => r.status === "fulfilled" && r.toolCount > 0).length;
    for (const r of result.results) {
      if (r.status === "rejected") {
        console.error(`Warning: could not connect to ${r.serverName}: ${r.error}`);
      }
    }
    const elapsed = Date.now() - startMs;
    console.error(`mcp-lazy: discovered ${registry.getToolCount()} tools from ${successCount} servers in ${elapsed}ms`);
    saveToolCache2(fingerprint, registry.getAllTools());
  }"""

REPLACEMENTS: list[tuple[str, str]] = [
    (
        "        options?.onServerDone?.(name, entries.length, elapsed);\n        results.push({",
        "        options?.onServerDone?.(name, entries.length, elapsed);\n        __mcpLazyDebug(\"discovery\", \"server done\", { name, toolCount: entries.length, elapsedMs: elapsed });\n        results.push({",
    ),
    (
        "        options?.onServerFailed?.(name, message, elapsed);\n        results.push({\n          serverName: name,\n          status: \"rejected\"",
        "        options?.onServerFailed?.(name, message, elapsed);\n        __mcpLazyDebug(\"discovery\", \"server failed\", { name, error: message, elapsedMs: elapsed });\n        results.push({\n          serverName: name,\n          status: \"rejected\"",
    ),
    (
        "        const client = await loader.getClient(server_name);\n        const result = await client.callTool({",
        "        const client = await loader.getClient(server_name);\n        __mcpLazyDebug(\"execute\", \"backend client ready\", { server_name });\n        const result = await client.callTool({",
    ),
    (
        "          arguments: args ?? {}\n        });\n        return {\n          content: [\n            {\n              type: \"text\",\n              text: JSON.stringify(result)",
        "          arguments: args ?? {}\n        });\n        __mcpLazyDebug(\"execute\", \"callTool returned\", { tool_name, server_name });\n        return {\n          content: [\n            {\n              type: \"text\",\n              text: JSON.stringify(result)",
    ),
    (
        "  await client.connect(transport);\n  return { client, transport };",
        "  await client.connect(transport);\n  __mcpLazyDebug(\"discovery\", \"connectToServer connected\", { command });\n  return { client, transport };",
    ),
    (
        "        await Promise.race([connectPromise, timeoutPromise]);\n        this.servers.set(serverName, {",
        "        await Promise.race([connectPromise, timeoutPromise]);\n        __mcpLazyDebug(\"loader\", \"attemptConnect ok\", { serverName });\n        this.servers.set(serverName, {",
    ),
    (
        "async function runServe() {\n  const { loadServersBackup: loadServersBackup2, computeServerFingerprint: computeServerFingerprint2, loadToolCache: loadToolCache2, saveToolCache: saveToolCache2 } = await Promise.resolve().then(() => (init_config(), config_exports));",
        "async function runServe() {\n  __mcpLazyDebug(\"serve\", \"runServe start\", { pid: process.pid, cwd: process.cwd() });\n  const { loadServersBackup: loadServersBackup2, computeServerFingerprint: computeServerFingerprint2, loadToolCache: loadToolCache2, saveToolCache: saveToolCache2 } = await Promise.resolve().then(() => (init_config(), config_exports));",
    ),
    (
        "  const loader = new ServerLoader2(servers);\n  await startProxyServer2(registry, loader);",
        "  const loader = new ServerLoader2(servers);\n  __mcpLazyDebug(\"serve\", \"proxy listening on stdio\", { toolCount: registry.getToolCount(), servers: serverNames });\n  await startProxyServer2(registry, loader);",
    ),
]

INJECTIONS: list[tuple[str, str]] = [
    (
        "async function connectToServer(command, args, env) {",
        '  __mcpLazyDebug("discovery", "connectToServer start", { command, args: args ?? [] });',
    ),
    (
        "async function discoverTools(servers, options) {",
        '  __mcpLazyDebug("discovery", "discoverTools start", { servers: Object.keys(servers) });',
    ),
    (
        "      options?.onServerStart?.(name);\n      const serverStart = Date.now();",
        '      __mcpLazyDebug("discovery", "server start", { name, command: serverConfig.command });',
    ),
    (
        "      async loadServer(serverName) {\n        const config = this.serverConfigs[serverName];",
        '        __mcpLazyDebug("loader", "loadServer", { serverName });',
    ),
    (
        "        const timeoutMs = 3e4;\n        if (!config.command) {",
        '        __mcpLazyDebug("loader", "attemptConnect start", { serverName, command: config.command, timeoutMs: 3e4 });',
    ),
    (
        '    async ({ query, limit }) => {\n      const results = registry.search(query, limit);',
        '      __mcpLazyDebug("search", "mcp_search_tools", { query, limit });',
    ),
    (
        '    async ({ tool_name, server_name, arguments: args }) => {\n      const tool = registry.findTool(tool_name, server_name);',
        '      __mcpLazyDebug("execute", "mcp_execute_tool", { tool_name, server_name });',
    ),
    (
        "      } catch (error) {\n        const message = error instanceof Error ? error.message : String(error);\n        const alternatives = registry.search(tool_name, 3);",
        '        __mcpLazyDebug("execute", "callTool failed", { tool_name, server_name, error: message });',
    ),
]


def patch_stale_cache(text: str) -> str:
    if STALE_MARKER in text:
        return text
    for old in (CACHE_BLOCK_OLD, CACHE_BLOCK_OLD_NO_DEBUG):
        if old in text:
            return text.replace(old, CACHE_BLOCK_NEW, 1)
    raise RuntimeError("stale cache patch target not found in runServe()")


def patch_index_js(text: str) -> str:
    if STALE_MARKER in text and MARKER in text and "__mcpLazyDebug" in text:
        return text

    if MARKER not in text:
        if not text.startswith("#!/usr/bin/env node"):
            raise RuntimeError("unexpected index.js format (no shebang)")
        first_newline = text.index("\n")
        text = text[: first_newline + 1] + DEBUG_HELPER + text[first_newline + 1 :]

    # Stale-cache fast path must run before debug injections that touch runServe().
    text = patch_stale_cache(text)

    for anchor, snippet in INJECTIONS:
        if snippet.strip() in text:
            continue
        if anchor not in text:
            raise RuntimeError(f"patch anchor not found: {anchor[:70]!r}...")
        text = text.replace(anchor, anchor + "\n" + snippet, 1)

    for anchor, replacement in REPLACEMENTS:
        if anchor not in text:
            raise RuntimeError(f"replacement anchor not found: {anchor[:70]!r}...")
        if replacement.split("\n")[1] in text if "\n" in replacement else replacement in text:
            continue
        text = text.replace(anchor, replacement, 1)

    return text


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: patch-mcp-lazy-debug.py <path/to/mcp-lazy/dist/index.js>", file=sys.stderr)
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
