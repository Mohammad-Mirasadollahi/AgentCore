#!/usr/bin/env node
/**
 * Comprehensive compression lanes test — RTK (Shell) + Headroom (blobs).
 * Validates complementary coverage, token savings, quality, and false-positive risks.
 */
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { execFileSync, spawnSync } from "node:child_process";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO = join(__dirname, "../..");
const require = createRequire(join(REPO, "ai-toolstack/data/local/node_modules/mcp-lazy/package.json"));
const { Client } = require("@modelcontextprotocol/sdk/client/index.js");
const { StdioClientTransport } = require("@modelcontextprotocol/sdk/client/stdio.js");

const RTK = process.env.RTK_BIN || "/root/.local/bin/rtk";

function estTokens(text) {
  return Math.ceil(Buffer.byteLength(String(text), "utf8") / 4);
}

function runShell(argv, { useRtk = false, cwd = REPO, timeout = 120000 } = {}) {
  const args = useRtk && existsSync(RTK) ? [RTK, ...argv] : argv;
  const proc = spawnSync(args[0], args.slice(1), {
    cwd,
    encoding: "utf8",
    maxBuffer: 30 * 1024 * 1024,
    timeout,
  });
  const out = `${proc.stdout || ""}${proc.stderr || ""}`;
  return { out, exit: proc.status ?? -1 };
}

function qualityChecks(raw, filtered, checks) {
  const results = checks.map((c) => {
    const inRaw = c.pattern.test(raw);
    const inFiltered = c.pattern.test(filtered);
    return {
      name: c.name,
      inRaw,
      inFiltered,
      falsePositiveRisk: inRaw && !inFiltered,
      ok: inFiltered || !inRaw,
    };
  });
  const lost = results.filter((r) => r.falsePositiveRisk);
  return { results, lostCount: lost.length, allOk: lost.length === 0 };
}

