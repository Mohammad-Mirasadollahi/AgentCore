# MCP Lazy — Debug, Reliability, and Custom Backends

Complete guide for diagnosing mcp-lazy hangs, reading verbose logs in Cursor, and registering custom/personal MCP servers behind the proxy.

**Related docs:** [token-optimization-overview.md](./token-optimization-overview.md) · [headroom-integration.md](./headroom-integration.md)

**Stack:** mcp-lazy backends are **memory** and **headroom** only (former Graphify/CRG MCP removed).

---

## Table of contents

1. [Problems solved](#problems-solved)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Install integration](#install-integration)
5. [Log locations](#log-locations)
6. [Reading logs in Cursor](#reading-logs-in-cursor)
7. [Environment variables](#environment-variables)
8. [Diagnostic workflow](#diagnostic-workflow)
9. [Adding a custom MCP backend](#adding-a-custom-mcp-backend)
10. [Log message reference](#log-message-reference)
11. [Common hang causes](#common-hang-causes)
12. [Troubleshooting](#troubleshooting)
13. [Disabling verbose mode](#disabling-verbose-mode)

---

## Problems solved

| Symptom | Root cause | Fix |
|---------|------------|-----|
| **Cursor hangs 5–60s on MCP start** | `mcp-lazy serve` blocked on full tool discovery when cache fingerprint mismatched | **Stale-cache fast path** — use existing cache instantly, refresh in background |
| **Cursor hangs / MCP deadlock** | Debug preload attached `stdout` listeners and **stole JSON-RPC frames** from backends | Preload logs spawn/exit only — **never** read child stdout/stderr |
| Cursor freezes when MCP starts | Stale `tool-cache.json` → blocking discovery | `./ai-toolstack/install.sh` + `mcp-lazy init`; sessionStart hook refreshes cache |
| `spawn npx ENOENT` in MCP panel | Cursor spawn PATH omits nvm/fnm | `bin/mcp-lazy-serve.sh` + `lib/resolve-node.sh` |
| Memory missing (40 tools not 49) | Nested `npx -y` exceeds mcp-lazy 30s connect timeout | Local install under `data/local/node_modules/` |
| Custom MCP hangs entire IDE | Backend never completes MCP initialize or pollutes stdout | Use `mcp-custom-serve.sh` + `mcp-backend-probe.mjs`; see [custom backends](#adding-a-custom-mcp-backend) |
| Cannot tell Cursor vs backend fault | No visibility into spawn/connect timing | Verbose debug patch + spawn intercept (this doc) |
| mcp-lazy itself slow on every Cursor start | `npx -y mcp-lazy` on each spawn | Local `mcp-lazy@0.1.7` installed by `install.sh` |

---

## Architecture

```
Cursor ~/.cursor/mcp.json          ← single entry: mcp-lazy only
  └── bin/mcp-lazy-serve.sh        (absolute path; logs startup + enables preload)
        └── data/local/node_modules/.bin/mcp-lazy serve   (local binary, patched)
              ├── lib/mcp-lazy-debug-preload.cjs   (spawn intercept → spawn.log)
              ├── memory                           (local mcp-server-memory binary)
              ├── headroom                         (bin/headroom-mcp-serve.sh via servers.json)
              └── [your custom backend]            (via mcp-custom-serve.sh optional)

Headroom is NOT a second row in ~/.cursor/mcp.json — only in mcp-lazy-servers.json.
```

### Logging layers

| Layer | Source | Output | Purpose |
|-------|--------|--------|---------|
| **Wrapper** | `mcp-lazy-serve.sh` | stderr + `session-*.log` | PID, env, servers.json, cache state |
| **Spawn intercept** | `mcp-lazy-debug-preload.cjs` | stderr + `spawn.log` | Every `child_process.spawn` with cmd/args/cwd |
| **In-process** | Patched `mcp-lazy/dist/index.js` | stderr (`[mcp-lazy DEBUG …]`) | discovery, loader, search, execute phases |
| **Custom backend** | `mcp-custom-serve.sh` | stderr + `backends/*.log` | Personal MCP startup only |

**Important:** MCP uses **stdio JSON-RPC**. Only **stderr** is safe for debug output. Never `print()` / `console.log()` diagnostics to stdout in a backend — it breaks the protocol and causes deadlocks.

---

## Components

| File | Role |
|------|------|
| `bin/mcp-lazy-serve.sh` | Cursor MCP entry; enables verbose logging and local binary |
| `bin/headroom-mcp-serve.sh` | Headroom backend spawn (used by mcp-lazy via `servers.json`, not a separate Cursor MCP entry) |
| `lib/mcp-lazy-debug.sh` | Shared log helpers, env defaults, binary resolution |
| `lib/mcp-lazy-debug-preload.cjs` | Node `--require` hook; intercepts spawns |
| `scripts/patch-mcp-lazy-debug.py` | Idempotent patch of local `mcp-lazy/dist/index.js` |
| `scripts/patch-mcp-lazy-execute-aliases.py` | Accept `server`/`tool` aliases and flat backend args on `mcp_execute_tool` |
| `scripts/mcp-lazy-diagnose.sh` | Full diagnostic (per-backend probe + doctor + init) |
| `scripts/mcp-backend-probe.mjs` | Single-backend MCP handshake test (SDK transport) |
| `bin/mcp-custom-serve.sh` | Verbose wrapper for custom/personal MCP servers |
| `data/mcp-lazy/logs/` | Runtime log directory (gitignored) |

---

## Install integration

`install.sh` runs (among other steps):

1. `ensure_memory_server` — local `@modelcontextprotocol/server-memory`
2. **`ensure_mcp_lazy_server`** — local `mcp-lazy@0.1.7` + debug patch
3. `ensure_headroom_server` — pipx `headroom-ai[mcp]` when missing
4. `ensure_mcp_lazy_cache` — `mcp-lazy init` with verbose env
5. Template render → `data/local/mcp.json` (**mcp-lazy** only) and `data/local/mcp-lazy-servers.json` (**memory**, **headroom**)
6. Symlink `~/.cursor/mcp.json` and `~/.mcp-lazy/servers.json`

Re-apply after upgrading mcp-lazy or changing patch anchors:

```bash
./ai-toolstack/install.sh
# or patch only:
python3 ai-toolstack/scripts/patch-mcp-lazy-debug.py \
  ai-toolstack/data/local/node_modules/mcp-lazy/dist/index.js
```

---

## Log locations

All under `ai-toolstack/data/mcp-lazy/logs/` (gitignored):

| File | When written | Contents |
|------|--------------|----------|
| `session-YYYYMMDD-HHMMSS-PID.log` | Each `mcp-lazy-serve.sh` invocation | Startup env, servers.json summary, cache status |
| `spawn.log` | When preload active | All backend spawns: command, args, cwd, exit code |
| `diagnose-YYYYMMDD-HHMMSS.log` | `mcp-lazy-diagnose.sh` | Full diagnostic run |
| `backends/<name>-*.log` | Custom MCP via `mcp-custom-serve.sh` | Backend-specific startup |

---

## Reading logs in Cursor

1. Open **Cursor Settings → MCP**
2. Select **mcp-lazy** (or `user-mcp-lazy`)
3. Click **View Logs** / output panel

Look for:

```
[mcp-lazy DEBUG 2026-…][serve] runServe start {"pid":…}
[mcp-lazy DEBUG …][serve] cache hit {"toolCount":49,"elapsedMs":12}
[mcp-lazy DEBUG …][loader] attemptConnect start {"serverName":"my-custom-mcp",…}
```

If logs stop at `attemptConnect start` with no `attemptConnect ok`, that backend is hanging during MCP initialize (30s timeout × 2 retry inside mcp-lazy).

Also check on disk:

```bash
ls -lt ai-toolstack/data/mcp-lazy/logs/
tail -f ai-toolstack/data/mcp-lazy/logs/spawn.log
```

---

## Environment variables

| Variable | Default | Effect |
|----------|---------|--------|
| `MCP_LAZY_VERBOSE` | `0` (off in production) | Enables `[mcp-lazy DEBUG …]` when set to `1` |
| `MCP_LAZY_DEBUG` | `0` | Alias gate for debug helper + spawn intercept |
| `MCP_LAZY_LOG_DIR` | `ai-toolstack/data/mcp-lazy/logs` | Directory for session/spawn/diagnose logs |
| `MCP_LAZY_SESSION_LOG` | auto per PID | Override session log file path |
| `MCP_PROBE_TIMEOUT_MS` | `45000` | Per-backend probe timeout in diagnose script |
| `MCP_LOCAL_NODE_MODULES` | `data/local/node_modules` | SDK resolution for `mcp-backend-probe.mjs` |
| `MCP_CUSTOM_NAME` | basename of command | Log prefix for `mcp-custom-serve.sh` |

Set `MCP_LAZY_VERBOSE=0` to disable in-process debug (see [Disabling verbose mode](#disabling-verbose-mode)).

---

## Diagnostic workflow

### Full diagnose (recommended)

```bash
./ai-toolstack/scripts/mcp-lazy-diagnose.sh
```

Phases:

| Phase | What it does |
|-------|--------------|
| 1 | Per-backend MCP probe (`mcp-backend-probe.mjs`) — same transport as mcp-lazy |
| 2 | `mcp-lazy doctor` |
| 3 | `mcp-lazy init` (parallel discovery — reproduces cache-miss serve path) |
| 4 | Cache vs `servers.json` freshness check |

Quick mode (skip per-backend probes):

```bash
./ai-toolstack/scripts/mcp-lazy-diagnose.sh --quick
```

### Probe a single backend

```bash
MCP_LOCAL_NODE_MODULES=/opt/ThinkingSOC/ai-toolstack/data/local/node_modules \
node ai-toolstack/scripts/mcp-backend-probe.mjs \
  '{"command":"/path/to/server","args":["serve"],"env":{},"cwd":"/path/to/project"}' \
  my-server-name
```

Expected: `OK my-server-name: N tools in XXXms`

Timeout (`124`): backend never completes MCP handshake — primary hang indicator.

### Cache freshness

mcp-lazy `serve` loads tools from `~/.mcp-lazy/tool-cache.json` when the **fingerprint** matches `servers.json`. If you add/change a backend without re-running `init`, the next Cursor MCP start runs **full parallel discovery** (slow; feels like a hang).

```bash
# Check mtimes
ls -la ~/.mcp-lazy/tool-cache.json ~/.mcp-lazy/servers.json

# Rebuild cache
./ai-toolstack/install.sh
# or:
ai-toolstack/data/local/node_modules/.bin/mcp-lazy init
```

---

## Adding a custom MCP backend

### Option A — Direct entry in `servers.json`

Edit the generated file (or extend the template and re-run `install.sh`):

**File:** `ai-toolstack/data/local/mcp-lazy-servers.json`  
**Symlink:** `~/.mcp-lazy/servers.json`

```json
{
  "servers": {
    "memory": { "...": "..." },
    "headroom": { "...": "..." },
    "my-custom-mcp": {
      "command": "/opt/ThinkingSOC/ai-toolstack/bin/mcp-custom-serve.sh",
      "args": ["/path/to/your/mcp/entry", "serve"],
      "cwd": "/path/to/project",
      "env": {
        "MY_API_KEY": "from-env-or-secret-store"
      }
    }
  }
}
```

Then:

```bash
ai-toolstack/data/local/node_modules/.bin/mcp-lazy init
# Cursor → Reload Window
```

### Option B — Extend the install template

Add your server block to `ai-toolstack/config/mcp-lazy-servers.json.template` using placeholders if paths vary by machine, then:

```bash
./ai-toolstack/install.sh --no-verify
npx mcp-lazy init
```

### Custom backend checklist

- [ ] **Executable** — `command` path is absolute and executable
- [ ] **No nested npx** — install backend locally; use real binary path in `args`
- [ ] **stderr only** — all debug output to stderr, never stdout
- [ ] **Fast initialize** — must respond to MCP `initialize` within ~30s
- [ ] **Probe passes** — `mcp-backend-probe.mjs` returns `OK`
- [ ] **Cache rebuilt** — run `mcp-lazy init` after changing `servers.json`

### Avoid nested `npx`

mcp-lazy hardcodes a **30s connect timeout** per backend (one retry on timeout). Nested `npx -y` at runtime routinely exceeds this — the backend is silently dropped from the cache or blocks discovery.

Pattern used for built-in servers:

| Server | Local binary |
|--------|--------------|
| `memory` | `data/local/node_modules/.bin/mcp-server-memory` |
| `mcp-lazy` (proxy) | `data/local/node_modules/.bin/mcp-lazy` |

Apply the same pattern to custom Node/Python MCP servers.

---

## Log message reference

| Phase tag | Example | Meaning |
|-----------|---------|---------|
| `[serve] runServe start` | Proxy process starting | |
| `[serve] cache hit` | Loaded N tools from cache | Fast path — good |
| `[serve] cache miss — running discovery` | Connecting to all backends at once | Slow path — check cache freshness |
| `[discovery] server start` | Backend name + command | Discovery began for one server |
| `[discovery] connectToServer connected` | Handshake OK | |
| `[discovery] server done` | toolCount + elapsedMs | Success |
| `[discovery] server failed` | error message | Backend rejected or timed out |
| `[loader] loadServer` | Lazy load on first tool call | |
| `[loader] attemptConnect start` | Spawning backend | If hang follows, backend is stuck here |
| `[loader] attemptConnect ok` | Backend ready | |
| `[search] mcp_search_tools` | Agent searched tools | |
| `[execute] mcp_execute_tool` | Agent called a backend tool | |
| `[spawn-intercept …] spawn:` | cmd + args | Low-level spawn audit |

---

## Common hang causes

### 1. Stale or missing tool cache

**Symptom:** Cursor unresponsive 5–60s on first MCP use after adding a server.  
**Log:** `[serve] cache miss — running discovery`  
**Fix:** `mcp-lazy init` then Reload Window.

### 2. Backend initialize timeout

**Symptom:** Hang ~30–60s; one server never completes.  
**Log:** `[loader] attemptConnect start` without `attemptConnect ok`  
**Fix:** Run probe on that server; fix startup (deps, env, blocking I/O).

### 3. stdout pollution

**Symptom:** Random hangs or `JSON parse error` in spawn log.  
**Log:** `spawn stdout[pid]:` shows non-JSON text before MCP frames  
**Fix:** Redirect diagnostics to stderr in your MCP server.

### 4. Nested `npx -y`

**Symptom:** Timeouts on first connect; memory/custom server missing from cache.  
**Fix:** Pre-install backend under `data/local/node_modules/` or use a venv binary.

### 5. `npx -y mcp-lazy` instead of local binary

**Symptom:** Slow MCP server start in Cursor even with warm cache.  
**Log:** `using npx -y mcp-lazy (consider ./ai-toolstack/install.sh for local binary)`  
**Fix:** Run `./ai-toolstack/install.sh`.

---

## Troubleshooting

| Symptom | Action |
|---------|--------|
| MCP red / "Loading tools" forever | `./ai-toolstack/scripts/mcp-lazy-diagnose.sh`; read `session-*.log` and Cursor MCP panel |
| Hang after adding custom MCP | Probe backend: `mcp-backend-probe.mjs`; wrap with `mcp-custom-serve.sh` |
| 40 tools not 49 | Memory timeout — `./ai-toolstack/install.sh`; confirm local `mcp-server-memory` in `servers.json` |
| Debug patch failed on upgrade | Re-run `install.sh` or `patch-mcp-lazy-debug.py`; check mcp-lazy version pin (`0.1.7` in `install.sh`) |
| No `[mcp-lazy DEBUG]` lines | Confirm local patched binary: `grep thinkingSOC data/local/node_modules/mcp-lazy/dist/index.js` |
| `spawn npx ENOENT` | Install Node.js; re-run `./ai-toolstack/install.sh` |

---

## Disabling verbose mode

Verbose logging is on by default in `mcp-lazy-serve.sh` (`MCP_LAZY_VERBOSE=1`).

To disable for production:

1. Edit `ai-toolstack/lib/mcp-lazy-debug.sh`:

   ```bash
   export MCP_LAZY_VERBOSE="${MCP_LAZY_VERBOSE:-0}"
   export MCP_LAZY_DEBUG="${MCP_LAZY_DEBUG:-0}"
   ```

2. Or set before Cursor starts (if your OS supports MCP env config):

   ```bash
   export MCP_LAZY_VERBOSE=0
   export MCP_LAZY_DEBUG=0
   ```

Wrapper session logs and spawn intercept still run when `MCP_LAZY_VERBOSE=0` unless you also skip `mcp_lazy_enable_node_preload` — for minimal overhead, set both vars to `0`.

---

## Version pins

Recorded in `install.sh`:

| Package | Pin | Location |
|---------|-----|----------|
| `mcp-lazy` | `0.1.7` | `data/local/node_modules/mcp-lazy` |
| `@modelcontextprotocol/server-memory` | `2026.1.26` | `data/local/node_modules/.bin/mcp-server-memory` |

Verify after install:

```bash
grep '"version"' ai-toolstack/data/local/node_modules/mcp-lazy/package.json
./ai-toolstack/scripts/mcp-lazy-diagnose.sh
ai-toolstack/data/local/node_modules/.bin/mcp-lazy doctor
```

---

*Update this document when changing debug scripts, patch anchors, mcp-lazy version pin, or custom-backend workflow.*
