#!/usr/bin/env node
/**
 * End-to-end Headroom MCP test (compress → retrieve → stats).
 * Also exercises mcp-lazy proxy path for headroom tools.
 */
import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO = join(__dirname, "../..");
const LOCAL = join(REPO, "ai-toolstack/data/local");
const SERVERS_JSON = join(homedir(), ".mcp-lazy/servers.json");
const SDK_ROOT = join(LOCAL, "node_modules/@modelcontextprotocol/sdk/dist/cjs");
const { Client } = require(join(SDK_ROOT, "client/index.js"));
const { StdioClientTransport } = require(join(SDK_ROOT, "client/stdio.js"));

const TIMEOUT_MS = 60_000;

function loadServers() {
  return JSON.parse(readFileSync(SERVERS_JSON, "utf8"));
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
  const client = new Client({ name: "verify-headroom-e2e", version: "1.0.0" });
  await client.connect(transport);
  try {
    return await fn(client);
  } finally {
    await client.close();
  }
}

function textFromResult(result) {
  const block = result?.content?.find((c) => c.type === "text");
  return block?.text ?? "";
}

function parseJson(text) {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

async function testDirectHeadroom(serverCfg) {
  console.log("\n=== Direct Headroom MCP (stdio) ===");

  return withClient("headroom", serverCfg, async (client) => {
    const listed = await client.listTools();
    const names = (listed.tools ?? []).map((t) => t.name).sort();
    console.log(`tools/list: ${names.join(", ")}`);
    const expected = ["headroom_compress", "headroom_retrieve", "headroom_stats"];
    for (const n of expected) {
      if (!names.includes(n)) throw new Error(`missing tool: ${n}`);
    }

    const sampleLog = [
      "ERROR: connection refused on port 5432",
      "FATAL: database unreachable",
      "WARN: retry 1/3 failed",
      "INFO: health check ok",
    ]
      .flatMap((line) => Array.from({ length: 50 }, (_, i) => `${line} seq=${i}`))
      .join("\n");

    const compress = await Promise.race([
      client.callTool({ name: "headroom_compress", arguments: { content: sampleLog } }),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error("headroom_compress timeout")), TIMEOUT_MS),
      ),
    ]);
    if (compress.isError) throw new Error(`headroom_compress isError: ${textFromResult(compress)}`);

    const compressText = textFromResult(compress);
    const compressJson = parseJson(compressText);
    if (!compressJson?.hash) {
      throw new Error(`headroom_compress missing hash: ${compressText.slice(0, 300)}`);
    }
    const hash = compressJson.hash;
    const savings = compressJson.savings_percent ?? compressJson.savingsPercent;
    console.log(
      `headroom_compress: hash=${hash.slice(0, 12)}… tokens ${compressJson.original_tokens ?? "?"} → ${compressJson.compressed_tokens ?? "?"} (${savings ?? "?"}% saved)`,
    );

    const retrieve = await Promise.race([
      client.callTool({ name: "headroom_retrieve", arguments: { hash } }),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error("headroom_retrieve timeout")), TIMEOUT_MS),
      ),
    ]);
    if (retrieve.isError) throw new Error(`headroom_retrieve isError: ${textFromResult(retrieve)}`);
    const retrieveText = textFromResult(retrieve);
    const retrieveJson = parseJson(retrieveText);
    const original =
      retrieveJson?.original_content ?? retrieveJson?.content ?? retrieveText;
    if (!original || String(original).length < 100) {
      throw new Error("headroom_retrieve returned too little content");
    }
    if (!String(original).includes("FATAL")) {
      throw new Error("headroom_retrieve lost critical FATAL line");
    }
    console.log(`headroom_retrieve: OK (${String(original).length} chars, FATAL preserved)`);

    const stats = await client.callTool({ name: "headroom_stats", arguments: {} });
    if (stats.isError) throw new Error(`headroom_stats isError: ${textFromResult(stats)}`);
    const statsText = textFromResult(stats);
    console.log(`headroom_stats: ${statsText.split("\n")[0].slice(0, 120)}`);

    return { hash, compressJson };
  });
}

async function testMcpLazyHeadroom() {
  console.log("\n=== mcp-lazy proxy → headroom ===");
  const npx = join(LOCAL, "bin/npx");
  const pathPrefix = join(LOCAL, "bin");
  const env = { ...process.env, PATH: `${pathPrefix}:${process.env.PATH ?? ""}` };
  const transport = new StdioClientTransport({
    command: npx,
    args: ["-y", "mcp-lazy", "serve"],
    cwd: REPO,
    env,
    stderr: "pipe",
  });
  const client = new Client({ name: "verify-headroom-lazy", version: "1.0.0" });
  await client.connect(transport);
  try {
    const search = await client.callTool({
      name: "mcp_search_tools",
      arguments: { query: "headroom compress", limit: 5 },
    });
    if (search.isError) throw new Error("mcp_search_tools failed");
    const searchText = textFromResult(search);
    if (!/headroom_compress/i.test(searchText)) {
      throw new Error(`search did not surface headroom_compress: ${searchText.slice(0, 200)}`);
    }
    console.log("mcp_search_tools: found headroom_compress");

    const payload = "ERROR: disk full\n".repeat(200);
    const execute = await Promise.race([
      client.callTool({
        name: "mcp_execute_tool",
        arguments: {
          server_name: "headroom",
          tool_name: "headroom_compress",
          arguments: { content: payload },
        },
      }),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error("mcp_execute_tool timeout")), TIMEOUT_MS),
      ),
    ]);
    if (execute.isError) throw new Error(`mcp_execute_tool isError: ${textFromResult(execute)}`);
    const execText = textFromResult(execute);
    const execJson = parseJson(execText);
    const inner = execJson?.content?.[0]?.text ? parseJson(execJson.content[0].text) : execJson;
    const hasHash =
      inner?.hash ||
      execJson?.hash ||
      /"hash"\s*:/.test(execText) ||
      /"compressed"\s*:/.test(execText);
    if (!hasHash) {
      throw new Error(`mcp_execute_tool bad response: ${execText.slice(0, 300)}`);
    }
    console.log("mcp_execute_tool(headroom_compress): OK");
  } finally {
    await client.close();
  }
}

async function main() {
  console.log("Headroom E2E verification");
  console.log(`Repo: ${REPO}`);
  console.log(`Servers: ${SERVERS_JSON}`);

  const servers = loadServers();
  if (!servers.servers?.headroom) {
    throw new Error("headroom missing from mcp-lazy servers.json — run ./ai-toolstack/install.sh");
  }

  await testDirectHeadroom(servers.servers.headroom);
  await testMcpLazyHeadroom();

  console.log("\n✓ All Headroom E2E checks passed.");
}

main().catch((err) => {
  console.error("\n✗ Headroom E2E FAILED:", err.message ?? err);
  process.exit(1);
});
