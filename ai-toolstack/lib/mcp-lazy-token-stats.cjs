/**
 * Append MCP / toolstack token events to JSONL (stderr-safe; no stdout).
 * Loaded via NODE_OPTIONS from mcp-lazy-serve.sh or patch require.
 */
"use strict";

const fs = require("fs");
const path = require("path");

const PROXY_SCHEMA_TOKENS = 75;
const FULL_MCP_SCHEMA_TOKENS = 13300;

function statsDir() {
  return (
    process.env.AI_TOOLSTACK_TOKEN_STATS_DIR ||
    path.join(process.cwd(), "ai-toolstack", "data", "token-stats")
  );
}

function eventsFile() {
  return path.join(statsDir(), "events.jsonl");
}

function estimateTokens(byteLen) {
  return Math.max(0, Math.round((byteLen || 0) / 4));
}

function appendEvent(event) {
  const dir = statsDir();
  try {
    fs.mkdirSync(dir, { recursive: true });
    const row = {
      ts: new Date().toISOString(),
      ...event,
    };
    fs.appendFileSync(eventsFile(), JSON.stringify(row) + "\n");
  } catch {
    /* never break MCP */
  }
}

function logSessionSchemaSavings(toolCount) {
  const saved = Math.max(0, FULL_MCP_SCHEMA_TOKENS - PROXY_SCHEMA_TOKENS);
  appendEvent({
    component: "mcp-lazy",
    event: "session_schema_proxy",
    tokens_in: FULL_MCP_SCHEMA_TOKENS,
    tokens_out: PROXY_SCHEMA_TOKENS,
    tokens_saved: saved,
    meta: { tool_count: toolCount || 0, note: "cached tools via mcp-lazy proxy vs direct registration" },
  });
}

function logSearch(query, limit, payloadText) {
  const inBytes = Buffer.byteLength(String(query || ""), "utf8");
  const bytes = Buffer.byteLength(payloadText || "", "utf8");
  appendEvent({
    component: "mcp-lazy",
    event: "mcp_search_tools",
    tokens_in: estimateTokens(inBytes),
    tokens_out: estimateTokens(bytes),
    tokens_saved: 0,
    meta: { query, limit, bytes, in_bytes: inBytes },
  });
}

function logExecute(serverName, toolName, payloadText, isError, args) {
  const inBytes = Buffer.byteLength(
    JSON.stringify({
      server_name: serverName,
      tool_name: toolName,
      arguments: args || {},
    }),
    "utf8"
  );
  const bytes = Buffer.byteLength(payloadText || "", "utf8");
  const tokensIn = estimateTokens(inBytes);
  const tokensOut = estimateTokens(bytes);
  const component =
    serverName === "headroom"
      ? "headroom"
      : serverName === "memory"
        ? "memory"
        : "mcp-lazy";
  let tokensSaved = 0;
  appendEvent({
    component,
    event: "mcp_execute_tool",
    tokens_in: tokensIn,
    tokens_out: tokensOut,
    tokens_saved: tokensSaved,
    meta: {
      server_name: serverName,
      tool_name: toolName,
      bytes,
      in_bytes: inBytes,
      is_error: !!isError,
    },
  });
}

module.exports = {
  appendEvent,
  estimateTokens,
  logSessionSchemaSavings,
  logSearch,
  logExecute,
  FULL_MCP_SCHEMA_TOKENS,
  PROXY_SCHEMA_TOKENS,
};
