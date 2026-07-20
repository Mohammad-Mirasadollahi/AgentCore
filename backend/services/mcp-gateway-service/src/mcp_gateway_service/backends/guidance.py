from __future__ import annotations

from typing import Any
from uuid import uuid4

from . import _paths  # noqa: F401 — side effect: service path bootstrap

from common_context_service.core import NotFoundError

from .platform import PlatformBackends


def guidance_resolve(
    backends: PlatformBackends,
    arguments: dict[str, Any],
    *,
    scope: dict[str, str],
    correlation_id: str,
    base: dict[str, Any],
) -> dict[str, Any]:
    backends.ensure_guidance_seed(scope, correlation_id)
    budget_overrides = arguments.get("budget_overrides")
    if budget_overrides is not None and not isinstance(budget_overrides, dict):
        raise ValueError("budget_overrides must be an object")
    bundle = backends.common_context.resolve_guidance(
        backends.common_context_scope(scope),
        task_summary=str(arguments.get("task_summary") or ""),
        workflow_type=str(arguments.get("workflow_type") or "coding"),
        include_skill_bodies=bool(arguments.get("include_skill_bodies") or False),
        budget_overrides=budget_overrides,
        include_general_common_context=bool(arguments.get("include_general_common_context") or False),
    )
    return {**base, "bundle": bundle}


def guidance_list_skills(
    backends: PlatformBackends,
    arguments: dict[str, Any],
    *,
    scope: dict[str, str],
    correlation_id: str,
    base: dict[str, Any],
) -> dict[str, Any]:
    backends.ensure_guidance_seed(scope, correlation_id or str(uuid4()))
    skills = backends.common_context.list_skills(
        backends.common_context_scope(scope),
        query=str(arguments.get("query") or ""),
    )
    return {**base, "skills": skills}


def guidance_get_skill(
    backends: PlatformBackends,
    arguments: dict[str, Any],
    *,
    scope: dict[str, str],
    correlation_id: str,
    base: dict[str, Any],
) -> dict[str, Any]:
    backends.ensure_guidance_seed(scope, correlation_id or str(uuid4()))
    skill_id = str(arguments.get("skill_id") or "").strip() or None
    name = str(arguments.get("name") or "").strip() or None
    if not skill_id and not name:
        raise ValueError("skill_id or name is required")
    try:
        skill = backends.common_context.get_skill(
            backends.common_context_scope(scope),
            skill_id=skill_id,
            name=name,
            bundle_id=str(arguments.get("bundle_id") or "").strip() or None,
        )
    except NotFoundError as exc:
        raise ValueError(str(exc)) from exc
    return {**base, "skill": skill}
