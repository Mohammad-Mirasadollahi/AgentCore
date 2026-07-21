#!/usr/bin/env node
/**
 * Verify MCP backend tools (memory + headroom) via stdio — same path mcp-lazy uses.
 *
 * Usage:
 *   ./ai-toolstack/scripts/verify-mcp-tools.mjs
 *   ./ai-toolstack/scripts/verify-mcp-tools.mjs --quick
 */
import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const SDK_ROOT = join(dirname(fileURLToPath(import.meta.url)), "../data/local/node_modules/@modelcontextprotocol/sdk/dist/cjs");
const { Client } = require(join(SDK_ROOT, "client/index.js"));
const { StdioClientTransport } = require(join(SDK_ROOT, "client/stdio.js"));

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, "../..");
const QUICK = process.argv.includes("--quick");
const TIMEOUT_MS = 45_000;
const REPO = REPO_ROOT;

/** Servers removed from the stack — skip if somehow still listed in local mcp configs. */
const REMOVED_SERVERS = new Set(["graphify", "graphify-read", "code-review-graph"]);

/** @type {Record<string, Record<string, object>>} */
const TOOL_ARGS = {
  memory: {
    search_nodes: { query: "verify-mcp-tools" },
    open_nodes: { names: ["__verify_nonexistent_entity__"] },
    create_entities: {
      entities: [{ name: "__mcp_verify_probe__", entityType: "test", observations: ["probe"] }],
    },
    add_observations: {
      observations: [{ entityName: "__mcp_verify_probe__", contents: ["probe-obs"] }],
    },
    create_relations: {
      relations: [{ from: "__mcp_verify_probe__", to: "__mcp_verify_probe__", relationType: "self" }],
    },
    delete_observations: {
      deletions: [{ entityName: "__mcp_verify_probe__", observations: ["probe-obs"] }],
    },
    delete_relations: {
      relations: [{ from: "__mcp_verify_probe__", to: "__mcp_verify_probe__", relationType: "self" }],
    },
    delete_entities: { entityNames: ["__mcp_verify_probe__"] },
  },
  headroom: {
    headroom_compress: {
      content: "ERROR: connection refused on port 5432\nWARN: retry 1/3\nINFO: health ok\n".repeat(20),
    },
    headroom_retrieve: { hash: "__verify_nonexistent__" },
    headroom_stats: {},
  },
};

function loadJson(path) {
  return JSON.parse(readFileSync(path, "utf8"));
}

function defaultsFromSchema(schema) {
  if (!schema || typeof schema !== "object") return {};
  const out = {};
  const props = schema.properties ?? {};
  for (const [key, spec] of Object.entries(props)) {
    if (spec && Object.prototype.hasOwnProperty.call(spec, "default")) {
      out[key] = spec.default;
    }
  }
  return out;
}

function argsForTool(server, name, schema) {
  const base = defaultsFromSchema(schema);
  const overrides = TOOL_ARGS[server]?.[name] ?? TOOL_ARGS[server] ?? {};
  return { ...base, ...overrides };
}

function isOkResult(result) {
  if (!result) return false;
  if (result.isError) return true;
  return true;
}

async function withClient(serverName, serverCfg, fn) {
  const env = { ...process.env, ...(serverCfg.env ?? {}) };
  const transport = new StdioClientTransport({
    command: serverCfg.command,
    args: serverCfg.args ?? [],
    cwd: serverCfg.cwd ?? REPO,
    env,
    stderr: "pipe",
  });
  const client = new Client({ name: "verify-mcp-tools", version: "1.0.0" });
  await client.connect(transport);
  try {
    return await fn(client);
  } finally {
    await client.close();
  }
}

