"""Embedding refresh orchestration (GAP-T03).

Role: re-embed symbols when model/dims change or rows are missing per refresh-policy.
SoT: PostgreSQL/pgvector EmbeddingIndex rows + refresh-policy.json; turbovec is replica only.
Allowed: skip when model matches; fail-open turbovec sync; dry-run without writes.
Forbidden: treating ANN as SoR; cross-tenant refresh; silent incomplete without failed state.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from ..domain.rag import SEARCHABLE_SYMBOL_KINDS

RefreshState = Literal["pending", "running", "failed", "complete"]

_DEFAULT_POLICY = (
    Path(__file__).resolve().parents[5]
    / "configs"
    / "embeddings"
    / "refresh-policy.json"
)


@dataclass
class RefreshReport:
    policy_id: str
    target_model: str
    state: RefreshState = "pending"
    scanned: int = 0
    refreshed: int = 0
    skipped: int = 0
    deleted_orphans: int = 0
    dry_run: bool = False
    error: str | None = None
    reasons: dict[str, int] = field(default_factory=dict)

    def public(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "policy_id": self.policy_id,
            "target_model": self.target_model,
            "state": self.state,
            "scanned": self.scanned,
            "refreshed": self.refreshed,
            "skipped": self.skipped,
            "deleted_orphans": self.deleted_orphans,
            "dry_run": self.dry_run,
            "reasons": dict(self.reasons),
        }
        if self.error:
            payload["error"] = self.error
        return payload


def load_refresh_policy(path: Path | None = None) -> dict[str, Any]:
    policy_path = path or _DEFAULT_POLICY
    data = json.loads(policy_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"refresh policy must be an object: {policy_path}")
    return data


def _require_tenant_scope(scope: Any, policy: dict[str, Any]) -> None:
    isolation = policy.get("tenant_isolation") or {}
    keys = list(isolation.get("scope_keys") or ("tenant_id", "workspace_id", "project_id"))
    missing = [key for key in keys if not str(getattr(scope, key, "") or "").strip()]
    if missing:
        raise ValueError(f"embedding refresh requires scope fields: {', '.join(missing)}")
    if isolation.get("cross_tenant_forbidden", True) is not True:
        raise ValueError("refresh-policy tenant_isolation.cross_tenant_forbidden must be true")


class EmbeddingRefreshMixin:
    """Mixin for CodeGraphService — refresh embeddings under configured policy."""

    def refresh_embeddings(
        self,
        scope: Any,
        *,
        force: bool = False,
        dry_run: bool = False,
        policy_path: Path | None = None,
    ) -> RefreshReport:
        policy = load_refresh_policy(policy_path)
        target_model = str(
            getattr(self.embeddings, "model", None) or policy.get("default_model") or ""
        )
        report = RefreshReport(
            policy_id=str(policy.get("policy_id") or "unknown"),
            target_model=target_model,
            state="pending",
            dry_run=bool(dry_run),
        )
        try:
            _require_tenant_scope(scope, policy)
            report.state = "running"
            if self.embedding_index is None:
                report.state = "complete"
                return report

            symbols = list(self.store.list_symbols(scope))
            models: dict[str, str] = {}
            list_models = getattr(self.embedding_index, "list_symbol_models", None)
            if callable(list_models):
                models = dict(list_models(scope))

            live_ids = {s.id for s in symbols}
            for symbol_id in list(models):
                if symbol_id not in live_ids:
                    if not dry_run:
                        self._delete_embedding(scope, symbol_id)
                    report.deleted_orphans += 1
                    report.reasons["orphan_cleanup_after_delete"] = (
                        report.reasons.get("orphan_cleanup_after_delete", 0) + 1
                    )

            skip_when_unchanged = bool(policy.get("skip_when_model_unchanged", True)) and not force
            pending: list[tuple[Any, str, str, str]] = []
            for symbol in symbols:
                kind = str(getattr(symbol.kind, "value", symbol.kind) or "unknown")
                if kind not in SEARCHABLE_SYMBOL_KINDS:
                    continue
                report.scanned += 1
                existing_model = models.get(symbol.id, "")
                needs = force or not existing_model or existing_model != target_model
                reason = (
                    "operator_force_refresh"
                    if force
                    else (
                        "missing_embedding_row"
                        if not existing_model
                        else "configured_model_mismatch"
                        if existing_model != target_model
                        else ""
                    )
                )
                if not needs and skip_when_unchanged:
                    report.skipped += 1
                    continue
                text = " ".join(
                    part
                    for part in (
                        getattr(symbol, "qualified_name", "") or getattr(symbol, "name", ""),
                        getattr(symbol, "signature", "") or "",
                        getattr(symbol, "body", "") or "",
                        getattr(symbol, "ai_documentation", "") or "",
                    )
                    if part
                ).strip()
                if not text:
                    report.skipped += 1
                    continue
                if dry_run:
                    report.refreshed += 1
                    if reason:
                        report.reasons[reason] = report.reasons.get(reason, 0) + 1
                    continue
                pending.append((symbol, kind, text, reason))
            batch = getattr(self.embeddings, "embed_many", None)
            chunks = [
                pending[offset : offset + 128]
                for offset in range(0, len(pending), 128)
            ]

            def _embed_chunk(chunk: list[tuple[Any, str, str, str]]):
                texts = [item[2] for item in chunk]
                results = (
                    list(batch(texts))
                    if callable(batch)
                    else [self.embeddings.embed(text) for text in texts]
                )
                if len(results) != len(chunk):
                    raise RuntimeError(
                        "embedding batch returned "
                        f"{len(results)} results for {len(chunk)} symbols"
                    )
                return chunk, results

            try:
                configured_workers = int(
                    os.environ.get("AGENTCORE_EMBEDDING_REFRESH_WORKERS", "4")
                )
            except ValueError:
                configured_workers = 4
            workers = min(
                max(1, configured_workers),
                16,
                max(1, len(chunks)),
            )
            with ThreadPoolExecutor(
                max_workers=workers,
                thread_name_prefix="embedding-refresh",
            ) as executor:
                futures = [executor.submit(_embed_chunk, chunk) for chunk in chunks]
                completed = (future.result() for future in as_completed(futures))
                for chunk, results in completed:
                    for (symbol, kind, _text, reason), result in zip(
                        chunk,
                        results,
                        strict=True,
                    ):
                        self._index_embedding(
                            scope,
                            symbol.id,
                            list(result.vector),
                            kind=kind,
                        )
                        report.refreshed += 1
                        if reason:
                            report.reasons[reason] = report.reasons.get(reason, 0) + 1
            report.state = "complete"
            return report
        except Exception as exc:  # noqa: BLE001 — job state must surface failure
            report.state = "failed"
            report.error = f"{type(exc).__name__}: {exc}"
            return report
