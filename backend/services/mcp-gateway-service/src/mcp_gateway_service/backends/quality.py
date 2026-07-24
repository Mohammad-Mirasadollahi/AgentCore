"""Quality-audit MCP handlers (docs + code debt for coding agents)."""

from __future__ import annotations

from typing import Any

from core_data_service.core import Kind

from .platform import PlatformBackends


def quality_audit(
    backends: PlatformBackends,
    arguments: dict[str, Any],
    *,
    scope: dict[str, str],
    correlation_id: str,
    base: dict[str, Any],
) -> dict[str, Any]:
    """Return compact quality-audit findings; optionally create durable follow-up tasks."""
    from agentcore_cli.commands.quality_audit.collect import build_quality_audit_report
    from agentcore_cli.commands.quality_audit.mcp_payload import compact_quality_audit_payload

    top_n = int(arguments.get("top_n") or 25)
    top_n = max(1, min(top_n, 100))
    severities_raw = arguments.get("severities")
    severities: list[str] | None = None
    if isinstance(severities_raw, list):
        severities = [str(x).strip().lower() for x in severities_raw if str(x).strip()]
    elif isinstance(severities_raw, str) and severities_raw.strip():
        severities = [p.strip().lower() for p in severities_raw.split(",") if p.strip()]

    report = build_quality_audit_report()
    payload = compact_quality_audit_payload(
        report,
        top_n=top_n,
        severities=severities,
    )

    created: list[dict[str, Any]] = []
    if bool(arguments.get("create_tasks")):
        created = _create_tasks_for_findings(
            backends,
            findings=list(payload.get("findings") or []),
            scope=scope,
            correlation_id=correlation_id,
        )
    return {
        **base,
        "ok": True,
        **payload,
        "tasks_created": created,
        "tasks_created_count": len(created),
    }


def _create_tasks_for_findings(
    backends: PlatformBackends,
    *,
    findings: list[dict[str, Any]],
    scope: dict[str, str],
    correlation_id: str,
) -> list[dict[str, Any]]:
    """One durable task per high/medium finding path (idempotent key per category+path)."""
    out: list[dict[str, Any]] = []
    for idx, row in enumerate(findings):
        severity = str(row.get("severity") or "").lower()
        if severity not in {"high", "medium"}:
            continue
        category = str(row.get("category") or "quality")
        path = str(row.get("path") or "").strip() or "(unknown)"
        title = f"Quality: {category} — {path}"
        instructions = (
            f"Remediate AgentCore quality finding.\n"
            f"category={category}\n"
            f"severity={severity}\n"
            f"path={path}\n"
            f"detail={row.get('detail') or ''}\n"
            f"fix_hint={row.get('fix_hint') or ''}\n"
            f"Use skill agentcore-quality-audit / agentcore-standards-on-edit."
        )
        key = f"mcp-quality:{scope.get('project_id')}:{category}:{path}:{correlation_id}:{idx}"
        try:
            record = backends.core.create(
                Kind.TASK,
                backends.core_scope(scope),
                backends.actor_id,
                correlation_id,
                key[:200],
                {
                    "title": title[:240],
                    "assignee_type": "backend",
                    "instructions": instructions,
                    "acceptance_criteria": [
                        "Finding cleared in agentcore_quality_audit",
                        "Tests pass when code changed",
                    ],
                },
            )
            out.append(record.public())
        except Exception:  # noqa: BLE001 — best-effort; audit payload still returns
            continue
    return out
