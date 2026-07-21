#!/usr/bin/env node
/**
 * Stress / challenge test — RTK + Headroom + guardrails.
 * Adversarial scenarios, per-component bottleneck attribution, token vs quality tradeoffs.
 *
 * Usage: node ai-toolstack/scripts/compression-lanes-stress-test.mjs
 * Report: ai-toolstack/data/headroom/compression-lanes-stress-report.json
 */
import { readFileSync, writeFileSync, existsSync, mkdtempSync, rmSync } from "node:fs";
import { execFileSync, spawnSync } from "node:child_process";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { performance } from "node:perf_hooks";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO = join(__dirname, "../..");
const require = createRequire(join(REPO, "ai-toolstack/data/local/node_modules/mcp-lazy/package.json"));
const { Client } = require("@modelcontextprotocol/sdk/client/index.js");
const { StdioClientTransport } = require("@modelcontextprotocol/sdk/client/stdio.js");

const RTK = process.env.RTK_BIN || "/root/.local/bin/rtk";
const MARKER = "<!-- thinkingSOC:rtk-lane -->";
const REPORT_PATH = join(REPO, "ai-toolstack/data/headroom/compression-lanes-stress-report.json");
const QUICK = process.argv.includes("--quick") || process.env.STRESS_QUICK === "1";
const SKIP_LINT = QUICK || process.env.STRESS_SKIP_LINT === "1";

const report = {
  generatedAt: new Date().toISOString(),
  repo: REPO,
  suite: "compression-lanes-stress-v1",
  cases: [],
  bottlenecks: [],
  summary: {},
};

function estTokens(text) {
  return Math.ceil(Buffer.byteLength(String(text ?? ""), "utf8") / 4);
}

function runShell(argv, { useRtk = false, cwd = REPO, timeout = 120000 } = {}) {
  const args = useRtk && existsSync(RTK) ? [RTK, ...argv] : argv;
  const t0 = performance.now();
  const proc = spawnSync(args[0], args.slice(1), {
    cwd,
    encoding: "utf8",
    maxBuffer: 40 * 1024 * 1024,
    timeout,
  });
  return {
    out: `${proc.stdout || ""}${proc.stderr || ""}`,
    exit: proc.status ?? -1,
    latencyMs: Math.round(performance.now() - t0),
  };
}

function record(caseDef) {
  report.cases.push(caseDef);
  if (caseDef.status === "FAIL") {
    report.bottlenecks.push({
      severity: caseDef.severity ?? "high",
      component: caseDef.component,
      id: caseDef.id,
      issue: caseDef.diagnosis,
      fix: caseDef.fixHint ?? "",
      metrics: caseDef.metrics ?? {},
    });
  } else if (caseDef.status === "WARN") {
    report.bottlenecks.push({
      severity: "medium",
      component: caseDef.component,
      id: caseDef.id,
      issue: caseDef.diagnosis,
      fix: caseDef.fixHint ?? "",
      metrics: caseDef.metrics ?? {},
    });
  }
  return caseDef;
}

function printCase(c) {
  const icon = { PASS: "✓", WARN: "⚠", FAIL: "✗", SKIP: "○" }[c.status] ?? "?";
  console.log(`${icon} [${c.component}] ${c.id} — ${c.status}`);
  console.log(`    ${c.title}`);
  if (c.metrics && Object.keys(c.metrics).length) {
    const m = c.metrics;
    const parts = [];
    if (m.tokensIn != null) parts.push(`in=${m.tokensIn.toLocaleString()}`);
    if (m.tokensOut != null) parts.push(`out=${m.tokensOut.toLocaleString()}`);
    if (m.savingsPct != null) parts.push(`saved=${m.savingsPct}%`);
    if (m.quality != null) parts.push(`quality=${m.quality}`);
    if (m.latencyMs != null) parts.push(`${m.latencyMs}ms`);
    if (parts.length) console.log(`    metrics: ${parts.join(" | ")}`);
  }
  if (c.status !== "PASS") console.log(`    → ${c.diagnosis}`);
  if (c.fixHint && c.status !== "PASS") console.log(`    fix: ${c.fixHint}`);
  console.log("");
}

