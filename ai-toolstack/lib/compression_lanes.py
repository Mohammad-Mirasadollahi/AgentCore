"""ThinkingSOC compression lane constants and helpers (RTK + Headroom)."""

from __future__ import annotations

import json
from typing import Any

# Appended to RTK Shell lane output by hooks/rtk-cursor-hook.sh (single line, ~8 tokens).
RTK_LANE_MARKER = "<!-- thinkingSOC:rtk-lane -->"


def content_has_rtk_lane_marker(content: str) -> bool:
    return RTK_LANE_MARKER in (content or "")


def rtk_lane_bypass_result(content: str) -> dict[str, Any]:
    """Passthrough payload for headroom_compress when RTK lane marker is present."""
    raw = content or ""
    tokens = max(1, (len(raw.encode("utf-8")) + 3) // 4)
    return {
        "compressed": raw,
        "original_tokens": tokens,
        "compressed_tokens": tokens,
        "tokens_saved": 0,
        "savings_percent": 0,
        "bypassed": True,
        "bypass_reason": "rtk_lane_marker",
        "transforms": ["thinkingSOC:rtk-lane-bypass"],
        "note": "Shell output already filtered by RTK; Headroom compress skipped.",
    }


def wrap_rtk_shell_command(command: str, marker: str = RTK_LANE_MARKER) -> str:
    """Wrap a Shell command for RTK filtering + lane marker (hook preToolUse)."""
    cmd = (command or "").strip()
    if not cmd:
        return cmd
    if marker in cmd:
        return cmd
    if cmd.startswith("rtk "):
        base = cmd
    else:
        base = f"rtk {cmd}"
    # Marker on its own line — detected by Headroom guard, negligible token cost.
    return f"{base}; printf '%s\\n' '{marker}'"
