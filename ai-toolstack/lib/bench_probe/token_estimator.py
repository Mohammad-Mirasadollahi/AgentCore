"""Token estimate helper used by benchmark demos."""

from __future__ import annotations

_BYTES_PER_TOKEN = 4


def chars_to_token_estimate(byte_len: int) -> int:
    """Rough chars/bytes → token estimate (same heuristic as token_stats)."""
    return max(0, round(byte_len / _BYTES_PER_TOKEN))
