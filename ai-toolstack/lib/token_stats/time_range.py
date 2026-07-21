"""Parse --since / --until for ai-toolstack.sh stats."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import NamedTuple


class TimeRange(NamedTuple):
    start: datetime
    end: datetime
    label: str


_REL = re.compile(r"^(\d+)(h|d|w|m)$", re.I)


def _parse_iso(value: str) -> datetime:
    text = value.strip()
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        return datetime.fromisoformat(text + "T00:00:00").replace(tzinfo=timezone.utc)
    dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_time_range(
    since: str | None,
    until: str | None,
) -> TimeRange:
    now = datetime.now(timezone.utc)
    end = _parse_iso(until) if until else now

    if since:
        m = _REL.match(since.strip())
        if m:
            n, unit = int(m.group(1)), m.group(2).lower()
            delta = {
                "h": timedelta(hours=n),
                "d": timedelta(days=n),
                "w": timedelta(weeks=n),
                "m": timedelta(days=n * 30),
            }[unit]
            start = end - delta
            label = f"last {since}"
        else:
            start = _parse_iso(since)
            label = f"{start.date().isoformat()} → {end.date().isoformat()}"
    else:
        start = end - timedelta(days=7)
        label = "last 7d (default)"

    if start > end:
        start, end = end, start
    return TimeRange(start=start, end=end, label=label)
