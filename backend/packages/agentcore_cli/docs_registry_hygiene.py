"""Purge known live-test fixture noise from docs-sync symbol registry.

Role: remove never_linked / ghost_* / never_should_exist rows left by live QA
so docs_status coverage is not polluted. Called from quality_audit and sync
follow-up (best-effort; never fails the caller).
"""

from __future__ import annotations

from typing import Any

# Substrings matched against "symbol_path file_path" (case-sensitive path norms).
_FIXTURE_MARKERS = (
    "never_linked",
    "ghost_",
    "never_should_exist",
)


def is_docs_registry_fixture_noise(*, symbol_path: str, file_path: str = "") -> bool:
    """True when the docs-sync row looks like an intentional live-test fixture."""
    blob = f"{symbol_path or ''} {file_path or ''}"
    return any(marker in blob for marker in _FIXTURE_MARKERS)


def purge_docs_registry_fixture_noise(docs_service: Any, scope: Any) -> dict[str, Any]:
    """Unregister fixture-noise symbols in *scope*. Best-effort per row."""
    deleted: list[dict[str, str]] = []
    errors: list[str] = []
    try:
        symbols = list(docs_service.store.list_symbols(scope))
    except Exception as exc:  # noqa: BLE001
        return {
            "deleted_count": 0,
            "deleted": [],
            "errors": [f"list_symbols: {type(exc).__name__}: {exc}"],
        }

    for symbol in symbols:
        path = str(getattr(symbol, "symbol_path", "") or "")
        file_path = str(getattr(symbol, "file_path", "") or "")
        if not is_docs_registry_fixture_noise(symbol_path=path, file_path=file_path):
            continue
        sid = str(getattr(symbol, "id", "") or "")
        if not sid:
            continue
        try:
            docs_service.unregister_symbol(scope, sid)
            deleted.append({"id": sid, "symbol_path": path, "file_path": file_path})
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{sid}: {type(exc).__name__}: {exc}")

    return {
        "deleted_count": len(deleted),
        "deleted": deleted,
        "errors": errors,
    }
