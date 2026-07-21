#!/usr/bin/env node
/**
 * Real-world Headroom demo on ThinkingSOC content.
 * Uses the same MCP stdio path as Cursor (headroom-mcp-serve.sh).
 */
import { readFileSync, writeFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO = join(__dirname, "../..");
const SERVERS = JSON.parse(
  readFileSync(join(process.env.HOME, ".mcp-lazy/servers.json"), "utf8"),
);
const SDK = join(REPO, "ai-toolstack/data/local/node_modules/@modelcontextprotocol/sdk/dist/cjs");
const { Client } = require(join(SDK, "client/index.js"));
const { StdioClientTransport } = require(join(SDK, "client/stdio.js"));

function estTokens(text) {
  return Math.ceil(String(text).length / 4);
}

function loadSamples() {
  const grepOut = execFileSync(
    "rg",
    ["-n", "--no-heading", "token|compress|headroom|rtk|mcp-lazy", "ai-toolstack/", "-g", "*.py", "-g", "*.md", "-g", "*.sh"],
    { cwd: REPO, encoding: "utf8", maxBuffer: 10 * 1024 * 1024 },
  );

  const codeFile = readFileSync(join(REPO, "ai-toolstack/install.sh"), "utf8");
  const docFile = readFileSync(join(REPO, "ai-toolstack/docs/token-optimization-overview.md"), "utf8");

  return [
    {
      id: "grep-toolstack",
      label: "Simulated rg/Grep tool output (203 matches)",
      content: grepOut,
      qualityCheck: /headroom/i,
      retrieveQuery: "headroom",
    },
    {
      id: "read-install-sh",
      label: "Simulated Read: ai-toolstack/install.sh",
      content: codeFile,
      qualityCheck: /ensure_headroom_server/,
      retrieveQuery: "ensure_headroom",
    },
    {
      id: "read-token-doc",
      label: "Simulated Read: token-optimization-overview.md",
      content: docFile,
      qualityCheck: /Ponytail|Headroom|RTK/i,
      retrieveQuery: "Headroom",
    },
  ];
}

async function withHeadroom(fn) {
  const cfg = SERVERS.servers.headroom;
  const transport = new StdioClientTransport({
    command: cfg.command,
    args: cfg.args ?? [],
    cwd: cfg.cwd ?? REPO,
    env: { ...process.env, ...cfg.env },
    stderr: "pipe",
  });
  const client = new Client({ name: "headroom-real-demo", version: "1.0.0" });
  await client.connect(transport);
  try {
    return await fn(client);
  } finally {
    await client.close();
  }
}

function parseToolJson(result) {
  const text = result?.content?.find((c) => c.type === "text")?.text ?? "";
  try {
    return JSON.parse(text);
  } catch {
    return { raw: text };
  }
}

async function compressSample(client, sample) {
  const before = estTokens(sample.content);
  const t0 = Date.now();
  const result = await client.callTool({
    name: "headroom_compress",
    arguments: { content: sample.content },
  });
  const ms = Date.now() - t0;
  if (result.isError) throw new Error(parseToolJson(result).raw ?? "compress failed");

  const data = parseToolJson(result);
  const compressed = data.compressed ?? "";
  const after = data.compressed_tokens ?? estTokens(compressed);
  const beforeMeasured = data.original_tokens ?? before;
  const saved = Math.max(0, beforeMeasured - after);
  const pct = beforeMeasured ? Math.round((100 * saved) / beforeMeasured) : 0;

  let retrieveOk = false;
  let retrieveSnippet = "";
  if (data.hash && sample.retrieveQuery) {
    const ret = await client.callTool({
      name: "headroom_retrieve",
      arguments: { hash: data.hash, query: sample.retrieveQuery },
    });
    const retData = parseToolJson(ret);
    const blob =
      retData.original_content ??
      retData.results ??
      retData.content ??
      JSON.stringify(retData);
    retrieveSnippet = String(blob).slice(0, 120).replace(/\s+/g, " ");
    retrieveOk = sample.qualityCheck.test(String(blob));
  }

  const qualityInCompressed = sample.qualityCheck.test(compressed);

  return {
    id: sample.id,
    label: sample.label,
    charsBefore: sample.content.length,
    charsAfter: compressed.length,
    tokensBefore: beforeMeasured,
    tokensAfter: after,
    tokensSaved: saved,
    savingsPct: data.savings_percent ?? pct,
    transforms: data.transforms ?? [],
    ms,
    hash: data.hash?.slice(0, 16),
    qualityInCompressed,
    retrieveOk,
    retrieveSnippet,
  };
}

async function main() {
  const samples = loadSamples();
  const rows = [];

  console.log("=".repeat(72));
  console.log("Headroom REAL demo — ThinkingSOC content via MCP (Cursor path)");
  console.log("=".repeat(72));
  console.log(`Repo: ${REPO}`);
  console.log(`Server: ${SERVERS.servers.headroom.command}`);
  console.log("");

  await withHeadroom(async (client) => {
    for (const sample of samples) {
      const row = await compressSample(client, sample);
      rows.push(row);
    }

    const stats = await client.callTool({ name: "headroom_stats", arguments: {} });
    const statsText = stats.content?.find((c) => c.type === "text")?.text ?? "";
    rows._stats = statsText.split("\n").slice(0, 8).join("\n");
  });

  let totalBefore = 0;
  let totalAfter = 0;

  for (const r of rows) {
    if (!r.id) continue;
    totalBefore += r.tokensBefore;
    totalAfter += r.tokensAfter;
    console.log(`--- ${r.label} ---`);
    console.log(`  Chars:     ${r.charsBefore.toLocaleString()} → ${r.charsAfter.toLocaleString()}`);
    console.log(`  Tokens:    ${r.tokensBefore.toLocaleString()} → ${r.tokensAfter.toLocaleString()}  (${r.savingsPct}% saved)`);
    console.log(`  Transforms: ${(r.transforms || []).join(", ") || "passthrough/minimal"}`);
    console.log(`  Latency:   ${r.ms}ms  |  hash: ${r.hash}…`);
    console.log(`  Quality:   signal in compressed=${r.qualityInCompressed ? "YES" : "NO"}  retrieve query=${r.retrieveOk ? "YES" : "NO"}`);
    if (r.retrieveSnippet) console.log(`  Retrieve:  "${r.retrieveSnippet}…"`);
    console.log("");
  }

  const totalSaved = totalBefore - totalAfter;
  const totalPct = totalBefore ? Math.round((100 * totalSaved) / totalBefore) : 0;
  console.log("=".repeat(72));
  console.log("TOTAL (3 agent-like payloads)");
  console.log(`  ${totalBefore.toLocaleString()} → ${totalAfter.toLocaleString()} tokens  (${totalPct}% saved, ${totalSaved.toLocaleString()} tokens)`);
  console.log("");
  console.log("Session stats (headroom_stats):");
  console.log(rows._stats || "(none)");
  console.log("");
  console.log("When Headroom helps vs RTK:");
  console.log("  RTK        → shell output (git status, pytest, docker logs)");
  console.log("  Headroom   → large Read/grep/JSON/MCP results (this demo)");
  console.log("  Discovery  → repo docs + path-scoped rg");
  console.log("=".repeat(72));

  const reportPath = join(REPO, "ai-toolstack/data/headroom/demo-report.json");
  writeFileSync(
    reportPath,
    JSON.stringify({ generatedAt: new Date().toISOString(), rows: rows.filter((r) => r.id), totals: { totalBefore, totalAfter, totalSaved, totalPct } }, null, 2),
  );
  console.log(`Report: ${reportPath}`);
}

main().catch((e) => {
  console.error("Demo failed:", e.message ?? e);
  process.exit(1);
});