async function withHeadroom(fn) {
  const servers = JSON.parse(readFileSync(join(process.env.HOME, ".mcp-lazy/servers.json"), "utf8"));
  const cfg = servers.servers.headroom;
  const transport = new StdioClientTransport({
    command: cfg.command,
    args: cfg.args ?? [],
    cwd: cfg.cwd ?? REPO,
    env: { ...process.env, ...cfg.env },
  });
  const client = new Client({ name: "compression-lanes-test", version: "2.0" });
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

async function headroomCompress(client, content, qualityCheck, retrieveQuery) {
  const before = estTokens(content);
  const result = await client.callTool({
    name: "headroom_compress",
    arguments: { content },
  });
  if (result.isError) throw new Error("headroom_compress failed");
  const data = parseToolJson(result);
  const compressed = data.compressed ?? "";
  const after = data.compressed_tokens ?? estTokens(compressed);
  let retrieveOk = false;
  if (data.hash && retrieveQuery) {
    const ret = await client.callTool({
      name: "headroom_retrieve",
      arguments: { hash: data.hash, query: retrieveQuery },
    });
    const retData = parseToolJson(ret);
    const blob = String(
      retData.original_content ?? retData.results ?? retData.content ?? JSON.stringify(retData),
    );
    retrieveOk = qualityCheck.test(blob);
  }
  const signalInCompressed = qualityCheck.test(compressed);
  const needleInSource = qualityCheck.test(content);
  return {
    tokensBefore: data.original_tokens ?? before,
    tokensAfter: after,
    tokensSaved: Math.max(0, (data.original_tokens ?? before) - after),
    savingsPct: data.savings_percent ?? 0,
    transforms: data.transforms ?? [],
    bypassed: !!data.bypassed,
    signalInCompressed,
    retrieveOk,
    falsePositiveRisk: needleInSource && !signalInCompressed && !retrieveOk,
    retrieveRecovers: needleInSource && !signalInCompressed && retrieveOk,
    qualityOk: !needleInSource || signalInCompressed || retrieveOk,
    compressedPreview: compressed.slice(0, 200).replace(/\s+/g, " "),
  };
}

/** What each lane should own — used for coverage verdict */
const COVERAGE_MATRIX = [
  { source: "Shell: git status", lane: "RTK", rtkExpected: true, headroomExpected: false },
  { source: "Shell: ps / docker / pytest", lane: "RTK", rtkExpected: true, headroomExpected: false },
  { source: "Shell: eslint via rtk lint", lane: "RTK", rtkExpected: true, headroomExpected: false },
  { source: "Shell: cat huge log (RTK passthrough)", lane: "Headroom", rtkExpected: false, headroomExpected: true },
  { source: "Tool Read: large source file", lane: "Headroom", rtkExpected: false, headroomExpected: true },
  { source: "Grep/rg dump (non-Shell tool output)", lane: "Headroom", rtkExpected: false, headroomExpected: true },
  { source: "Large MCP/JSON blob (Headroom)", lane: "Headroom", rtkExpected: false, headroomExpected: true },
  { source: "RTK-filtered Shell (double compress)", lane: "Skip", rtkExpected: false, headroomExpected: false },
];

const report = {
  generatedAt: new Date().toISOString(),
  repo: REPO,
  rtkHook: null,
  rtkShell: [],
  headroomBlobs: [],
  gaps: [],
  doubleCompress: null,
  coverageMatrix: COVERAGE_MATRIX,
  summary: {},
};

// --- RTK hook status ---
const hooksPath = join(REPO, "ai-toolstack/data/local/cursor-hooks.json");
if (existsSync(hooksPath)) {
  const hooks = JSON.parse(readFileSync(hooksPath, "utf8"));
  report.rtkHook = hooks?.hooks?.preToolUse?.[0] ?? null;
}

console.log("=".repeat(78));
console.log("COMPREHENSIVE compression lanes test — RTK (Shell) + Headroom (blobs)");
console.log("=".repeat(78));
console.log(`Repo: ${REPO}`);
console.log(`RTK: ${existsSync(RTK) ? RTK : "MISSING"}`);
console.log(`Hook: ${report.rtkHook ? report.rtkHook.command : "NOT CONFIGURED"}\n`);

function printRtkCase(c, row) {
  console.log(`--- [RTK] ${c.id}: ${row.command} ---`);
  console.log(`  Lane owner: RTK (Shell automatic)`);
  console.log(`  Tokens: ${row.rawTokens.toLocaleString()} → ${row.rtkTokens.toLocaleString()} (${row.savingsPct}% saved)`);
  console.log(`  Quality: ${row.quality.lostCount} signal(s) lost`);
  for (const r of row.quality.results) {
    console.log(`    [${r.falsePositiveRisk ? "LOST" : r.inFiltered ? "OK" : "n/a"}] ${r.name}`);
  }
  if (c.note) console.log(`  Note: ${c.note}`);
  console.log("");
}

// --- Lane A: RTK shell cases ---
console.log("## Lane A — RTK (Shell, automatic via preToolUse hook)\n");

const shellCases = [
  {
    id: "git-status",
    argv: ["git", "status", "--short"],
    checks: [
      { name: "tracked change markers", pattern: /[MADRCU?!]/ },
      { name: "file paths", pattern: /\.(py|sh|md|tsx?|json|mdc)/ },
    ],
  },
  {
    id: "ps-aux-head",
    argv: ["ps", "aux"],
    checks: [
      { name: "header row preserved", pattern: /USER.*PID.*COMMAND/ },
      { name: "init process visible", pattern: /sbin\/init|systemd/ },
    ],
    note: "RTK truncates tail — use `ps aux | rg name` when hunting a specific process",
  },
  {
    id: "rg-docs",
    argv: ["rg", "-n", "--no-heading", "compression lanes|RTK|Headroom", "ai-toolstack/docs/", "-g", "*.md"],
    checks: [
      { name: "headroom doc hits", pattern: /headroom-integration/i },
    ],
  },
  {
    id: "docker-ps",
    argv: ["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}"],
    checks: [{ name: "container table or empty", pattern: /NAMES|CONTAINER|Cannot connect|permission denied/i }],
    optional: true,
  },
  {
    id: "rtk-lint",
    argv: ["lint", "app/system/settings", "--max-warnings=0"],
    cwd: join(REPO, "frontend"),
    checks: [
      { name: "summary counts", pattern: /\d+\s+(errors?|warnings?)/i },
      { name: "top rules listed", pattern: /Top rules|@typescript-eslint/i },
    ],
    note: "Use `rtk lint` not `rtk eslint` — hook maps eslint → lint",
    timeout: 180000,
  },
];

for (const c of shellCases) {
  const cwd = c.cwd ?? REPO;
  const raw = runShell(c.argv, { cwd, timeout: c.timeout });
  if (c.optional && /Cannot connect|not found|No such file/i.test(raw.out)) {
    console.log(`--- [RTK] ${c.id}: skipped (${raw.out.slice(0, 60).replace(/\s+/g, " ")}) ---\n`);
    continue;
  }
  const rtk = runShell(c.argv, { useRtk: true, cwd, timeout: c.timeout });
  const q = qualityChecks(raw.out, rtk.out, c.checks);
  const row = {
    id: c.id,
    lane: "RTK",
    command: (cwd !== REPO ? `(cwd ${cwd.replace(REPO + "/", "")}) ` : "") + c.argv.join(" "),
    rawTokens: estTokens(raw.out),
    rtkTokens: estTokens(rtk.out),
    saved: Math.max(0, estTokens(raw.out) - estTokens(rtk.out)),
    savingsPct:
      estTokens(raw.out) > 0
        ? Math.round((100 * (estTokens(raw.out) - estTokens(rtk.out))) / estTokens(raw.out))
        : 0,
    quality: q,
  };
  report.rtkShell.push(row);
  printRtkCase(c, row);
}

// --- Gap: cat log — RTK does NOT compress; Headroom should ---
console.log("## Gap test — cat log (RTK passthrough → Headroom lane)\n");

const logCandidates = [
  "backend/logs/runner_final_test.log",
  "backend/logs/1.log",
].map((p) => join(REPO, p)).filter(existsSync);
if (logCandidates.length) {
  const logPath = logCandidates[0];
  const rel = logPath.replace(REPO + "/", "");
  const rawCat = runShell(["cat", rel]);
  const rtkCat = runShell(["cat", rel], { useRtk: true });
  const gap = {
    id: "cat-log",
    file: rel,
    rawTokens: estTokens(rawCat.out),
    rtkTokens: estTokens(rtkCat.out),
    rtkCompresses: estTokens(rtkCat.out) < estTokens(rawCat.out) * 0.95,
    correctLane: "Headroom",
  };
  report.gaps.push(gap);
  console.log(`--- cat ${rel} ---`);
  console.log(`  Raw: ${gap.rawTokens.toLocaleString()} tok | RTK: ${gap.rtkTokens.toLocaleString()} tok`);
  console.log(
    `  RTK compresses cat? ${gap.rtkCompresses ? "YES (unexpected)" : "NO — agent must use Headroom on Read/cat blob"}`,
  );
  console.log("");
}

// --- Lane B: Headroom ---
console.log("## Lane B — Headroom (Read / grep / MCP / log blobs)\n");

const grepBlob = execFileSync(
  "rg",
  ["-n", "--no-heading", "token|compress|headroom|rtk", "ai-toolstack/", "-g", "*.py", "-g", "*.md"],
  { cwd: REPO, encoding: "utf8", maxBuffer: 12 * 1024 * 1024 },
);
const installSh = readFileSync(join(REPO, "ai-toolstack/install.sh"), "utf8");
const tokenDoc = readFileSync(join(REPO, "ai-toolstack/docs/token-optimization-overview.md"), "utf8");

// Synthetic large JSON blob for Headroom lane (mcp-lazy backends: memory + headroom)
const largeMcpJson = JSON.stringify(
  {
    note: "synthetic MCP-sized payload for Headroom lane",
    backends: ["memory", "headroom"],
    rows: Array.from({ length: 200 }, (_, i) => ({
      id: i,
      path: `backend/docs/standards/sample/doc-${i}.md`,
      excerpt: `token compress headroom rtk mcp-lazy lane-${i} `.repeat(8),
    })),
  },
  null,
  2,
);

const headroomCases = [
  {
    id: "grep-toolstack",
    label: "Grep/rg dump (tool output, not Shell lane)",
    content: grepBlob,
    qualityCheck: /apply_rtk_shell_hook|compression.lanes/i,
    retrieveQuery: "apply_rtk_shell_hook",
  },
  {
    id: "read-install-sh",
    label: "Read: install.sh",
    content: installSh,
    qualityCheck: /apply_rtk_shell_hook/,
    retrieveQuery: "apply_rtk_shell_hook",
  },
  {
    id: "read-token-doc",
    label: "Read: token-optimization-overview.md",
    content: tokenDoc,
    qualityCheck: /Ponytail|Headroom|RTK/i,
    retrieveQuery: "Headroom",
  },
  {
    id: "mcp-large-json",
    label: "Large MCP/JSON blob (Headroom)",
    content: largeMcpJson,
    qualityCheck: /headroom|mcp-lazy/i,
    retrieveQuery: "headroom",
  },
];

if (logCandidates.length) {
  const logContent = readFileSync(logCandidates[0], "utf8").slice(0, 400000);
  headroomCases.push({
    id: "read-log-file",
    label: `Read/cat blob: ${logCandidates[0].replace(REPO + "/", "")}`,
    content: logContent,
    qualityCheck: /ERROR|WARN|INFO|trace_id/i,
    retrieveQuery: "ERROR",
  });
}

await withHeadroom(async (client) => {
  for (const c of headroomCases) {
    const row = { id: c.id, label: c.label, lane: "Headroom", ...(await headroomCompress(client, c.content, c.qualityCheck, c.retrieveQuery)) };
    report.headroomBlobs.push(row);
    console.log(`--- [Headroom] ${c.id}: ${c.label} ---`);
    console.log(`  Lane owner: Headroom (on-demand MCP)`);
    console.log(`  Tokens: ${row.tokensBefore.toLocaleString()} → ${row.tokensAfter.toLocaleString()} (${row.savingsPct}% saved)`);
    console.log(`  Transforms: ${(row.transforms || []).join(", ") || "minimal"}`);
    console.log(`  Quality: compressed=${row.signalInCompressed ? "YES" : "NO"} retrieve=${row.retrieveOk ? "YES" : "NO"} overall=${row.qualityOk ? "OK" : "RISK"}`);
    if (row.falsePositiveRisk) console.log(`  ⚠ RISK: needle lost without retrieve`);
    else if (row.retrieveRecovers) console.log(`  ✓ Expected: summary + retrieve for detail`);
    else if (row.signalInCompressed) console.log(`  ✓ Signal kept in compressed text`);
    console.log("");
  }

  const gitRtk = runShell(["git", "status", "--short"], { useRtk: true });
  const double = await headroomCompress(client, gitRtk.out, /install\.sh/, "install");
  report.doubleCompress = {
    lane: "Skip (anti-pattern)",
    rtkTokens: estTokens(gitRtk.out),
    afterHeadroom: double.tokensAfter,
    delta: double.tokensAfter - estTokens(gitRtk.out),
    skipHeadroomOnShell: double.tokensAfter >= estTokens(gitRtk.out) * 0.9,
    ...double,
  };
  console.log("--- [Skip] double-compress: Headroom on RTK git status ---");
  console.log(`  RTK ${report.doubleCompress.rtkTokens} tok → Headroom ${report.doubleCompress.afterHeadroom} tok (delta ${report.doubleCompress.delta >= 0 ? "+" : ""}${report.doubleCompress.delta})`);
  console.log(`  Verdict: ${report.doubleCompress.skipHeadroomOnShell ? "DO NOT double-compress Shell" : "unexpected savings"}\n`);

  // --- Hard guard: RTK marker bypass ---
  const MARKER = "<!-- thinkingSOC:rtk-lane -->";
  const markedShell = `${gitRtk.out}\n${MARKER}`;
  const bypass = await headroomCompress(client, markedShell, /install\.sh/, "install");
  report.guardBypass = {
    marker: MARKER,
    bypassed: bypass.bypassed || bypass.transforms?.includes("thinkingSOC:rtk-lane-bypass"),
    tokensBefore: bypass.tokensBefore,
    tokensAfter: bypass.tokensAfter,
    savingsPct: bypass.savingsPct,
  };
  console.log("--- [Guard] Headroom bypass on RTK lane marker ---");
  console.log(`  Marker present → bypassed=${report.guardBypass.bypassed ? "YES" : "NO"}`);
  console.log(`  Tokens: ${report.guardBypass.tokensBefore} → ${report.guardBypass.tokensAfter} (saved ${report.guardBypass.savingsPct}%)\n`);

  // --- headroom_read (disk-first) vs cat ---
  if (logCandidates.length) {
    const logPath = logCandidates[0];
    try {
      const readRes = await client.callTool({
        name: "headroom_read",
        arguments: { file_path: logPath, fresh: true },
      });
      const readData = parseToolJson(readRes);
      const readText = JSON.stringify(readData);
      report.headroomRead = {
        file: logPath.replace(REPO + "/", ""),
        tokensEst: estTokens(readText),
        cached: !!readData.cached || !!readData.cache_hit,
        ok: !readRes.isError,
      };
      console.log("--- [Headroom] headroom_read (disk-first, no cat) ---");
      console.log(`  File: ${report.headroomRead.file}`);
      console.log(`  Response ~${report.headroomRead.tokensEst.toLocaleString()} tok in MCP (not terminal)`);
      console.log(`  Prefer over: cat ${report.headroomRead.file} (${report.gaps[0]?.rawTokens?.toLocaleString() ?? "?"} tok in shell)\n`);
    } catch (e) {
      console.log(`--- [Headroom] headroom_read skipped: ${e.message}\n`);
    }
  }
});

// --- Summary ---
const rtkRaw = report.rtkShell.reduce((s, r) => s + r.rawTokens, 0);
const rtkOut = report.rtkShell.reduce((s, r) => s + r.rtkTokens, 0);
const hrIn = report.headroomBlobs.reduce((s, r) => s + r.tokensBefore, 0);
const hrOut = report.headroomBlobs.reduce((s, r) => s + r.tokensAfter, 0);
const fpRtk = report.rtkShell.reduce((s, r) => s + r.quality.lostCount, 0);
const fpHr = report.headroomBlobs.filter((r) => r.falsePositiveRisk).length;
const hrOk = report.headroomBlobs.filter((r) => r.qualityOk).length;

const combinedRaw = rtkRaw + hrIn + (report.gaps[0]?.rawTokens ?? 0);
const combinedSaved =
  rtkRaw - rtkOut + (hrIn - hrOut) + (report.gaps[0] && !report.gaps[0].rtkCompresses ? Math.max(0, report.gaps[0].rawTokens - (report.headroomBlobs.find((b) => b.id === "read-log-file")?.tokensAfter ?? report.gaps[0].rawTokens)) : 0);

report.summary = {
  rtkShell: { raw: rtkRaw, out: rtkOut, saved: rtkRaw - rtkOut, pct: rtkRaw ? Math.round((100 * (rtkRaw - rtkOut)) / rtkRaw) : 0 },
  headroomBlobs: { in: hrIn, out: hrOut, saved: hrIn - hrOut, pct: hrIn ? Math.round((100 * (hrIn - hrOut)) / hrIn) : 0, qualityOk: `${hrOk}/${report.headroomBlobs.length}` },
  falsePositiveSignals: { rtk: fpRtk, headroom: fpHr },
  hookConfigured: !!report.rtkHook,
  complementary:
    fpHr === 0 &&
    report.gaps.every((g) => !g.rtkCompresses) &&
    (report.guardBypass?.bypassed ?? false),
};

console.log("=".repeat(78));
console.log("COVERAGE MATRIX (complementary lanes)");
for (const row of COVERAGE_MATRIX) {
  console.log(`  ${row.source.padEnd(42)} → ${row.lane}`);
}
console.log("");
console.log("SUMMARY");
console.log(`  RTK Shell:      ${rtkRaw.toLocaleString()} → ${rtkOut.toLocaleString()} tok (${report.summary.rtkShell.pct}% saved, ${fpRtk} quality loss)`);
console.log(`  Headroom blobs: ${hrIn.toLocaleString()} → ${hrOut.toLocaleString()} tok (${report.summary.headroomBlobs.pct}% saved, quality ${report.summary.headroomBlobs.qualityOk})`);
console.log(`  Hook active:    ${report.summary.hookConfigured ? "YES" : "NO — run ./ai-toolstack/install.sh"}`);
console.log(`  RTK bypass guard: ${report.guardBypass?.bypassed ? "YES" : "NO"}`);
console.log(`  Complementary:  ${report.summary.complementary ? "YES — lanes + hard guardrails OK" : "REVIEW gaps above"}`);
console.log(`  Est. combined savings (this run): ~${(rtkRaw - rtkOut + hrIn - hrOut).toLocaleString()} tokens`);
console.log("=".repeat(78));

const outPath = join(REPO, "ai-toolstack/data/headroom/compression-lanes-test-report.json");
writeFileSync(outPath, JSON.stringify(report, null, 2));
console.log(`Full JSON: ${outPath}`);
