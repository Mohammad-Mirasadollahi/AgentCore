"""Live token benchmark — fixed context, MCP probes, prompt scenarios."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from bench_probe.token_estimator import chars_to_token_estimate  # noqa: F401 — import edge for bench demos
from cli.paths import ToolstackPaths
from token_stats.events import load_events
from token_stats.report import COMPONENT_HELP, _fmt_k
from token_stats.headroom import query_headroom
from token_stats.time_range import parse_time_range


def estimate_tokens(byte_len: int) -> int:
    return max(0, round(byte_len / 4))


@dataclass
class FixedContext:
    rules_bytes: int = 0
    agents_bytes: int = 0
    cursorrules_bytes: int = 0
    mcp_direct_tokens: int = 0
    mcp_lazy_tokens: int = 0
    mcp_saved_per_turn: int = 0
    tool_count: int = 0

    @property
    def rules_tokens(self) -> int:
        return estimate_tokens(self.rules_bytes)

    @property
    def agents_tokens(self) -> int:
        return estimate_tokens(self.agents_bytes)

    @property
    def fixed_per_turn(self) -> int:
        return self.rules_tokens + self.agents_tokens + self.mcp_lazy_tokens


@dataclass
class PromptScenario:
    name: str
    description: str
    steps: list[dict[str, Any]] = field(default_factory=list)

    @property
    def total_out(self) -> int:
        return sum(int(s.get("tokens_out") or 0) for s in self.steps)

    @property
    def total_saved(self) -> int:
        return sum(int(s.get("tokens_saved") or 0) for s in self.steps)


def measure_fixed_context(paths: ToolstackPaths, probe_data: dict[str, Any]) -> FixedContext:
    always_rules = [
        "ai-toolstack.mdc",
        "ponytail.mdc",
        "mcp-memory.mdc",
        "no-cloud-exfiltration.mdc",
    ]
    rules_bytes = 0
    for name in always_rules:
        p = paths.rules / name
        if p.is_file():
            rules_bytes += p.stat().st_size

    agents = paths.repo / "AGENTS.md"
    cursorrules = paths.repo / ".cursorrules"
    fc = FixedContext(
        rules_bytes=rules_bytes,
        agents_bytes=agents.stat().st_size if agents.is_file() else 0,
        cursorrules_bytes=cursorrules.stat().st_size if cursorrules.is_file() else 0,
    )

    for p in probe_data.get("probes") or []:
        if p.get("id") == "mcp_schema_direct":
            fc.mcp_direct_tokens = int(p.get("tokens") or 0)
            fc.tool_count = int((p.get("meta") or {}).get("tool_count") or 0)
        if p.get("id") == "mcp_schema_lazy":
            fc.mcp_lazy_tokens = int(p.get("tokens") or 0)
            fc.mcp_saved_per_turn = int(p.get("saved_vs_direct") or 0)
    return fc


def _probe_map(probe_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(p["id"]): p for p in (probe_data.get("probes") or []) if p.get("id")}


def build_scenarios(probes: dict[str, dict[str, Any]], fixed: FixedContext) -> list[PromptScenario]:
    def step(label: str, pid: str, *, saved: int = 0, note: str = "") -> dict[str, Any]:
        p = probes.get(pid) or {}
        return {
            "label": label,
            "tokens_out": int(p.get("tokens") or 0),
            "tokens_saved": saved,
            "bytes": int(p.get("bytes") or 0),
            "ms": int(p.get("ms") or 0),
            "ok": p.get("ok", False),
            "note": note,
        }

    mem_q = probes.get("memory_search") or {}
    mem_baseline = 1200
    mem_saved = max(0, mem_baseline - int(mem_q.get("tokens") or 0))

    scenarios = [
        PromptScenario(
            name="A — Doc question (Read / rg)",
            description='User: "Where are settings tabs documented?"',
            steps=[
                step("Fixed context (rules + MCP lazy schemas)", "mcp_schema_lazy",
                     saved=fixed.mcp_saved_per_turn,
                     note="paid every agent turn while MCP enabled"),
                step("mcp_search_tools (memory)", "mcp_search_memory"),
                step("memory search_nodes", "memory_search", saved=mem_saved),
            ],
        ),
        PromptScenario(
            name="B — Backend change (rg + tests)",
            description="Read standards → narrow rg → pytest",
            steps=[
                step("Fixed context", "mcp_schema_lazy", saved=fixed.mcp_saved_per_turn),
                step("Headroom compress (large Read sample)", "headroom_compress_sample",
                     saved=max(0, 4000 - int((probes.get("headroom_compress_sample") or {}).get("tokens") or 0))),
            ],
        ),
    ]
    return scenarios


def measure_rtk_pair(paths: ToolstackPaths) -> dict[str, Any] | None:
    rtk = shutil.which("rtk")
    if not rtk:
        return None
    cwd = str(paths.repo)
    try:
        raw = subprocess.run(
            ["git", "status", "--short"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        raw_bytes = len((raw.stdout or "").encode("utf-8"))
        filt = subprocess.run(
            [rtk, "git", "status", "--short"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        filt_bytes = len((filt.stdout or "").encode("utf-8"))
        return {
            "command": "git status --short",
            "raw_bytes": raw_bytes,
            "rtk_bytes": filt_bytes,
            "raw_tokens": estimate_tokens(raw_bytes),
            "rtk_tokens": estimate_tokens(filt_bytes),
            "saved_tokens": max(0, estimate_tokens(raw_bytes) - estimate_tokens(filt_bytes)),
        }
    except (subprocess.TimeoutExpired, OSError):
        return None


def run_mcp_probes(paths: ToolstackPaths, timeout_s: int = 180) -> dict[str, Any]:
    probe_js = paths.scripts / "token-stats-benchmark-probe.mjs"
    local_nm = paths.local / "node_modules"
    env = {
        **os.environ,
        "REPO_ROOT": str(paths.repo),
        "AI_TOOLSTACK_LOCAL_NODE_MODULES": str(local_nm),
    }
    proc = subprocess.run(
        ["node", str(probe_js)],
        cwd=str(paths.repo),
        capture_output=True,
        text=True,
        timeout=timeout_s,
        env=env,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"benchmark probe failed (exit {proc.returncode}): {(proc.stderr or proc.stdout)[:500]}"
        )
    return json.loads(proc.stdout)


def format_benchmark_text(
    paths: ToolstackPaths,
    fixed: FixedContext,
    probe_data: dict[str, Any],
    scenarios: list[PromptScenario],
    rtk_pair: dict[str, Any] | None,
    actual_report: dict[str, Any] | None,
    real_test_lines: list[str] | None = None,
) -> str:
    lines: list[str] = []
    lines.append("ThinkingSOC Token Benchmark")
    lines.append("=" * 60)
    lines.append(f"Repo: {paths.repo}")
    lines.append("")
    lines.append("How to read this:")
    lines.append("  - OFF = no mcp-lazy in Cursor; ON = mcp-lazy + Headroom MCP backend.")
    lines.append("  - Token estimates: bytes/4 for MCP/Read; Headroom uses measured counts.")
    lines.append("")

    lines.append("1) MCP SCHEMA COST — personal MCP OFF vs mcp-lazy ON (per agent turn)")
    lines.append("-" * 60)
    lines.append(f"  OFF (no personal MCP):           0 tok")
    lines.append(f"  ON  (mcp-lazy, {fixed.tool_count} tools behind proxy):  ~{fixed.mcp_lazy_tokens:,} tok")
    lines.append(f"  If you registered 49 tools direct (not recommended): ~{fixed.mcp_direct_tokens:,} tok")
    lines.append(f"  mcp-lazy saves vs direct registration: ~{fixed.mcp_saved_per_turn:,} tok / turn")
    lines.append("")
    lines.append(f"  Rules + AGENTS.md (same either way): ~{fixed.rules_tokens + fixed.agents_tokens:,} tok / turn")
    lines.append("")

    lines.append("2) LIVE MCP PROBES — measured just now")
    lines.append("-" * 60)
    lines.append(f"  {'ID':<22} {'Out':>8} {'ms':>6}  Label")
    lines.append("  " + "-" * 56)
    for p in probe_data.get("probes") or []:
        if str(p.get("id", "")).startswith("mcp_schema"):
            continue
        ok = "ok" if p.get("ok") else "FAIL"
        lines.append(
            f"  {p.get('id',''):<22} {_fmt_k(int(p.get('tokens') or 0)):>8} "
            f"{int(p.get('ms') or 0):>5}  {p.get('label','')} [{ok}]"
        )
    lines.append("")

    if rtk_pair:
        lines.append("3) RTK SHELL SAMPLE — one command measured now")
        lines.append("-" * 60)
        lines.append(f"  Command: {rtk_pair['command']}")
        lines.append(
            f"  Raw: {_fmt_k(rtk_pair['raw_tokens'])} tok  →  RTK: {_fmt_k(rtk_pair['rtk_tokens'])} tok  "
            f"  SAVE: {_fmt_k(rtk_pair['saved_tokens'])} tok"
        )
        lines.append("")

    sec = 4 if rtk_pair else 3
    lines.append(f"{sec}) PROMPT SCENARIOS — what one workflow costs (tool I/O only)")
    lines.append("-" * 60)
    for sc in scenarios:
        lines.append(f"  {sc.name}")
        lines.append(f"    {sc.description}")
        for i, st in enumerate(sc.steps, 1):
            note = f" — {st['note']}" if st.get("note") else ""
            saved = f"  save ~{_fmt_k(st['tokens_saved'])}" if st.get("tokens_saved") else ""
            lines.append(
                f"    {i}. {st['label']}: ~{st['tokens_out']:,} tok{saved}{note}"
            )
        tool_only = sc.total_out
        with_fixed = tool_only + fixed.fixed_per_turn
        lines.append(f"    → Tool I/O subtotal: ~{tool_only:,} tok")
        lines.append(f"    → + 1 turn fixed context: ~{with_fixed:,} tok (estimate)")
        lines.append("")

    sec += 1
    lines.append(f"{sec}) YOUR RECENT USAGE (Headroom + MCP JSONL, last 24h)")
    lines.append("-" * 60)
    if actual_report:
        lines.append(
            f"  Consumed: ~{_fmt_k(actual_report.get('consumed_tokens_est', 0))}  "
            f"Saved: ~{_fmt_k(actual_report.get('saved_tokens_est', 0))}  "
            f"({actual_report.get('range', '')})"
        )
        for comp, data in (actual_report.get("components") or {}).items():
            if not data.get("calls"):
                continue
            lines.append(
                f"    {comp:<18} calls={data['calls']:<4} out={_fmt_k(data['tokens_out']):>6} "
                f"saved={_fmt_k(data['tokens_saved']):>6}"
            )
        hr = actual_report.get("headroom") or {}
        if hr.get("available") and hr.get("compressions"):
            lines.append(
                f"    {'headroom':<18} compressions={hr['compressions']:<4} out={_fmt_k(hr['tokens_out']):>6} "
                f"saved={_fmt_k(hr['tokens_saved']):>6}  (measured)"
            )
    else:
        lines.append("  (no data — run MCP in Cursor after install.sh to populate JSONL)")
    lines.append("")

    lines.append("Component meanings:")
    for key in ("mcp-lazy", "headroom", "memory"):
        lines.append(f"  • {key}: {COMPONENT_HELP.get(key, '')}")
    lines.append("")
    lines.append("Repeat benchmark:  ./ai-toolstack/scripts/ai-toolstack.sh benchmark")
    lines.append("Live stats:          ./ai-toolstack/scripts/ai-toolstack.sh stats status --since 24h -p")
    lines.append("Headroom detail:     headroom stats  |  ./ai-toolstack/scripts/ai-toolstack.sh stats gain")
    return "\n".join(lines)


def run_benchmark(paths: ToolstackPaths | None = None) -> dict[str, Any]:
    paths = paths or ToolstackPaths.discover()
    probe_data = run_mcp_probes(paths)
    fixed = measure_fixed_context(paths, probe_data)
    scenarios = build_scenarios(_probe_map(probe_data), fixed)
    # Remove anti-pattern scenario — compare ENABLE vs DISABLE only
    scenarios = [s for s in scenarios if "ANTI-PATTERN" not in s.name]

    tr = parse_time_range("24h", None)
    events = load_events(paths.data / "token-stats" / "events.jsonl", tr.start, tr.end)
    from token_stats.report import Report, aggregate_events, format_json

    os.environ.setdefault("HEADROOM_WORKSPACE_DIR", str(paths.data / "headroom"))
    actual_report = format_json(
        Report(
            range_label=tr.label,
            components=aggregate_events(events),
            headroom=query_headroom(tr.start, tr.end),
        )
    )
    actual_report["range"] = tr.label
    text = format_benchmark_text(
        paths, fixed, probe_data, scenarios, None, actual_report, None
    )
    return {
        "text": text,
        "fixed": fixed,
        "probes": probe_data,
        "scenarios": scenarios,
        "actual_24h": actual_report,
    }
