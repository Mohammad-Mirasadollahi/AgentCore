"""After sync standards gate: durable follow-up tasks for skipped/stale debt.

Module contract:
- Role: turn skipped nonconforming docs (and optional quality code debt) into
  CoreData tasks + a local JSON mirror the coding agent can read.
- Source of truth: standards_gate skipped paths; optional quality-audit code rows.
- Failures: store/create errors are best-effort — never fail sync; surface
  ``create_errors`` when CoreData write fails (e.g. missing service imports).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from agentcore_cli.util import now_iso, repo_root


def _write_mirror(rows: list[dict[str, Any]]) -> Path:
    base = Path(repo_root()).resolve() / ".agentcore"
    base.mkdir(parents=True, exist_ok=True)
    path = base / "quality-followup-tasks.json"
    payload = {
        "generated_at": now_iso(),
        "count": len(rows),
        "tasks": rows,
        "agent_instruction": (
            "Remediate listed paths (skill agentcore-quality-audit / "
            "agentcore-standards-on-edit), then re-run agentcore_quality_audit / sync."
        ),
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _ensure_platform_imports() -> None:
    """Make core-data + MCP platform backends importable from the CLI process."""
    import sys

    root = Path(repo_root()).resolve()
    for rel in (
        ("backend", "services", "mcp-gateway-service", "src"),
        ("backend", "services", "core-data-service", "src"),
        ("backend", "services", "memory-service", "src"),
        ("backend", "services", "code-graph-service", "src"),
        ("backend", "services", "docs-sync-service", "src"),
        ("backend", "services", "common-context-service", "src"),
        ("backend", "packages"),
    ):
        path = root.joinpath(*rel)
        text = str(path)
        if path.is_dir() and text not in sys.path:
            sys.path.insert(0, text)


def _try_create_core_task(
    *,
    title: str,
    instructions: str,
    scope: Any,
    idempotency_key: str,
) -> dict[str, Any] | None:
    backends = None
    try:
        _ensure_platform_imports()
        from core_data_service.core import Kind
        from mcp_gateway_service.backends.platform import PlatformBackends

        backends = PlatformBackends.from_env()
        scope_dict = {
            "tenant_id": str(getattr(scope, "tenant_id", "") or "agentcore"),
            "workspace_id": str(getattr(scope, "workspace_id", "") or "dev"),
            "project_id": str(getattr(scope, "project_id", "") or "agentcore"),
        }
        correlation_id = str(uuid4())
        record = backends.core.create(
            Kind.TASK,
            backends.core_scope(scope_dict),
            "agentcore-cli-sync",
            correlation_id,
            idempotency_key[:200],
            {
                "title": title[:240],
                "assignee_type": "backend",
                "instructions": instructions,
                "acceptance_criteria": [
                    "Finding remediated",
                    "agentcore_quality_audit clean for path",
                ],
            },
        )
        return record.public()
    except Exception as exc:  # noqa: BLE001 — sync must not fail on follow-up
        return {"error": f"{type(exc).__name__}: {exc}", "ok": False}
    finally:
        if backends is not None:
            try:
                backends.close()
            except Exception:  # noqa: BLE001
                pass


def create_sync_followup_tasks(
    *,
    scope: Any,
    standards_gate: Any,
    include_code_audit: bool = True,
) -> dict[str, Any]:
    """Create follow-up tasks for skipped docs (+ optional stale/never-ingested code)."""
    specs: list[dict[str, Any]] = []
    skipped_docs = list(getattr(standards_gate, "skipped_docs", None) or [])
    skipped_code = list(getattr(standards_gate, "skipped_code", None) or [])

    if skipped_docs:
        paths = "\n".join(f"- {p}" for p in skipped_docs[:40])
        more = len(skipped_docs) - 40
        if more > 0:
            paths += f"\n- … and {more} more"
        specs.append(
            {
                "kind": "docs.standards_skipped",
                "title": f"Remediate {len(skipped_docs)} sync-skipped nonconforming doc(s)",
                "instructions": (
                    "These paths failed Full-tier docs-standards and were excluded from sync.\n"
                    "Fix with agentcore-standards-on-edit / docs remediator, then re-sync.\n"
                    f"{paths}"
                ),
                "paths": skipped_docs,
            }
        )
    if skipped_code:
        specs.append(
            {
                "kind": "code.standards_skipped",
                "title": f"Remediate {len(skipped_code)} sync-skipped code path(s)",
                "instructions": (
                    "Code paths excluded by the standards gate — remediate then re-sync.\n"
                    + "\n".join(f"- {p}" for p in skipped_code[:40])
                ),
                "paths": skipped_code,
            }
        )

    if include_code_audit:
        try:
            from agentcore_cli.commands.quality_audit.collect import build_quality_audit_report

            report = build_quality_audit_report()
            never = [
                f["path"]
                for f in report.get("findings") or []
                if f.get("category") == "code.never_ingested"
            ]
            stale = [
                f["path"]
                for f in report.get("findings") or []
                if f.get("category") == "code.stale_edited"
            ]
            if never or stale:
                specs.append(
                    {
                        "kind": "code.sync_debt",
                        "title": (
                            f"Code graph debt: {len(never)} never-ingested, "
                            f"{len(stale)} stale-edited"
                        ),
                        "instructions": (
                            "Run agentcore sync (AST-only ok if cloud LLM blocked) for:\n"
                            "Never ingested:\n"
                            + "\n".join(f"- {p}" for p in never[:30])
                            + "\nStale edited:\n"
                            + "\n".join(f"- {p}" for p in stale[:30])
                        ),
                        "paths": never + stale,
                    }
                )
        except Exception:  # noqa: BLE001
            pass

    created: list[dict[str, Any]] = []
    create_errors: list[str] = []
    mirrored: list[dict[str, Any]] = []
    project = str(getattr(scope, "project_id", "") or "agentcore")
    for spec in specs:
        mirrored.append(spec)
        key = f"sync-followup:{project}:{spec['kind']}:{len(spec.get('paths') or [])}"
        public = _try_create_core_task(
            title=str(spec["title"]),
            instructions=str(spec["instructions"]),
            scope=scope,
            idempotency_key=key,
        )
        if public and public.get("ok") is False and public.get("error"):
            create_errors.append(str(public["error"]))
        elif public:
            created.append(public)

    mirror_path = _write_mirror(mirrored)
    return {
        "ok": True,
        "specs_count": len(specs),
        "tasks_created_count": len(created),
        "tasks_created": created,
        "create_errors": create_errors,
        "mirror_path": str(mirror_path),
        "specs": mirrored,
    }
