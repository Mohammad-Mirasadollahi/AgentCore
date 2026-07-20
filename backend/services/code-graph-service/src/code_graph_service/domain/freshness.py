"""Freshness / stale banners (Wave 3) and rationale comment extraction."""

from __future__ import annotations

import re
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

    def mark_pending(self, file_path: str, *, now: float | None = None) -> None:
        self.pending[file_path.replace("\\", "/")] = float(now if now is not None else time())

    def clear_pending(self, file_path: str | None = None) -> None:
        if file_path is None:
            self.pending.clear()
        else:
            self.pending.pop(file_path.replace("\\", "/"), None)
        self.last_sync_at = time()

    def stale_banner(self, referenced_paths: list[str] | None = None) -> dict:
        referenced = {p.replace("\\", "/") for p in (referenced_paths or [])}
        pending_refs = sorted(p for p in self.pending if p in referenced) if referenced else []
        other = sorted(p for p in self.pending if p not in referenced) if referenced else sorted(self.pending)
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
            "pending_count": len(self.pending),
            "pending_files": sorted(self.pending)[:50],
            "banner": banner,
            "footer": footer,
            "last_sync_at": self.last_sync_at or None,
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
