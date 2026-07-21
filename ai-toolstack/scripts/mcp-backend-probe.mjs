#!/usr/bin/env node
/**
 * Probe a single MCP backend (same transport as mcp-lazy discovery).
 * Usage: MCP_LOCAL_NODE_MODULES=/path/to/data/local/node_modules \
 *        node mcp-backend-probe.mjs '<json-server-config>' [name]
 */
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const localModules =
  process.env.MCP_LOCAL_NODE_MODULES ||
  join(here, "..", "data", "local", "node_modules");
const require = createRequire(join(localModules, "mcp-lazy/package.json"));

const { Client } = require("@modelcontextprotocol/sdk/client/index.js");
const { StdioClientTransport } = require("@modelcontextprotocol/sdk/client/stdio.js");

const config = JSON.parse(process.argv[2] ?? "{}");
const name = process.argv[3] ?? "backend";
const timeoutMs = Number(process.env.MCP_PROBE_TIMEOUT_MS ?? 45000);

if (!config.command) {
  console.error(`SKIP ${name}: no command`);
  process.exit(2);
}

const client = new Client({ name: "mcp-lazy-diagnose", version: "1.0" });
const transport = new StdioClientTransport({
  command: config.command,
  args: config.args ?? [],
  env: { ...process.env, ...(config.env ?? {}) },
  cwd: config.cwd,
});

const timer = setTimeout(() => {
  console.error(`TIMEOUT ${name}: no MCP handshake within ${timeoutMs}ms`);
  process.exit(124);
}, timeoutMs);

const t0 = Date.now();
try {
  await client.connect(transport);
  const tools = await client.listTools();
  clearTimeout(timer);
  console.log(
    `OK ${name}: ${tools.tools.length} tools in ${Date.now() - t0}ms`
  );
  await client.close();
  process.exit(0);
} catch (err) {
  clearTimeout(timer);
  console.error(
    `FAIL ${name}: ${err instanceof Error ? err.message : String(err)} (${Date.now() - t0}ms)`
  );
  process.exit(1);
}
