"""Live sync progress: percent, ETA, adaptive rate, status snapshot file."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import mkstemp
from typing import Any

from agentcore_cli import ui
from agentcore_cli.util import repo_root

PROGRESS_FILENAME = "sync-progress.json"
DEFAULT_INTERVAL_SEC = 30.0
# Start showing rate/ETA within the first 10s even if no file has finished yet.
EARLY_RATE_AFTER_SEC = 5.0
SAMPLE_KEEP_SEC = 180.0
# Recent window for adaptive pace (resists single slow files less than pure instant).
RECENT_WINDOW_SEC = 60.0
# Blend: favor lifetime avg for stability; recent pulls ETA when pace sustains a change.
LIFETIME_WEIGHT = 0.65
RECENT_WEIGHT = 0.35
# Light EWMA on the blended rate so printed ETA does not jump every tick.
BLEND_EWMA_ALPHA = 0.22
# Need a few completions before trusting lifetime over provisional.
MIN_DONE_FOR_LIFETIME = 1


def progress_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / ".agentcore" / PROGRESS_FILENAME


def wall_clock_now() -> str:
    """Local wall clock to the second: ``YYYY-MM-DD HH:MM:SS``."""
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


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
    _t0: float = field(default_factory=lambda: time.monotonic())
    _last_print: float = 0.0
    _last_pct_printed: float = -1.0
    _samples: list[tuple[float, int]] = field(default_factory=list)
    _ewma_rate: float | None = None  # files / second (smoothed blend)
    _rate_basis: str = ""
    _latest: dict[str, Any] = field(default_factory=dict)
    _finished: bool = False
    _had_rate: bool = False
    _lock: Any = field(default=None, repr=False)

    def __post_init__(self) -> None:
        import threading

        if self.progress_file is None:
            self.progress_file = progress_path()
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        object.__setattr__(self, "_lock", threading.Lock())

    def __call__(self, event: dict[str, Any]) -> None:
        self.update(event)

    def update(self, event: dict[str, Any]) -> None:
        with self._lock:
            self._update_unlocked(event)

    def update_sessions(self, sessions: dict[str, Any]) -> None:
        with self._lock:
            if not self._latest:
                return
            now = time.monotonic()
            sessions_changed = self._latest.get("llm_sessions") != sessions
            due = (now - self._last_print) >= self.interval_sec
            need_early_rate = (
                not self._had_rate
                and (now - self._t0) >= EARLY_RATE_AFTER_SEC
            )
            # Unchanged sessions: still refresh ETA/rate on interval, and once
            # when the early provisional rate becomes available.
            if not sessions_changed and not due and not need_early_rate:
                return
            event = dict(self._latest)
            event.update(
                {
                    "rpm": int(sessions.get("rpm") or 0),
                    "rpm_inflight_cap": int(sessions.get("inflight_cap") or 0),
                    "rpm_inflight": int(sessions.get("inflight_count") or 0),
                    "rpm_starts_in_window": int(sessions.get("starts_in_window") or 0),
                    "llm_sessions": dict(sessions),
                }
            )
            self._update_unlocked(event)

    def _update_unlocked(self, event: dict[str, Any]) -> None:
        event = dict(event)
        previous_sessions = self._latest.get("llm_sessions")
        if "llm_sessions" not in event and isinstance(previous_sessions, dict):
            event["llm_sessions"] = dict(previous_sessions)
            event.setdefault("rpm", int(previous_sessions.get("rpm") or 0))
            event.setdefault(
                "rpm_inflight_cap",
                int(previous_sessions.get("inflight_cap") or 0),
            )
            event.setdefault(
                "rpm_inflight",
                int(previous_sessions.get("inflight_count") or 0),
            )
            event.setdefault(
                "rpm_starts_in_window",
                int(previous_sessions.get("starts_in_window") or 0),
            )
        now = time.monotonic()
        done = int(event.get("done") or 0)
        total = max(int(event.get("total") or 0), 0)
        in_flight = int(event.get("files_in_flight") or 0)
        status = str(event.get("status") or "")
        self._latest = event
        self._samples.append((now, done))
        cutoff = now - SAMPLE_KEEP_SEC
        self._samples = [s for s in self._samples if s[0] >= cutoff]

        estimated = self._estimate_rate(
            now,
            done,
            in_flight=in_flight,
            total=total,
        )
        if estimated is not None:
            rate, basis = estimated
            if rate > 0:
                if self._ewma_rate is None:
                    self._ewma_rate = rate
                else:
                    self._ewma_rate = (
                        BLEND_EWMA_ALPHA * rate
                        + (1.0 - BLEND_EWMA_ALPHA) * self._ewma_rate
                    )
                self._rate_basis = basis

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
            "rate_basis": self._rate_basis or None,
            "file": event.get("file") or "",
            "symbols_indexed": int(event.get("symbols_indexed") or 0),
            "edges_written": int(event.get("edges_written") or 0),
            "approx_tokens": int(event.get("approx_tokens") or 0),
            "chars_read": int(event.get("chars_read") or 0),
            "files_in_flight": in_flight,
            "files_in_flight_paths": list(event.get("files_in_flight_paths") or [])[:8],
            "file_workers": int(event.get("file_workers") or 0),
            "prior_indexed": int(event.get("prior_indexed") or 0),
            "queue_new": int(event.get("queue_new") or 0),
            "queue_changed": int(event.get("queue_changed") or 0),
            "queue_unchanged": int(event.get("queue_unchanged") or 0),
            "rpm": int(event.get("rpm") or 0),
            "rpm_inflight_cap": int(event.get("rpm_inflight_cap") or 0),
            "rpm_inflight": int(event.get("rpm_inflight") or 0),
            "rpm_starts_in_window": int(event.get("rpm_starts_in_window") or 0),
            "llm_sessions": dict(event.get("llm_sessions") or {}),
            "pid": os.getpid(),
            "updated_at": time.time(),
            "logged_at": wall_clock_now(),
        }
        self._write(snapshot)

        # Print sparsely: start/finish, first ETA, then every interval_sec (default 30s).
        force = status in {"started", "finished"} or pct >= 100.0
        due = (now - self._last_print) >= self.interval_sec
        rate_became_available = bool(self._ewma_rate) and not self._had_rate
        if self._ewma_rate:
            self._had_rate = True
        if not (force or due or rate_became_available):
            return
        self._last_print = now
        self._last_pct_printed = pct
        self._print_line(snapshot)
        if status == "finished":
            self._finished = True

    def finish(self) -> None:
        with self._lock:
            if self._finished:
                self.clear()
                return
            # Ensure a final line if ingest was empty/fast
            if self._latest:
                event = dict(self._latest)
                event["status"] = "finished"
                event["done"] = int(event.get("total") or event.get("done") or 0)
                self._update_unlocked(event)
            self.clear()

    def clear(self) -> None:
        path = self.progress_file
        if path and path.is_file():
            try:
                path.unlink()
            except OSError:
                pass

    def _estimate_rate(
        self,
        now: float,
        done: int,
        *,
        in_flight: int = 0,
        total: int = 0,
    ) -> tuple[float, str] | None:
        """Return ``(files_per_sec, basis)`` for ETA.

        Prefer a **blend of lifetime average and recent-window average** once
        files have finished (stable against one slow file, still tracks sustained
        slowdowns). Before any completion, use a conservative provisional pace.
        """
        elapsed = now - self._t0
        lifetime = self._lifetime_rate(now, done)
        recent = self._recent_rate(now, done)

        if lifetime is not None and recent is not None:
            blended = LIFETIME_WEIGHT * lifetime + RECENT_WEIGHT * recent
            return blended, "avg+recent"
        if lifetime is not None:
            return lifetime, "avg"
        if recent is not None:
            return recent, "recent"

        if elapsed < EARLY_RATE_AFTER_SEC or total <= 0:
            return None
        # Provisional only while nothing has finished yet.
        active = max(int(in_flight), 1)
        return active / elapsed, "provisional"

    def _lifetime_rate(self, now: float, done: int) -> float | None:
        if done < MIN_DONE_FOR_LIFETIME:
            return None
        elapsed = now - self._t0
        if elapsed < 0.5:
            return None
        return done / elapsed

    def _recent_rate(self, now: float, done: int) -> float | None:
        if done <= 0:
            return None
        window = max(RECENT_WINDOW_SEC, float(self.interval_sec))
        # Oldest sample still inside the recent window (or just outside for Δ).
        older = [(t, d) for t, d in self._samples if now - t >= min(window, 5.0)]
        if not older:
            return None
        t0, d0 = older[0]
        dt = now - t0
        dd = done - d0
        if dt <= 0 or dd <= 0:
            return None
        return dd / dt

    def _write(self, snapshot: dict[str, Any]) -> None:
        assert self.progress_file is not None
        fd, tmp_name = mkstemp(
            prefix=f".{self.progress_file.name}.",
            suffix=".tmp",
            dir=self.progress_file.parent,
        )
        tmp = Path(tmp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                fd = -1
                handle.write(json.dumps(snapshot, indent=2, sort_keys=True) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            tmp.replace(self.progress_file)
        except BaseException:
            if fd >= 0:
                os.close(fd)
            tmp.unlink(missing_ok=True)
            raise

    def _print_line(self, snap: dict[str, Any]) -> None:
        pct = float(snap["percent"])
        bar = format_bar(pct)
        eta = snap.get("eta_sec")
        eta_txt = "…" if eta is None and snap["done"] < snap["total"] else format_duration(float(eta or 0))
        rate = snap.get("files_per_sec")
        basis = str(snap.get("rate_basis") or "")
        if rate:
            rate_txt = f"{rate:.2f}/s"
            if basis:
                rate_txt += f" ({basis})"
        else:
            rate_txt = "…"
        file_name = str(snap.get("file") or "")
        if len(file_name) > 48:
            file_name = "…" + file_name[-47:]
        logged_at = str(snap.get("logged_at") or wall_clock_now())
        elapsed_txt = format_duration(float(snap["elapsed_sec"]))
        print()
        print(
            f"   {ui.dim('at')} {logged_at}  "
            f"{ui.dim('elapsed')} {elapsed_txt}"
        )
        line = (
            f"   {ui.accent(bar)} {ui.bold(f'{pct:5.1f}%')}  "
            f"this run {snap['done']}/{snap['total']}  "
            f"ETA {eta_txt}  "
            f"rate {rate_txt}"
        )
        print(line)
        prior = int(snap.get("prior_indexed") or 0)
        q_new = int(snap.get("queue_new") or 0)
        q_changed = int(snap.get("queue_changed") or 0)
        q_unchanged = int(snap.get("queue_unchanged") or 0)
        if prior or q_new or q_changed or q_unchanged:
            print(
                f"   {ui.dim('graph')} prior file symbols {prior}  "
                f"{ui.dim('queue')} new={q_new}  changed={q_changed}  "
                f"unchanged_recheck={q_unchanged}"
            )
            if int(snap["done"]) == 0 and int(snap.get("files_in_flight") or 0) > 0:
                print(
                    f"   {ui.dim('note')} 0 finished so far — counters are this run only; "
                    f"in-flight files have not completed yet"
                )
        detail = (
            f"   {ui.dim('symbols')} {snap.get('symbols_indexed')}  "
            f"{ui.dim('edges')} {snap.get('edges_written')}  "
            f"{ui.dim('≈tokens')} {snap.get('approx_tokens')}"
        )
        if file_name:
            detail += f"  {ui.dim('file')} {file_name}"
        print(detail)

        in_flight = int(snap.get("files_in_flight") or 0)
        workers = int(snap.get("file_workers") or 0)
        rpm = int(snap.get("rpm") or 0)
        rpm_cap = int(snap.get("rpm_inflight_cap") or rpm or 0)
        rpm_inf = int(snap.get("rpm_inflight") or 0)
        rpm_starts = int(snap.get("rpm_starts_in_window") or 0)
        if workers or in_flight or rpm:
            conc = (
                f"   {ui.dim('parallel')} {in_flight} active / {workers or '?'} workers"
            )
            paths = list(snap.get("files_in_flight_paths") or [])
            if paths:
                shown = ", ".join(str(p) for p in paths[:4])
                if len(paths) > 4:
                    shown += ", …"
                conc += f"  [{shown}]"
            print(conc)
            if rpm:
                print(
                    f"   {ui.dim('rpm')} inflight {rpm_inf}/{rpm_cap or rpm}  "
                    f"starts {rpm_starts}/{rpm} (rolling 60s)"
                )
        print()


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
