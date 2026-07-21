"""Live sync progress: percent, ETA, adaptive rate, status snapshot file."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agentcore_cli import ui
from agentcore_cli.util import repo_root

PROGRESS_FILENAME = "sync-progress.json"
DEFAULT_INTERVAL_SEC = 10.0


def progress_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / ".agentcore" / PROGRESS_FILENAME


def format_duration(seconds: float) -> str:
    sec = max(0, int(seconds))
    if sec < 60:
        return f"{sec}s"
    minutes, rem = divmod(sec, 60)
    if minutes < 60:
        return f"{minutes}m {rem}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m"


def format_bar(pct: float, *, width: int = 24) -> str:
    pct = max(0.0, min(100.0, pct))
    filled = int(round(width * pct / 100.0))
    return "[" + ("#" * filled) + ("-" * (width - filled)) + "]"


@dataclass
class SyncProgressTracker:
    """Adaptive progress reporter for agentcore sync."""

    scope: str
    path: str
    interval_sec: float = DEFAULT_INTERVAL_SEC
    progress_file: Path | None = None
    _t0: float = field(default_factory=time.monotonic)
    _last_print: float = 0.0
    _last_pct_printed: float = -1.0
    _samples: list[tuple[float, int]] = field(default_factory=list)
    _ewma_rate: float | None = None  # files / second
    _latest: dict[str, Any] = field(default_factory=dict)
    _finished: bool = False

    def __post_init__(self) -> None:
        if self.progress_file is None:
            self.progress_file = progress_path()
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)

    def __call__(self, event: dict[str, Any]) -> None:
        self.update(event)

    def update(self, event: dict[str, Any]) -> None:
        now = time.monotonic()
        done = int(event.get("done") or 0)
        total = max(int(event.get("total") or 0), 0)
        status = str(event.get("status") or "")
        self._latest = dict(event)
        self._samples.append((now, done))
        # Keep ~2 minutes of samples for rate
        cutoff = now - 120.0
        self._samples = [s for s in self._samples if s[0] >= cutoff]
        instant = self._instant_rate(now, done)
        if instant is not None and instant > 0:
            if self._ewma_rate is None:
                self._ewma_rate = instant
            else:
                # Newer samples weigh more as we learn the machine
                alpha = 0.35
                self._ewma_rate = alpha * instant + (1.0 - alpha) * self._ewma_rate

        pct = (100.0 * done / total) if total else 0.0
        elapsed = now - self._t0
        eta = None
        remaining = max(total - done, 0)
        if self._ewma_rate and self._ewma_rate > 0 and remaining > 0:
            eta = remaining / self._ewma_rate

        snapshot = {
            "active": status != "finished",
            "scope": self.scope,
            "path": self.path,
            "phase": event.get("phase"),
            "status": status,
            "done": done,
            "total": total,
            "percent": round(pct, 1),
            "elapsed_sec": round(elapsed, 1),
            "eta_sec": None if eta is None else round(eta, 1),
            "files_per_sec": None if not self._ewma_rate else round(self._ewma_rate, 3),
            "file": event.get("file") or "",
            "symbols_indexed": int(event.get("symbols_indexed") or 0),
            "edges_written": int(event.get("edges_written") or 0),
            "approx_tokens": int(event.get("approx_tokens") or 0),
            "chars_read": int(event.get("chars_read") or 0),
            "pid": os.getpid(),
            "updated_at": time.time(),
        }
        self._write(snapshot)

        force = status in {"started", "finished"} or pct >= 100.0
        due = (now - self._last_print) >= self.interval_sec
        jumped = pct - self._last_pct_printed >= 5.0 and done > 0
        if not (force or due or jumped):
            return
        self._last_print = now
        self._last_pct_printed = pct
        self._print_line(snapshot)
        if status == "finished":
            self._finished = True

    def finish(self) -> None:
        if self._finished:
            self.clear()
            return
        # Ensure a final line if ingest was empty/fast
        if self._latest:
            event = dict(self._latest)
            event["status"] = "finished"
            event["done"] = int(event.get("total") or event.get("done") or 0)
            self.update(event)
        self.clear()

    def clear(self) -> None:
        path = self.progress_file
        if path and path.is_file():
            try:
                path.unlink()
            except OSError:
                pass

    def _instant_rate(self, now: float, done: int) -> float | None:
        # Prefer rate over last ~interval window
        window = max(self.interval_sec, 5.0)
        older = [(t, d) for t, d in self._samples if now - t >= min(window, 3.0)]
        if not older:
            elapsed = now - self._t0
            if elapsed < 0.5 or done <= 0:
                return None
            return done / elapsed
        t0, d0 = older[0]
        dt = now - t0
        dd = done - d0
        if dt <= 0 or dd < 0:
            return None
        return dd / dt

    def _write(self, snapshot: dict[str, Any]) -> None:
        assert self.progress_file is not None
        tmp = self.progress_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(self.progress_file)

    def _print_line(self, snap: dict[str, Any]) -> None:
        pct = float(snap["percent"])
        bar = format_bar(pct)
        eta = snap.get("eta_sec")
        eta_txt = "…" if eta is None and snap["done"] < snap["total"] else format_duration(float(eta or 0))
        rate = snap.get("files_per_sec")
        rate_txt = f"{rate:.2f}/s" if rate else "…"
        file_name = str(snap.get("file") or "")
        if len(file_name) > 48:
            file_name = "…" + file_name[-47:]
        line = (
            f"   {ui.accent(bar)} {ui.bold(f'{pct:5.1f}%')}  "
            f"files {snap['done']}/{snap['total']}  "
            f"elapsed {format_duration(float(snap['elapsed_sec']))}  "
            f"ETA {eta_txt}  "
            f"rate {rate_txt}"
        )
        print(line)
        detail = (
            f"   {ui.dim('symbols')} {snap.get('symbols_indexed')}  "
            f"{ui.dim('edges')} {snap.get('edges_written')}  "
            f"{ui.dim('≈tokens')} {snap.get('approx_tokens')}"
        )
        if file_name:
            detail += f"  {ui.dim('file')} {file_name}"
        print(detail)


def read_live_progress(*, max_age_sec: float = 30.0, root: Path | None = None) -> dict[str, Any] | None:
    """Return sync progress snapshot if a sync looks active."""
    path = progress_path(root)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict) or not data.get("active"):
        return None
    updated = float(data.get("updated_at") or 0)
    if updated <= 0 or (time.time() - updated) > max_age_sec:
        return None
    pid = int(data.get("pid") or 0)
    if pid > 0:
        try:
            os.kill(pid, 0)
        except OSError:
            return None
    return data
