"""Freshness / stale banners (Wave 3) and rationale comment extraction."""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass, field
from time import time


_RATIONALE = re.compile(
    r"^\s*(?:#|//|/\*)\s*(?P<tag>WHY|NOTE|HACK|TODO|FIXME)\s*:\s*(?P<body>.+?)(?:\*/)?\s*$",
    re.IGNORECASE | re.MULTILINE,
)


@dataclass(frozen=True)
class RationaleHit:
    tag: str
    body: str
    line: int


@dataclass
class FreshnessState:
    """In-process pending file edits awaiting ingest/sync."""

    pending: dict[str, float] = field(default_factory=dict)  # path -> unix mtime noted
    last_sync_at: float = 0.0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)

    def mark_pending(self, file_path: str, *, now: float | None = None) -> None:
        with self._lock:
            self.pending[file_path.replace("\\", "/")] = float(now if now is not None else time())

    def mark_pending_many(self, file_paths: list[str], *, now: float | None = None) -> None:
        stamp = float(now if now is not None else time())
        with self._lock:
            for path in file_paths:
                cleaned = (path or "").strip().replace("\\", "/")
                if cleaned:
                    self.pending[cleaned] = stamp

    def clear_pending(self, file_path: str | None = None) -> None:
        with self._lock:
            if file_path is None:
                self.pending.clear()
            else:
                self.pending.pop(file_path.replace("\\", "/"), None)
            self.last_sync_at = time()

    def stale_banner(self, referenced_paths: list[str] | None = None) -> dict:
        referenced = {p.replace("\\", "/") for p in (referenced_paths or [])}
        with self._lock:
            pending_snapshot = dict(self.pending)
            last_sync = self.last_sync_at
        pending_refs = sorted(p for p in pending_snapshot if p in referenced) if referenced else []
        other = (
            sorted(p for p in pending_snapshot if p not in referenced)
            if referenced
            else sorted(pending_snapshot)
        )
        banner = None
        footer = None
        if pending_refs:
            banner = (
                "⚠️ Pending sync: "
                + ", ".join(pending_refs[:8])
                + " — read those files directly for live content."
            )
        elif other:
            footer = f"Pending sync (not in this result): {', '.join(other[:5])}"
        return {
            "pending_count": len(pending_snapshot),
            "pending_files": sorted(pending_snapshot)[:50],
            "banner": banner,
            "footer": footer,
            "last_sync_at": last_sync or None,
        }


def extract_rationale_comments(source: str) -> list[RationaleHit]:
    hits: list[RationaleHit] = []
    for match in _RATIONALE.finditer(source):
        line = source[: match.start()].count("\n") + 1
        hits.append(
            RationaleHit(
                tag=match.group("tag").upper(),
                body=match.group("body").strip(),
                line=line,
            )
        )
    return hits
