"""Serialize store mutations for concurrent ingest workers (single Postgres connection)."""

from __future__ import annotations

import os
import threading
from typing import Any

def _rpm_from_env(env: dict[str, str]) -> int:
    raw = str(env.get("AGENTCORE_LITELLM_RPM", "") or "").strip()
    if not raw:
        try:
            from llm_gateway.settings import DEFAULT_RPM

            return int(DEFAULT_RPM)
        except Exception:  # noqa: BLE001
            return 30
    try:
        return max(1, int(raw))
    except ValueError:
        return 30


def _auto_file_workers(env: dict[str, str]) -> int:
    """Derive worker count from CPU cores and LiteLLM RPM (in-flight cap)."""
    cpus = os.cpu_count() or 1
    rpm = _rpm_from_env(env)
    return max(1, min(int(cpus), int(rpm)))


def sync_max_file_workers(environ: dict[str, str] | None = None) -> int:
    """Return parallel file-worker count.

    Default is **automatic**: ``min(cpu_count, AGENTCORE_LITELLM_RPM)``.
    Tracks the operator RPM setting; no fixed thread ceiling.
    Set ``AGENTCORE_SYNC_MAX_FILE_WORKERS`` to a positive integer to override.
    Values ``auto``, empty, or invalid fall back to the automatic formula.
    """
    env = environ if environ is not None else os.environ
    raw = str(env.get("AGENTCORE_SYNC_MAX_FILE_WORKERS", "") or "").strip().lower()
    if raw and raw not in {"auto", "0"}:
        try:
            return max(1, int(raw))
        except ValueError:
            pass
    return _auto_file_workers(env)


class LockedStore:
    """Proxy that holds a lock around every callable attribute of the underlying store."""

    def __init__(self, store: Any) -> None:
        object.__setattr__(self, "_store", store)
        object.__setattr__(self, "_lock", threading.RLock())

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._store, name)
        if not callable(attr):
            return attr

        def locked(*args: Any, **kwargs: Any) -> Any:
            with self._lock:
                return attr(*args, **kwargs)

        return locked


class LockedEmbeddings:
    """Bound concurrent embed calls to avoid overwhelming a shared local model."""

    def __init__(self, embeddings: Any, *, max_concurrency: int = 4) -> None:
        self._inner = embeddings
        self._slots = threading.BoundedSemaphore(max(1, int(max_concurrency)))
        self.model = getattr(embeddings, "model", "")

    @property
    def backend_name(self) -> str:
        return str(getattr(self._inner, "backend_name", self.model) or self.model)

    def preload(self) -> None:
        with self._slots:
            preload = getattr(self._inner, "preload", None)
            if callable(preload):
                preload()

    def embed(self, text: str, *, is_query: bool = False) -> Any:
        with self._slots:
            embed_fn = self._inner.embed
            try:
                return embed_fn(text, is_query=is_query)
            except TypeError:
                return embed_fn(text)
