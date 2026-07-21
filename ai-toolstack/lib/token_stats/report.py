"""Aggregate and format token-stats gain report."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


COMPONENT_HELP: dict[str, str] = {
    "rtk": "Shell output compression (Cursor preToolUse hook). Raw command output vs RTK-filtered text.",
    "headroom": "Large blob compression via MCP (JSON, logs, files, RAG). headroom_compress + CCR retrieve.",
    "mcp-lazy": "MCP proxy: tool schemas hidden behind proxy tools per Cursor MCP session; plus search overhead.",
    "memory": "Small cross-session facts vs re-pasting conventions into chat.",
    "ponytail": "Terse user-facing replies (ponytail-fa / ponytail lite) vs verbose prose; afterAgentResponse hook.",
}

DISPLAY_ORDER = ["rtk", "headroom", "mcp-lazy", "memory", "ponytail"]

# Shown in "Used, no save" footer when Calls>0 and Saved=0 (rows stay in main table too).
NO_SAVE_USAGE_NOTE: dict[str, str] = {
    "memory": "Cross-session facts; no per-call save heuristic (small payloads).",
    "mcp-lazy": "Includes mcp_search_tools and proxy overhead rows with Saved=0.",
    "headroom": "Compress/retrieve logged; savings appear when compress runs in range.",
    "rtk": "Shell commands with no measurable shrink vs raw output.",
    "ponytail": "Reply logged; ratio may yield 0 for very short messages.",
}


def effective_tokens_in(row: dict[str, Any]) -> int:
    """Resolve MCP In: logged request size, meta bytes, or Out+Saved baseline."""
    logged = int(row.get("tokens_in") or 0)
    if logged > 0:
        return logged
    meta = row.get("meta")
    if isinstance(meta, dict):
        in_bytes = meta.get("in_bytes")
        if in_bytes is not None:
            return max(0, round(int(in_bytes) / 4))
    tokens_out = int(row.get("tokens_out") or 0)
    tokens_saved = int(row.get("tokens_saved") or 0)
    if tokens_saved > 0:
        return tokens_out + tokens_saved
    if tokens_out > 0:
        return tokens_out
    return 0


@dataclass
class ComponentTotals:
    component: str
    calls: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    tokens_saved: int = 0

    def add(self, row: dict[str, Any]) -> None:
        self.calls += 1
        self.tokens_in += effective_tokens_in(row)
        self.tokens_out += int(row.get("tokens_out") or 0)
        self.tokens_saved += int(row.get("tokens_saved") or 0)


@dataclass
class Report:
    range_label: str
    components: dict[str, ComponentTotals] = field(default_factory=dict)
    rtk: dict[str, Any] = field(default_factory=dict)
    rtk_top: list[dict[str, Any]] = field(default_factory=list)
    headroom: dict[str, Any] = field(default_factory=dict)

    def net_saved(self) -> int:
        total = sum(c.tokens_saved for c in self.components.values())
        total += int(self.rtk.get("tokens_saved") or 0)
        total += int(self.headroom.get("tokens_saved") or 0)
        return total

    def total_input(self) -> int:
        total = sum(c.tokens_in for c in self.components.values())
        total += int(self.rtk.get("tokens_in") or 0)
        total += int(self.headroom.get("tokens_in") or 0)
        return total

    def total_consumed(self) -> int:
        total = sum(c.tokens_out for c in self.components.values())
        total += int(self.rtk.get("tokens_out") or 0)
        total += int(self.headroom.get("tokens_out") or 0)
        return total

    def total_save_pct(self) -> float:
        saved = self.net_saved()
        if saved <= 0:
            return 0.0
        out = self.total_consumed()
        baseline = out + saved
        return min(100.0, 100.0 * saved / baseline) if baseline else 0.0


def aggregate_events(events: list[dict[str, Any]]) -> dict[str, ComponentTotals]:
    out: dict[str, ComponentTotals] = {}
    for row in events:
        comp = str(row.get("component") or "mcp-lazy")
        if comp not in out:
            out[comp] = ComponentTotals(component=comp)
        out[comp].add(row)
    return out


def _fmt_k(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 10_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def save_pct(tokens_in: int, tokens_out: int, tokens_saved: int) -> float:
    """Estimated share of tokens avoided vs raw/heuristic baseline."""
    if tokens_saved <= 0:
        return 0.0
    baseline = tokens_out + tokens_saved
    if tokens_in > 0 and tokens_in >= tokens_saved:
        return min(100.0, 100.0 * tokens_saved / tokens_in)
    if baseline > 0:
        return min(100.0, 100.0 * tokens_saved / baseline)
    return 0.0


def _fmt_pct(pct: float) -> str:
    if pct <= 0:
        return "0.0%"
    return f"{pct:.1f}%"


def component_metrics(report: Report, key: str) -> tuple[int, int, int, int]:
    """Return (calls, tokens_in, tokens_out, tokens_saved) for a canonical component key."""
    if key == "rtk":
        rtk = report.rtk
        return (
            int(rtk.get("calls") or 0),
            int(rtk.get("tokens_in") or 0),
            int(rtk.get("tokens_out") or 0),
            int(rtk.get("tokens_saved") or 0),
        )
    if key == "headroom":
        hr = report.headroom
        return (
            int(hr.get("compressions") or 0),
            int(hr.get("tokens_in") or 0),
            int(hr.get("tokens_out") or 0),
            int(hr.get("tokens_saved") or 0),
        )
    comp = report.components.get(key)
    if comp:
        return comp.calls, comp.tokens_in, comp.tokens_out, comp.tokens_saved
    return 0, 0, 0, 0


def _component_save_pct(report: Report, key: str, tokens_in: int, tokens_out: int, tokens_saved: int) -> float:
    if key == "rtk":
        pct = report.rtk.get("savings_pct")
        if pct is not None:
            return float(pct)
    if key == "headroom":
        pct = report.headroom.get("savings_pct")
        if pct is not None:
            return float(pct)
    return save_pct(tokens_in, tokens_out, tokens_saved)


def all_component_rows(report: Report) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for key in DISPLAY_ORDER:
        calls, tokens_in, tokens_out, tokens_saved = component_metrics(report, key)
        rows[key] = {
            "calls": calls,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "tokens_saved": tokens_saved,
            "save_pct": round(_component_save_pct(report, key, tokens_in, tokens_out, tokens_saved), 2),
            "description": COMPONENT_HELP.get(key, ""),
        }
    for key, comp in report.components.items():
        if key in rows:
            continue
        rows[key] = {
            "calls": comp.calls,
            "tokens_in": comp.tokens_in,
            "tokens_out": comp.tokens_out,
            "tokens_saved": comp.tokens_saved,
            "save_pct": round(save_pct(comp.tokens_in, comp.tokens_out, comp.tokens_saved), 2),
            "description": "(custom)",
        }
    return rows


def active_no_save_components(report: Report) -> list[dict[str, Any]]:
    """Components with usage in range but zero estimated save (still listed in main table)."""
    rows = all_component_rows(report)
    out: list[dict[str, Any]] = []
    for key in DISPLAY_ORDER:
        row = rows[key]
        if int(row["calls"]) <= 0 or int(row["tokens_saved"]) > 0:
            continue
        out.append(
            {
                "component": key,
                "calls": row["calls"],
                "tokens_in": row["tokens_in"],
                "tokens_out": row["tokens_out"],
                "note": NO_SAVE_USAGE_NOTE.get(key, "Used in range; no save heuristic applied."),
            }
        )
    for key in sorted(rows):
        if key in DISPLAY_ORDER:
            continue
        row = rows[key]
        if int(row["calls"]) <= 0 or int(row["tokens_saved"]) > 0:
            continue
        out.append(
            {
                "component": key,
                "calls": row["calls"],
                "tokens_in": row["tokens_in"],
                "tokens_out": row["tokens_out"],
                "note": "(custom component)",
            }
        )
    return out


def format_text(report: Report) -> str:
    lines: list[str] = []
    lines.append("ThinkingSOC Token Stats")
    lines.append("=" * 72)
    lines.append(f"Range: {report.range_label}")
    lines.append("")
    lines.append(
        f"In (est.): {_fmt_k(report.total_input())} tokens  |  "
        f"Out (est.): {_fmt_k(report.total_consumed())} tokens  |  "
        f"Saved (est.): {_fmt_k(report.net_saved())} tokens  |  "
        f"Save: {_fmt_pct(report.total_save_pct())}"
    )
    lines.append("")
    lines.append(
        f"{'Component':<20} {'Calls':>7} {'In':>10} {'Out':>10} {'Saved':>10} {'Save%':>7}  What it means"
    )
    lines.append("-" * 81)

    rows = all_component_rows(report)
    for key in DISPLAY_ORDER:
        row = rows[key]
        lines.append(
            f"{key:<20} {row['calls']:>7} {_fmt_k(row['tokens_in']):>10} "
            f"{_fmt_k(row['tokens_out']):>10} {_fmt_k(row['tokens_saved']):>10} "
            f"{_fmt_pct(row['save_pct']):>7}  {row['description']}"
        )

    for key in sorted(rows):
        if key in DISPLAY_ORDER:
            continue
        row = rows[key]
        lines.append(
            f"{key:<20} {row['calls']:>7} {_fmt_k(row['tokens_in']):>10} "
            f"{_fmt_k(row['tokens_out']):>10} {_fmt_k(row['tokens_saved']):>10} "
            f"{_fmt_pct(row['save_pct']):>7}  {row['description']}"
        )

    no_save = active_no_save_components(report)
    if no_save:
        lines.append("")
        lines.append("Used, no save (still in table above — not hidden)")
        lines.append("-" * 81)
        for item in no_save:
            name = str(item["component"])
            lines.append(
                f"  {name:<20} {int(item['calls']):>5} calls  "
                f"in {_fmt_k(int(item['tokens_in'])):<8} out {_fmt_k(int(item['tokens_out'])):<8}  "
                f"{item['note']}"
            )

    if report.rtk_top:
        lines.append("")
        lines.append("RTK top commands (saved)")
        lines.append("-" * 72)
        for item in report.rtk_top:
            cmd = item["command"]
            if len(cmd) > 42:
                cmd = cmd[:39] + "..."
            lines.append(
                f"  {cmd:<42} x{item['count']:<4} saved {_fmt_k(item['tokens_saved'])} ({item['avg_pct']:.1f}%)"
            )

    lines.append("")
    lines.append("Notes:")
    lines.append(
        "  - In: RTK/Headroom = measured raw input; MCP = request args when logged,"
    )
    lines.append(
        "    else Out+Saved baseline (legacy rows or heuristic savings)."
    )
    lines.append("  - Out: RTK/Headroom compressed output; MCP = response payload (bytes/4).")
    lines.append(
        "  - ponytail: estimated from assistant reply size vs verbose baseline (PONYTAIL_STATS_SAVE_RATIO, default 0.35)."
    )
    lines.append("  - Range: --since 24h | 7d | 2026-06-01 | ISO timestamp  [--until ISO]")
    lines.append("  - RTK only: rtk gain -p  |  Headroom: headroom stats  |  JSON: --format json")
    return "\n".join(lines)


def format_json(report: Report) -> dict[str, Any]:
    return {
        "range": report.range_label,
        "input_tokens_est": report.total_input(),
        "consumed_tokens_est": report.total_consumed(),
        "saved_tokens_est": report.net_saved(),
        "save_pct_est": round(report.total_save_pct(), 2),
        "rtk": report.rtk,
        "rtk_top_commands": report.rtk_top,
        "headroom": report.headroom,
        "components": all_component_rows(report),
        "active_no_save": active_no_save_components(report),
    }
