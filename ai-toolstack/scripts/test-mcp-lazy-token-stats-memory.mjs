#!/usr/bin/env node
/**
 * Live test: mcp-lazy proxy -> memory.search_nodes -> token-stats events.jsonl
 */
import { createRequire } from "node:module";
import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";

const repo = process.env.REPO_ROOT || process.cwd();
const localModules = join(repo, "ai-toolstack/data/local/node_modules");
const require = createRequire(join(localModules, "mcp-lazy/package.json"));
const { Client } = require("@modelcontextprotocol/sdk/client/index.js");
const { StdioClientTransport } = require("@modelcontextprotocol/sdk/client/stdio.js");

const eventsPath = join(repo, "ai-toolstack/data/token-stats/events.jsonl");
const serveSh = join(repo, "ai-toolstack/bin/mcp-lazy-serve.sh");

function countMemoryEvents() {
  if (!existsSync(eventsPath)) return 0;
  const text = readFileSync(eventsPath, "utf8");
  return (text.match(/"component":"memory"/g) || []).length;
}

async function callLazy(toolName, args) {
  const transport = new StdioClientTransport({
    command: serveSh,
    args: [],
    cwd: repo,
    env: {
      ...process.env,
      REPO_ROOT: repo,
      AI_TOOLSTACK_TOKEN_STATS_DIR: join(repo, "ai-toolstack/data/token-stats"),
      AI_TOOLSTACK_TOKEN_STATS_CJS: join(repo, "ai-toolstack/lib/mcp-lazy-token-stats.cjs"),
    },
  });
  const client = new Client({ name: "memory-stats-test", version: "1.0" });
  await client.connect(transport);
  const r = await client.callTool({ name: toolName, arguments: args });
  await client.close();
  const text = (r.content || []).map((c) => c.text || "").join("");
  return { text, isError: !!r.isError };
}

const before = countMemoryEvents();
console.log(`memory events before: ${before}`);

const search = await callLazy("mcp_search_tools", { query: "memory search_nodes", limit: 5 });
const parsed = JSON.parse(search.text);
const hit = (parsed.results || []).find(
  (r) => r.server_name === "memory" && r.tool_name === "search_nodes"
);
if (!hit) {
  console.error("FAIL: memory.search_nodes not found in search results");
  console.error(search.text.slice(0, 500));
  process.exit(1);
}

const exec = await callLazy("mcp_execute_tool", {
  server_name: "memory",
  tool_name: "search_nodes",
  arguments: { query: "token stats test" },
});
if (exec.isError) {
  console.error("FAIL: mcp_execute_tool error:", exec.text.slice(0, 500));
  process.exit(1);
}

const after = countMemoryEvents();
console.log(`memory events after: ${after}`);
console.log(`execute preview: ${exec.text.slice(0, 160).replace(/\s+/g, " ")}`);

if (after <= before) {
  console.error("FAIL: no new memory component event in events.jsonl");
  process.exit(1);
}

const lastLine = readFileSync(eventsPath, "utf8").trim().split("\n").pop();
console.log(`last event: ${lastLine}`);
console.log("PASS: memory MCP call logged to token-stats");