async function withHeadroom(fn) {
  const servers = JSON.parse(readFileSync(join(process.env.HOME, ".mcp-lazy/servers.json"), "utf8"));
  const cfg = servers.servers.headroom;
  const t0 = performance.now();
  const transport = new StdioClientTransport({
    command: cfg.command,
    args: cfg.args ?? [],
    cwd: cfg.cwd ?? REPO,
    env: { ...process.env, ...cfg.env },
  });
  const client = new Client({ name: "compression-stress", version: "1.0" });
  await client.connect(transport);
  const connectMs = Math.round(performance.now() - t0);
  try {
    return await fn(client, connectMs);
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

async function headroomCompress(client, content, { retrieveQuery, qualityPattern } = {}) {
  const t0 = performance.now();
  const before = estTokens(content);
  const result = await client.callTool({
    name: "headroom_compress",
    arguments: { content },
  });
  const latencyMs = Math.round(performance.now() - t0);
  if (result.isError) throw new Error("headroom_compress failed");
  const data = parseToolJson(result);
  const compressed = String(data.compressed ?? "");
  const after = data.compressed_tokens ?? estTokens(compressed);
  let retrieveOk = false;
  if (data.hash && retrieveQuery && qualityPattern) {
    const ret = await client.callTool({
      name: "headroom_retrieve",
      arguments: { hash: data.hash, query: retrieveQuery },
    });
    const retData = parseToolJson(ret);
    const blob = String(
      retData.original_content ?? retData.results ?? retData.content ?? JSON.stringify(retData),
    );
    retrieveOk = qualityPattern.test(blob);
  }
  const signalInCompressed = qualityPattern ? qualityPattern.test(compressed) : true;
  const needleInSource = qualityPattern ? qualityPattern.test(content) : true;
  return {
    data,
    compressed,
    tokensBefore: data.original_tokens ?? before,
    tokensAfter: after,
    savingsPct:
      before > 0 ? Math.round((100 * (before - after)) / before) : 0,
    latencyMs,
    bypassed: !!data.bypassed,
    transforms: data.transforms ?? [],
    signalInCompressed,
    retrieveOk,
    qualityOk: !needleInSource || signalInCompressed || retrieveOk,
    falsePositiveRisk: needleInSource && !signalInCompressed && !retrieveOk,
  };
}

function synthNoisyLog(needle, lines = 8000) {
  const rows = [];
  for (let i = 0; i < lines; i++) {
    rows.push(`2026-06-27T12:00:${String(i % 60).padStart(2, "0")} INFO worker-${i % 50} heartbeat ok shard=${i % 12}`);
  }
  rows.splice(Math.floor(lines * 0.73), 0, needle);
  return rows.join("\n");
}

console.log("=".repeat(78));
console.log("COMPRESSION LANES STRESS TEST — challenge scenarios + bottleneck map");
console.log("=".repeat(78));
console.log(`Repo: ${REPO}`);
console.log(`RTK:  ${existsSync(RTK) ? RTK : "MISSING"}`);
console.log(`Mode: ${QUICK ? "quick (--quick / STRESS_QUICK=1)" : "full"}${SKIP_LINT ? " | lint skipped" : ""}`);
console.log("");

// ─── INFRA ───────────────────────────────────────────────────────────────────
console.log("## Phase 1 — Infrastructure\n");

record({
  id: "infra-rtk-binary",
  component: "Infra",
  title: "RTK binary on PATH",
  status: existsSync(RTK) ? "PASS" : "FAIL",
  diagnosis: existsSync(RTK) ? "ok" : "RTK missing — Shell lane is raw (largest token leak)",
  fixHint: "Install RTK + ./ai-toolstack/install.sh",
  metrics: {},
});

const hookPath = join(REPO, "ai-toolstack/data/local/cursor-hooks.json");
let hookCmd = "";
if (existsSync(hookPath)) {
  const hooks = JSON.parse(readFileSync(hookPath, "utf8"));
  hookCmd = hooks?.hooks?.preToolUse?.[0]?.command ?? "";
}
record({
  id: "infra-rtk-hook",
  component: "Hook",
  title: "RTK preToolUse hook configured",
  status: hookCmd.includes("rtk-cursor-hook") ? "PASS" : hookCmd ? "WARN" : "FAIL",
  diagnosis: hookCmd.includes("rtk-cursor-hook")
    ? "ok"
    : hookCmd
      ? `Unexpected hook: ${hookCmd}`
      : "No preToolUse hook — RTK not automatic",
  fixHint: "./ai-toolstack/install.sh",
  metrics: { hook: hookCmd || "none" },
});

const hookProbe = spawnSync(
  "bash",
  ["-c", `echo '${JSON.stringify({ tool_name: "Shell", tool_input: { command: "git status --short" } })}' | ${join(REPO, "ai-toolstack/hooks/rtk-cursor-hook.sh")}`],
  { encoding: "utf8", cwd: REPO },
);
let hookHasMarker = false;
try {
  const hookOut = JSON.parse(hookProbe.stdout || "{}");
  hookHasMarker = String(hookOut?.updated_input?.command ?? "").includes("thinkingSOC:rtk-lane");
} catch {
  /* ignore */
}
record({
  id: "infra-hook-watermark",
  component: "Hook",
  title: "Hook wraps Shell with RTK + lane marker",
  status: hookHasMarker ? "PASS" : "FAIL",
  diagnosis: hookHasMarker ? "ok" : "Hook output missing watermark — Headroom bypass guard ineffective",
  fixHint: "Check ai-toolstack/hooks/rtk-cursor-hook.sh + jq",
  metrics: {},
});

const serveProbe = spawnSync(join(REPO, "ai-toolstack/bin/headroom-mcp-serve.sh"), [], {
  encoding: "utf8",
  timeout: 2500,
});
const guardStarted = /HEADROOM_PYTHON=.*headroom-ai.*python3.*guard/.test(serveProbe.stderr || "");
record({
  id: "infra-headroom-guard",
  component: "Headroom",
  title: "Headroom MCP guard starts with pipx Python",
  status: guardStarted ? "PASS" : "FAIL",
  diagnosis: guardStarted
    ? "ok"
    : "headroom_mcp_guard failed to start — check headroom-mcp-serve.sh readlink -f",
  fixHint: "pipx install 'headroom-ai[mcp]' && ./ai-toolstack/install.sh",
  metrics: { stderrPreview: (serveProbe.stderr || "").split("\n").slice(-2).join(" ") },
});

// ─── RTK CHALLENGES ──────────────────────────────────────────────────────────
console.log("## Phase 2 — RTK lane (token vs signal)\n");

const gitRaw = runShell(["git", "status", "--short"]);
const gitRtk = runShell(["git", "status", "--short"], { useRtk: true });
const gitSavings =
  gitRaw.out.length > 0
    ? Math.round((100 * (estTokens(gitRaw.out) - estTokens(gitRtk.out))) / estTokens(gitRaw.out))
    : 0;
record({
  id: "rtk-git-savings",
  component: "RTK",
  title: "git status — RTK should not inflate tokens",
  status: estTokens(gitRtk.out) <= estTokens(gitRaw.out) * 1.15 ? "PASS" : "WARN",
  diagnosis:
    estTokens(gitRtk.out) <= estTokens(gitRaw.out) * 1.15
      ? "ok"
      : "RTK increased git status tokens — check hook double-wrap",
  metrics: {
    tokensIn: estTokens(gitRaw.out),
    tokensOut: estTokens(gitRtk.out),
    savingsPct: gitSavings,
    latencyMs: gitRtk.latencyMs,
    quality: "paths preserved",
  },
});

const psRaw = runShell(["ps", "aux"]);
const psRtk = runShell(["ps", "aux"], { useRtk: true });
const psSavings = Math.round((100 * (estTokens(psRaw.out) - estTokens(psRtk.out))) / estTokens(psRaw.out));
const psHeaderOk = /USER.*PID.*COMMAND/.test(psRtk.out);
record({
  id: "rtk-ps-compress",
  component: "RTK",
  title: "ps aux — heavy compression with header kept",
  status: psHeaderOk && psSavings >= 50 ? "PASS" : psHeaderOk ? "WARN" : "FAIL",
  diagnosis: !psHeaderOk
    ? "PS header lost — RTK broke structure"
    : psSavings < 50
      ? `Low savings (${psSavings}%) — RTK filter may be inactive`
      : "ok",
  fixHint: psSavings < 50 ? "Verify rtk on PATH and hook wraps with rtk prefix" : "",
  metrics: {
    tokensIn: estTokens(psRaw.out),
    tokensOut: estTokens(psRtk.out),
    savingsPct: psSavings,
    latencyMs: psRtk.latencyMs,
    quality: psHeaderOk ? "header OK" : "header LOST",
  },
});

const obscurePid = `thinkingSOC_obscure_stress_pid_${Date.now()}`;
const fakePsLine = `root      99999  0.0  0.0  obscure  S+   00:00   0:00 ${obscurePid}`;
const psTailRaw = `${psRaw.out.trim()}\n${fakePsLine}`;
const psTailRtk = runShell(["ps", "aux"], { useRtk: true });
const tailLost = psTailRaw.includes(obscurePid) && !psTailRtk.out.includes(obscurePid);
record({
  id: "rtk-ps-tail-blindspot",
  component: "RTK",
  title: "CHALLENGE: obscure process at ps tail — known truncation blindspot",
  status: "WARN",
  severity: "medium",
  diagnosis: tailLost
    ? "Tail process not in RTK output (expected) — use `ps aux | rg <name>` not full ps"
    : "Unexpected: tail process visible in RTK output",
  fixHint: "Agent rule: ps aux | rg <needle> for specific process hunting",
  metrics: {
    tokensIn: estTokens(psRaw.out),
    tokensOut: estTokens(psTailRtk.out),
    quality: tailLost ? "tail LOST (known)" : "tail visible",
  },
});

const lintCwd = join(REPO, "frontend");
if (SKIP_LINT) {
  record({
    id: "rtk-lint-escape-hatch",
    component: "RTK",
    title: "CHALLENGE: lint summary vs lint -v (progressive disclosure)",
    status: "SKIP",
    diagnosis: "Skipped (STRESS_SKIP_LINT=1 or --quick) — run full suite without flags for lint latency test",
    metrics: {},
  });
} else if (existsSync(lintCwd)) {
  const lintSummary = runShell(["lint", "app/system/settings", "--max-warnings=0"], {
    useRtk: true,
    cwd: lintCwd,
    timeout: 180000,
  });
  const lintVerbose = runShell(["lint", "-v", "app/system/settings", "--max-warnings=0"], {
    useRtk: true,
    cwd: lintCwd,
    timeout: 180000,
  });
  const summaryOnly = /\d+\s+errors?/i.test(lintSummary.out) && !/\d+:\d+/.test(lintSummary.out.slice(0, 800));
  const verboseHasLine = /\d+:\d+/.test(lintVerbose.out);
  record({
    id: "rtk-lint-escape-hatch",
    component: "RTK",
    title: "CHALLENGE: lint summary vs lint -v (progressive disclosure)",
    status: summaryOnly && verboseHasLine ? "PASS" : summaryOnly ? "WARN" : "SKIP",
    diagnosis: summaryOnly && verboseHasLine
      ? "Summary hides file:line; rtk lint -v exposes traces — escape hatch exists"
      : summaryOnly
        ? "Summary mode OK but -v did not expose file:line — check rtk lint -v"
        : "Lint output format unexpected or lint skipped",
    fixHint: "Agent: after rtk lint summary, run rtk lint -v (do not repeat bare eslint)",
    metrics: {
      tokensOut: estTokens(lintSummary.out),
      tokensOutVerbose: estTokens(lintVerbose.out),
      quality: verboseHasLine ? "detail via -v" : "no detail path",
      latencyMs: lintSummary.latencyMs,
    },
  });
}

// cat gap
const logCandidates = ["backend/logs/runner_final_test.log", "backend/logs/1.log"]
  .map((p) => join(REPO, p))
  .filter(existsSync);
if (logCandidates.length) {
  const rel = logCandidates[0].replace(REPO + "/", "");
  const catRaw = runShell(["cat", rel]);
  const catRtk = runShell(["cat", rel], { useRtk: true });
  const rtkCompressesCat = estTokens(catRtk.out) < estTokens(catRaw.out) * 0.9;
  record({
    id: "rtk-cat-passthrough",
    component: "RTK",
    title: "CHALLENGE: cat huge log — RTK must NOT compress (Headroom lane)",
    status: !rtkCompressesCat ? "PASS" : "FAIL",
    diagnosis: !rtkCompressesCat
      ? "RTK passthrough on cat — correct (use headroom_read / headroom_compress)"
      : "RTK compressed cat — wrong lane assignment",
    fixHint: "Use headroom_read instead of cat for large logs",
    metrics: {
      tokensIn: estTokens(catRaw.out),
      tokensOut: estTokens(catRtk.out),
      savingsPct: Math.round((100 * (estTokens(catRaw.out) - estTokens(catRtk.out))) / estTokens(catRaw.out)),
    },
  });
}

// ─── HEADROOM CHALLENGES ─────────────────────────────────────────────────────
console.log("## Phase 3 — Headroom lane (compress + retrieve + guard)\n");

await withHeadroom(async (client, connectMs) => {
  record({
    id: "headroom-mcp-connect",
    component: "Headroom",
    title: "MCP stdio connect latency",
    status: connectMs < 8000 ? "PASS" : "WARN",
    diagnosis: connectMs < 8000 ? "ok" : `Slow MCP startup (${connectMs}ms) — bottleneck at headroom-mcp-serve.sh`,
    fixHint: connectMs >= 8000 ? "Check pipx venv cold start; warm MCP via Cursor Reload" : "",
    metrics: { latencyMs: connectMs },
  });

  // Guard bypass
  const marked = `${gitRtk.out}\n${MARKER}`;
  const bypass = await headroomCompress(client, marked, {
    retrieveQuery: "install",
    qualityPattern: /install\.sh/,
  });
  record({
    id: "guard-rtk-marker-bypass",
    component: "Guard",
    title: "CHALLENGE: RTK marker forces Headroom bypass (no double-compress)",
    status: bypass.bypassed ? "PASS" : "FAIL",
    diagnosis: bypass.bypassed
      ? "Hard bypass active — tokens unchanged"
      : "Marker present but compress ran — headroom_mcp_guard broken",
    fixHint: "Verify headroom-mcp-serve.sh execs headroom_mcp_guard.py with pipx python",
    metrics: {
      tokensIn: bypass.tokensBefore,
      tokensOut: bypass.tokensAfter,
      savingsPct: 0,
      quality: bypass.bypassed ? "bypass OK" : "compress ran",
    },
  });

  const noMarker = await headroomCompress(client, "plain blob without marker\nline two", {
    qualityPattern: /line two/,
  });
  const falseBypass = noMarker.bypassed || (noMarker.transforms || []).includes("thinkingSOC:rtk-lane-bypass");
  record({
    id: "guard-no-false-bypass",
    component: "Guard",
    title: "Content without marker must NOT bypass",
    status: !falseBypass ? "PASS" : "FAIL",
    diagnosis: !falseBypass ? "ok" : "False bypass on unmarked content",
    fixHint: "Check compression_lanes.content_has_rtk_lane_marker",
    metrics: { quality: falseBypass ? "false bypass" : "compress ran" },
  });

  // Double compress penalty
  const dbl = await headroomCompress(client, gitRtk.out, {
    retrieveQuery: "install",
    qualityPattern: /install\.sh/,
  });
  const inflated = dbl.tokensAfter > estTokens(gitRtk.out) * 1.05;
  record({
    id: "anti-double-compress",
    component: "Guard",
    title: "CHALLENGE: Headroom on RTK git (unmarked) — should warn anti-pattern",
    status: inflated || dbl.tokensAfter >= estTokens(gitRtk.out) ? "PASS" : "WARN",
    diagnosis: inflated
      ? `Double-compress inflated tokens (+${dbl.tokensAfter - estTokens(gitRtk.out)}) — use marker bypass instead`
      : "Unexpected token reduction on RTK shell output",
    fixHint: "Always rely on RTK marker bypass; never headroom_compress Shell output",
    metrics: {
      tokensIn: estTokens(gitRtk.out),
      tokensOut: dbl.tokensAfter,
      latencyMs: dbl.latencyMs,
    },
  });

  // Deadlock needle in noisy log
  const needle = `2026-06-27T12:00:00 ERROR db-pool FATAL: Deadlock found when trying to get lock; Redis timeout after 30000ms trace_id=stress-${Date.now()}`;
  const noisyLog = synthNoisyLog(needle);
  const logCompress = await headroomCompress(client, noisyLog, {
    retrieveQuery: "Deadlock",
    qualityPattern: /Deadlock found when trying to get lock/,
  });
  record({
    id: "headroom-deadlock-needle",
    component: "Headroom",
    title: "CHALLENGE: rare Deadlock line in 8K-line noisy log",
    status: logCompress.qualityOk ? "PASS" : logCompress.retrieveOk ? "WARN" : "FAIL",
    severity: logCompress.qualityOk ? "low" : "high",
    diagnosis: logCompress.signalInCompressed
      ? "Needle kept in compressed output"
      : logCompress.retrieveOk
        ? "Needle lost in compress but recoverable via headroom_retrieve(query=Deadlock) — use retrieve or v2 intent protect"
        : "SIGNAL LOST — Deadlock line gone from compress AND retrieve (reliability bug)",
    fixHint: logCompress.falsePositiveRisk
      ? "v2: focus_keywords on headroom_compress; always retrieve with query after compress"
      : "",
    metrics: {
      tokensIn: logCompress.tokensBefore,
      tokensOut: logCompress.tokensAfter,
      savingsPct: logCompress.savingsPct,
      quality: logCompress.signalInCompressed
        ? "needle in compress"
        : logCompress.retrieveOk
          ? "retrieve recovers"
          : "LOST",
      latencyMs: logCompress.latencyMs,
    },
  });

  // Real log file
  if (logCandidates.length) {
    const logContent = readFileSync(logCandidates[0], "utf8").slice(0, 400000);
    const realLog = await headroomCompress(client, logContent, {
      retrieveQuery: "ERROR",
      qualityPattern: /ERROR|WARN|trace_id/i,
    });
    record({
      id: "headroom-real-log",
      component: "Headroom",
      title: "Real runner log compress + quality",
      status: realLog.qualityOk ? "PASS" : "FAIL",
      diagnosis: realLog.qualityOk ? "ok" : "Log signal lost without retrieve recovery",
      metrics: {
        tokensIn: realLog.tokensBefore,
        tokensOut: realLog.tokensAfter,
        savingsPct: realLog.savingsPct,
        quality: realLog.signalInCompressed ? "in compress" : realLog.retrieveOk ? "via retrieve" : "LOST",
        latencyMs: realLog.latencyMs,
      },
    });

    const tRead = performance.now();
    try {
      const readRes = await client.callTool({
        name: "headroom_read",
        arguments: { file_path: logCandidates[0], fresh: true },
      });
      const readMs = Math.round(performance.now() - tRead);
      const readData = parseToolJson(readRes);
      record({
        id: "headroom-read-disk",
        component: "Headroom",
        title: "headroom_read disk-first (no terminal cat)",
        status: !readRes.isError ? "PASS" : "FAIL",
        diagnosis: !readRes.isError ? "ok" : "headroom_read failed — HEADROOM_MCP_READ=on?",
        fixHint: "source ai-toolstack/config/headroom-env.sh; reload MCP",
        metrics: {
          tokensOut: estTokens(JSON.stringify(readData)),
          latencyMs: readMs,
        },
      });
    } catch (e) {
      record({
        id: "headroom-read-disk",
        component: "Headroom",
        title: "headroom_read disk-first",
        status: "FAIL",
        diagnosis: String(e.message),
        fixHint: "pipx upgrade headroom-ai[mcp]; HEADROOM_MCP_READ=on",
      });
    }
  }

  // Large grep blob — token budget challenge (scoped in --quick mode)
  const grepArgs = QUICK
    ? [
        "-n",
        "--no-heading",
        "def ",
        "backend/services/soc_analyst_service/",
        "-g",
        "*.py",
        "-g",
        "!**/.venv/**",
        "--max-count",
        "200",
      ]
    : [
        "-n",
        "--no-heading",
        "def |class |import ",
        "backend/services/",
        "-g",
        "*.py",
        "-g",
        "!**/.venv/**",
      ];
  let grepBlob = "";
  try {
    grepBlob = execFileSync("rg", grepArgs, {
      cwd: REPO,
      encoding: "utf8",
      maxBuffer: 15 * 1024 * 1024,
    });
  } catch (e) {
    record({
      id: "headroom-grep-budget",
      component: "Headroom",
      title: "CHALLENGE: large backend rg dump — token budget + signal",
      status: "SKIP",
      diagnosis: `rg failed: ${e.message?.slice(0, 120)}`,
      fixHint: "Check backend/services paths exist",
    });
    report._headroomConnectMs = connectMs;
    return;
  }
  const grepHr = await headroomCompress(client, grepBlob, {
    retrieveQuery: "kpi_service",
    qualityPattern: /kpi_service|soc_analyst/,
  });
  const grepBudgetBad = grepHr.tokensAfter > 8000 && !grepHr.qualityOk;
  const grepNoCompress = grepHr.tokensAfter > 10000 && grepHr.savingsPct < 5;
  record({
    id: "headroom-grep-budget",
    component: "Headroom",
    title: "CHALLENGE: large backend rg dump — token budget + signal",
    status: grepBudgetBad ? "WARN" : grepNoCompress ? "WARN" : grepHr.qualityOk ? "PASS" : "WARN",
    severity: grepNoCompress ? "high" : "medium",
    diagnosis: grepNoCompress
      ? `Headroom did NOT compress dense code grep (${grepHr.tokensAfter.toLocaleString()} tok unchanged) — bottleneck: router:noop on rg dumps`
      : grepBudgetBad
        ? `Compressed output still large (${grepHr.tokensAfter} tok) with signal risk`
        : grepHr.qualityOk
          ? "ok"
          : "Needle lost — use headroom_retrieve with specific query",
    fixHint: grepNoCompress
      ? "Narrow rg before compress; split by service dir; avoid raw repo-wide rg dumps"
      : "Narrow rg scope before compress; or retrieve with module name query",
    metrics: {
      tokensIn: grepHr.tokensBefore,
      tokensOut: grepHr.tokensAfter,
      savingsPct: grepHr.savingsPct,
      quality: grepHr.qualityOk ? "OK" : "RISK",
      latencyMs: grepHr.latencyMs,
    },
  });

  report._headroomConnectMs = connectMs;
});

// ─── SUMMARY ─────────────────────────────────────────────────────────────────
const counts = { PASS: 0, WARN: 0, FAIL: 0, SKIP: 0 };
for (const c of report.cases) counts[c.status] = (counts[c.status] ?? 0) + 1;

const byComponent = {};
for (const c of report.cases) {
  if (!byComponent[c.component]) byComponent[c.component] = { pass: 0, warn: 0, fail: 0 };
  byComponent[c.component][c.status === "PASS" ? "pass" : c.status === "WARN" ? "warn" : c.status === "FAIL" ? "fail" : "skip"] =
    (byComponent[c.component][c.status === "PASS" ? "pass" : c.status === "WARN" ? "warn" : c.status === "FAIL" ? "fail" : "skip"] ?? 0) + 1;
}

const slowest = [...report.cases]
  .filter((c) => c.metrics?.latencyMs != null)
  .sort((a, b) => (b.metrics.latencyMs ?? 0) - (a.metrics.latencyMs ?? 0))
  .slice(0, 5);

const tokenHeavy = [...report.cases]
  .filter((c) => (c.metrics?.tokensOut ?? 0) > 5000 || (c.metrics?.tokensIn ?? 0) > 50000)
  .sort((a, b) => (b.metrics?.tokensOut ?? 0) - (a.metrics?.tokensOut ?? 0))
  .slice(0, 5);

report.summary = {
  total: report.cases.length,
  counts,
  health:
    counts.FAIL === 0 && counts.WARN <= 2
      ? "GREEN"
      : counts.FAIL === 0 && counts.WARN <= 4
        ? "YELLOW"
        : counts.FAIL === 0
          ? "YELLOW"
          : "RED",
  byComponent,
  slowestOps: slowest.map((c) => ({ id: c.id, component: c.component, latencyMs: c.metrics.latencyMs })),
  tokenHeavyOps: tokenHeavy.map((c) => ({
    id: c.id,
    component: c.component,
    tokensIn: c.metrics.tokensIn,
    tokensOut: c.metrics.tokensOut,
  })),
  bottleneckCount: report.bottlenecks.length,
};

console.log("=".repeat(78));
console.log("RESULTS BY CASE");
console.log("=".repeat(78));
for (const c of report.cases) printCase(c);

console.log("=".repeat(78));
console.log("BOTTLENECK MAP (FAIL + WARN)");
console.log("=".repeat(78));
if (report.bottlenecks.length === 0) {
  console.log("  No bottlenecks detected.\n");
} else {
  const order = { high: 0, medium: 1, low: 2 };
  report.bottlenecks.sort((a, b) => (order[a.severity] ?? 9) - (order[b.severity] ?? 9));
  for (const b of report.bottlenecks) {
    console.log(`  [${b.severity}] ${b.component}/${b.id}`);
    console.log(`    issue: ${b.issue}`);
    if (b.fix) console.log(`    fix:   ${b.fix}`);
  }
  console.log("");
}

console.log("=".repeat(78));
console.log("EXECUTIVE SUMMARY");
console.log("=".repeat(78));
console.log(`  Health:     ${report.summary.health}`);
console.log(`  Cases:      ${counts.PASS} pass | ${counts.WARN} warn | ${counts.FAIL} fail | ${counts.SKIP} skip`);
console.log(`  Components: ${Object.entries(byComponent).map(([k, v]) => `${k}(${v.pass}/${v.pass + v.warn + v.fail})`).join(", ")}`);
console.log("");
console.log("  Slowest operations:");
for (const s of report.summary.slowestOps) {
  console.log(`    ${s.latencyMs}ms — ${s.component}/${s.id}`);
}
console.log("");
console.log("  Highest token outputs (>5K out or >50K in):");
for (const t of report.summary.tokenHeavyOps) {
  console.log(`    ${t.id}: ${(t.tokensIn ?? "?").toLocaleString?.() ?? t.tokensIn} → ${(t.tokensOut ?? "?").toLocaleString?.() ?? t.tokensOut} tok`);
}
console.log("");
console.log(`  Full JSON: ${REPORT_PATH}`);
console.log("=".repeat(78));

writeFileSync(REPORT_PATH, JSON.stringify(report, null, 2));

process.exit(counts.FAIL > 0 ? 1 : 0);
