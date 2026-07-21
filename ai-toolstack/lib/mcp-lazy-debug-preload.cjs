"use strict";
/**
 * Node preload: intercept child_process.spawn for mcp-lazy backend debugging.
 * Activated via NODE_OPTIONS=--require .../mcp-lazy-debug-preload.cjs
 * Logs to stderr (Cursor MCP output panel) and MCP_LAZY_LOG_DIR/spawn.log
 */
const cp = require("child_process");
const fs = require("fs");
const path = require("path");

const VERBOSE =
  process.env.MCP_LAZY_VERBOSE === "1" ||
  process.env.MCP_LAZY_DEBUG === "1" ||
  process.env.MCP_LAZY_DEBUG === "verbose";

if (!VERBOSE) {
  module.exports = {};
} else {
  const logDir = process.env.MCP_LAZY_LOG_DIR || "";
  const spawnLog = logDir ? path.join(logDir, "spawn.log") : "";

  function debugLog(msg) {
    const line = `[${new Date().toISOString()}] [spawn-intercept pid=${process.pid}] ${msg}`;
    process.stderr.write(`${line}\n`);
    if (spawnLog) {
      try {
        fs.appendFileSync(spawnLog, `${line}\n`);
      } catch {
        /* ignore log write failures */
      }
    }
  }

  debugLog("preload active");

  function summarizeEnv(env) {
    if (!env || typeof env !== "object") return "{}";
    const keys = Object.keys(env).filter(
      (k) =>
        k.startsWith("MCP_") ||
        k.startsWith("MEMORY_") ||
        k.startsWith("HEADROOM_") ||
        k.startsWith("AI_TOOLSTACK_") ||
        k === "PATH" ||
        k === "HOME" ||
        k === "PWD"
    );
    const out = {};
    for (const k of keys.sort()) {
      out[k] =
        k === "PATH"
          ? `(len=${String(env[k] || "").length})`
          : String(env[k]).slice(0, 200);
    }
    return JSON.stringify(out);
  }

  function wrapSpawn(name, original) {
    return function patchedSpawn(command, args, options) {
      const cmd = String(command);
      const argv = Array.isArray(args) ? args : [];
      const opts = args && !Array.isArray(args) ? args : options || {};
      const cwd = opts.cwd || process.cwd();
      debugLog(
        `${name}: cmd=${cmd} args=${JSON.stringify(argv)} cwd=${cwd} env=${summarizeEnv(opts.env)}`
      );
      const child = original.apply(this, arguments);
      if (child && typeof child.on === "function") {
        child.on("error", (err) => {
          debugLog(`${name} error: pid=${child.pid} ${err.message}`);
        });
        child.on("spawn", () => {
          debugLog(`${name} spawned: pid=${child.pid}`);
        });
        child.on("exit", (code, signal) => {
          debugLog(
            `${name} exit: pid=${child.pid} code=${code} signal=${signal || "none"}`
          );
        });
        // Do NOT attach stdout/stderr listeners — they consume MCP JSON-RPC frames
        // and cause deadlocks between mcp-lazy and backends.
      }
      return child;
    };
  }

  cp.spawn = wrapSpawn("spawn", cp.spawn);
  cp.spawnSync = function patchedSpawnSync(command, args, options) {
    const cmd = String(command);
    const argv = Array.isArray(args) ? args : [];
    debugLog(`spawnSync: cmd=${cmd} args=${JSON.stringify(argv)}`);
    const result = cp.spawnSync.apply(this, arguments);
    if (result.error) {
      debugLog(`spawnSync error: ${result.error.message}`);
    } else {
      debugLog(
        `spawnSync done: status=${result.status} signal=${result.signal || "none"}`
      );
    }
    return result;
  };

  process.on("uncaughtException", (err) => {
    debugLog(`uncaughtException: ${err.stack || err.message}`);
  });
  process.on("unhandledRejection", (reason) => {
    debugLog(`unhandledRejection: ${reason}`);
  });
}