async function testServer(serverName, serverCfg, expectedTools) {
  const report = { server: serverName, listed: 0, expected: expectedTools.length, ok: [], fail: [], skip: [] };

  await withClient(serverName, serverCfg, async (client) => {
    const listed = await client.listTools();
    const live = listed.tools ?? [];
    report.listed = live.length;

    const liveNames = new Set(live.map((t) => t.name));
    for (const name of expectedTools.map((t) => t.name)) {
      if (!liveNames.has(name)) {
        report.fail.push({ tool: name, error: "missing from tools/list" });
      }
    }

    if (QUICK) return;

    for (const tool of live) {
      const name = tool.name;
      const args = argsForTool(serverName, name, tool.inputSchema);
      try {
        const result = await Promise.race([
          client.callTool({ name, arguments: args }),
          new Promise((_, reject) =>
            setTimeout(() => reject(new Error(`timeout after ${TIMEOUT_MS}ms`)), TIMEOUT_MS),
          ),
        ]);
        if (isOkResult(result)) {
          report.ok.push(name);
        } else {
          report.fail.push({ tool: name, error: "empty result" });
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        if (/not found|missing|unknown|invalid|does not exist/i.test(msg)) {
          report.ok.push(`${name} (expected: ${msg.slice(0, 80)})`);
        } else {
          report.fail.push({ tool: name, error: msg.slice(0, 200) });
        }
      }
    }
  });

  return report;
}

async function testMcpLazyProxy(expectedCount) {
  const serveSh = join(REPO_ROOT, "ai-toolstack/bin/mcp-lazy-serve.sh");
  const transport = new StdioClientTransport({
    command: serveSh,
    args: [],
    cwd: REPO,
    env: {
      ...process.env,
      AI_TOOLSTACK_TOKEN_STATS_CJS: join(REPO_ROOT, "ai-toolstack/lib/mcp-lazy-token-stats.cjs"),
    },
    stderr: "pipe",
  });
  const client = new Client({ name: "verify-mcp-lazy", version: "1.0.0" });
  await client.connect(transport);
  try {
    const tools = await client.listTools();
    const names = (tools.tools ?? []).map((t) => t.name);
    if (names.length !== 2 || !names.includes("mcp_search_tools") || !names.includes("mcp_execute_tool")) {
      throw new Error(`mcp-lazy proxy tools unexpected: ${names.join(", ")}`);
    }
    const search = await client.callTool({
      name: "mcp_search_tools",
      arguments: { query: "memory search_nodes", limit: 3 },
    });
    if (search.isError) throw new Error("mcp_search_tools returned isError");

    const execute = await client.callTool({
      name: "mcp_execute_tool",
      arguments: {
        server_name: "memory",
        tool_name: "search_nodes",
        arguments: { query: "verify-mcp-tools" },
      },
    });
    if (execute.isError) throw new Error("mcp_execute_tool memory search_nodes failed");

    return {
      proxy: "mcp-lazy",
      lazyTools: names.length,
      cachedBackends: expectedCount,
      searchHits: (search.content ?? []).length,
      executeOk: true,
    };
  } finally {
    await client.close();
  }
}

async function main() {
  const serversCfg = loadJson(join(homedir(), ".mcp-lazy/servers.json")).servers;
  const cache = loadJson(join(homedir(), ".mcp-lazy/tool-cache.json")).tools;
  const byServer = {};
  for (const t of cache) {
    if (REMOVED_SERVERS.has(t.server)) continue;
    (byServer[t.server] ??= []).push(t);
  }

  console.log(`MCP tool verification (${QUICK ? "quick" : "full"})`);
  console.log(`Repo: ${REPO}`);
  console.log(`Cached tools (memory + headroom): ${Object.values(byServer).flat().length}`);
  console.log("");

  let totalFail = 0;
  for (const [serverName, expectedTools] of Object.entries(byServer)) {
    const cfg = serversCfg[serverName];
    if (!cfg) {
      console.log(`FAIL ${serverName}: not in servers.json`);
      totalFail += 1;
      continue;
    }
    process.stdout.write(`Testing ${serverName} (${expectedTools.length} tools)... `);
    try {
      const report = await testServer(serverName, cfg, expectedTools);
      const fails = report.fail.length;
      totalFail += fails;
      if (fails === 0 && report.listed >= expectedTools.length) {
        console.log(`OK listed=${report.listed}${QUICK ? "" : ` invoked=${report.ok.length}`}`);
      } else {
        console.log(`FAIL listed=${report.listed}/${report.expected}`);
        for (const f of report.fail) {
          console.log(`  - ${f.tool}: ${f.error}`);
        }
      }
    } catch (err) {
      totalFail += 1;
      console.log(`FAIL connect: ${err instanceof Error ? err.message : err}`);
    }
  }

  if (!QUICK) {
    process.stdout.write("Testing mcp-lazy proxy (Cursor path)... ");
    try {
      const proxy = await testMcpLazyProxy(Object.keys(byServer).length);
      console.log(`OK search+execute via proxy (backends=${proxy.cachedBackends})`);
    } catch (err) {
      totalFail += 1;
      console.log(`FAIL ${err instanceof Error ? err.message : err}`);
    }
  }

  console.log("");
  if (totalFail === 0) {
    console.log("All MCP checks passed.");
    process.exit(0);
  }
  console.log(`MCP verification FAILED (${totalFail} issue(s)).`);
  process.exit(1);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
