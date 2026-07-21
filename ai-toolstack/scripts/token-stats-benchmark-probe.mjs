#!/usr/bin/env node
/**
 * Live MCP probes for token-stats-benchmark (same transport as mcp-lazy).
 * Prints JSON array of { id, label, bytes, tokens, ms, ok, preview }.
 */
import { createRequire } from "node:module";
import { readFileSync, existsSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const repo = process.env.REPO_ROOT || process.cwd();
const localModules =
  process.env.AI_TOOLSTACK_LOCAL_NODE_MODULES ||
  join(repo, "ai-toolstack/data/local/node_modules");
const require = createRequire(join(localModules, "mcp-lazy/package.json"));
const { Client } = require("@modelcontextprotocol/sdk/client/index.js");
const { StdioClientTransport } = require("@modelcontextprotocol/sdk/client/stdio.js");

function tok(bytes) {
  return Math.max(0, Math.round((bytes || 0) / 4));
}

async function callMcp(cmd, args, cwd, env, toolName, toolArgs) {
  const transport = new StdioClientTransport({
    command: cmd,
    args: args || [],
    cwd,
    env: { ...process.env, ...env },
  });
  const client = new Client({ name: "token-benchmark", version: "1.0" });
  const t0 = Date.now();
  try {
    await client.connect(transport);
    const r = await client.callTool({ name: toolName, arguments: toolArgs || {} });
    const text = (r.content || []).map((c) => c.text || "").join("");
    await client.close();
    return { ok: true, bytes: Buffer.byteLength(text, "utf8"), ms: Date.now() - t0, text };
  } catch (e) {
    try {
      await client.close();
    } catch {
      /* ignore */
    }
    const msg = e instanceof Error ? e.message : String(e);
    return { ok: false, bytes: Buffer.byteLength(msg, "utf8"), ms: Date.now() - t0, text: msg };
  }
}

function searchToolsSimulation(query, limit = 5) {
  const cachePath = join(homedir(), ".mcp-lazy/tool-cache.json");
  if (!existsSync(cachePath)) {
    return { ok: false, bytes: 0, text: "tool-cache.json missing" };
  }
  const cache = JSON.parse(readFileSync(cachePath, "utf8"));
  const tools = cache.tools || [];
  const q = query.toLowerCase().split(/\s+/).filter(Boolean);
  const scored = [];
  for (const t of tools) {
    const hay = `${t.name} ${t.description || ""}`.toLowerCase();
    let score = 0;
    for (const w of q) if (hay.includes(w)) score++;
    if (score) scored.push(t);
  }
  const results = scored.slice(0, limit).map((t) => ({
    tool_name: t.name,
    server_name: t.server,
    description: (t.description || "").slice(0, 120),
  }));
  const text = JSON.stringify({ results });
  return { ok: true, bytes: Buffer.byteLength(text, "utf8"), text };
}

function schemaSizes() {
  const cachePath = join(homedir(), ".mcp-lazy/tool-cache.json");
  let fullBytes = 0;
  let toolCount = 0;
  if (existsSync(cachePath)) {
    const cache = JSON.parse(readFileSync(cachePath, "utf8"));
    toolCount = (cache.tools || []).length;
    fullBytes = Buffer.byteLength(JSON.stringify(cache.tools || []), "utf8");
  }
  const proxy = [
    { name: "mcp_search_tools", description: "search" },
    { name: "mcp_execute_tool", description: "execute" },
  ];
  const proxyBytes = Buffer.byteLength(JSON.stringify(proxy), "utf8");
  return { toolCount, fullBytes, proxyBytes };
}

const probes = [];

const schemas = schemaSizes();
probes.push({
  id: "mcp_schema_direct",
  label: "MCP schemas if all tools registered directly (per turn)",
  bytes: schemas.fullBytes,
  tokens: tok(schemas.fullBytes),
  ms: 0,
  ok: true,
  meta: { tool_count: schemas.toolCount },
});

probes.push({
  id: "mcp_schema_lazy",
  label: "MCP schemas via mcp-lazy proxy (per turn)",
  bytes: schemas.proxyBytes,
  tokens: tok(schemas.proxyBytes),
  ms: 0,
  ok: true,
  saved_vs_direct: tok(schemas.fullBytes - schemas.proxyBytes),
});

const s1 = searchToolsSimulation("memory search_nodes");
probes.push({
  id: "mcp_search_memory",
  label: "mcp_search_tools('memory search_nodes')",
  bytes: s1.bytes,
  tokens: tok(s1.bytes),
  ms: 0,
  ok: s1.ok,
});

const memCmd = join(
  repo,
  "ai-toolstack/data/local/node_modules/.bin/mcp-server-memory"
);
const headroomCmd = join(repo, "ai-toolstack/bin/headroom-mcp-serve.sh");

const mcpCases = [
  {
    id: "memory_search",
    label: "memory search_nodes",
    cmd: memCmd,
    env: { MEMORY_FILE_PATH: join(repo, "ai-toolstack/data/mcp-memory/memory.jsonl") },
    tool: "search_nodes",
    args: { query: "token" },
  },
  {
    id: "headroom_compress_sample",
    label: "headroom_compress (sample payload)",
    cmd: headroomCmd,
    env: { HEADROOM_WORKSPACE_DIR: join(repo, "ai-toolstack/data/headroom") },
    tool: "headroom_compress",
    args: { text: "x".repeat(8000), hint: "benchmark" },
  },
];

for (const c of mcpCases) {
  if (!existsSync(c.cmd)) {
    probes.push({
      id: c.id,
      label: c.label,
      bytes: 0,
      tokens: 0,
      ms: 0,
      ok: false,
      preview: `missing: ${c.cmd}`,
    });
    continue;
  }
  const r = await callMcp(c.cmd, [], repo, c.env, c.tool, c.args);
  probes.push({
    id: c.id,
    label: c.label,
    bytes: r.bytes,
    tokens: tok(r.bytes),
    ms: r.ms,
    ok: r.ok,
    preview: (r.text || "").slice(0, 120).replace(/\s+/g, " "),
  });
}

console.log(JSON.stringify({ repo, probes }, null, 0));
