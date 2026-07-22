from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import uuid4

from .seed_mcp_first import mcp_first_seed_payloads

GUIDANCE_KINDS = frozenset({"agents_entry", "always_rule", "skill"})
ITEM_TYPES = GUIDANCE_KINDS | frozenset({"general"})
SCOPE_KINDS = frozenset({"org", "project", "user"})
ORG_PROJECT_SENTINEL = "__org__"
USER_PROJECT_PREFIX = "__user__:"
LAYER_RANK = {"org": 1, "project": 2, "user": 3}

DEFAULT_ENTRY_BUDGET = 2000
DEFAULT_ALWAYS_RULES_BUDGET = 1500
DEFAULT_SKILL_CATALOG_BUDGET = 800


class CommonContextError(Exception):
    def __init__(self, code: str, category: str, message: str):
        super().__init__(message)
        self.code, self.category, self.message = code, category, message


class ValidationError(CommonContextError):
    def __init__(self, message: str):
        super().__init__("validation_error", "validation_error", message)


class ConflictError(CommonContextError):
    def __init__(self, message: str):
        super().__init__("conflict_error", "conflict_error", message)


class NotFoundError(CommonContextError):
    def __init__(self, message: str):
        super().__init__("not_found", "not_found_error", message)


@dataclass(frozen=True)
class Scope:
    tenant_id: str
    workspace_id: str
    project_id: str
    scope_kind: str = "project"
    user_id: str | None = None

    def __post_init__(self) -> None:
        if not all((self.tenant_id.strip(), self.workspace_id.strip(), self.project_id.strip())):
            raise ValidationError("tenant_id, workspace_id, and project_id are required")
        kind = (self.scope_kind or "project").strip()
        if kind not in SCOPE_KINDS:
            raise ValidationError(f"scope_kind must be one of: {', '.join(sorted(SCOPE_KINDS))}")
        object.__setattr__(self, "scope_kind", kind)
        if kind == "user" and not (self.user_id or "").strip():
            raise ValidationError("user_id is required when scope_kind is user")


def org_scope(tenant_id: str, workspace_id: str) -> Scope:
    return Scope(tenant_id, workspace_id, ORG_PROJECT_SENTINEL, scope_kind="org")


def user_scope(tenant_id: str, workspace_id: str, user_id: str) -> Scope:
    uid = user_id.strip()
    return Scope(tenant_id, workspace_id, f"{USER_PROJECT_PREFIX}{uid}", scope_kind="user", user_id=uid)


def project_scope(tenant_id: str, workspace_id: str, project_id: str) -> Scope:
    return Scope(tenant_id, workspace_id, project_id, scope_kind="project")


def resolve_authoring_scope(
    tenant_id: str,
    workspace_id: str,
    project_id: str,
    *,
    scope_kind: str = "project",
    user_id: str | None = None,
    actor_id: str | None = None,
) -> Scope:
    kind = (scope_kind or "project").strip() or "project"
    if kind == "org":
        return org_scope(tenant_id, workspace_id)
    if kind == "user":
        uid = (user_id or actor_id or "").strip()
        if not uid:
            raise ValidationError("user_id or actor_id is required for user scope_kind")
        return user_scope(tenant_id, workspace_id, uid)
    return project_scope(tenant_id, workspace_id, project_id)


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def _token_estimate(text: str) -> int:
    return max(20, len(text) // 4)


def _item_layer(item: dict[str, Any]) -> str:
    return str(item.get("scope_kind") or "project")


def _rule_key(item: dict[str, Any]) -> str:
    slug = str(item.get("slug") or "").strip()
    if slug:
        return f"slug:{slug}"
    return f"id:{item['id']}"


def _skill_key(item: dict[str, Any]) -> str:
    return str(item.get("name") or "").strip()


def _normalize_task_overrides(raw: dict[str, Any] | None) -> dict[str, set[str]]:
    if raw is None:
        return {"suppress_rule_slugs": set(), "suppress_skill_names": set()}
    if not isinstance(raw, dict):
        raise ValidationError("task_overrides must be an object")
    slugs = raw.get("suppress_rule_slugs") or []
    names = raw.get("suppress_skill_names") or []
    if not isinstance(slugs, list) or not isinstance(names, list):
        raise ValidationError("suppress_rule_slugs and suppress_skill_names must be lists")
    return {
        "suppress_rule_slugs": {str(x).strip() for x in slugs if str(x).strip()},
        "suppress_skill_names": {str(x).strip() for x in names if str(x).strip()},
    }


def _merge_by_key(
    layered: list[tuple[str, dict[str, Any]]],
    *,
    key_fn,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Merge items low→high rank. Higher replaces lower unless lower is mandatory with different body."""
    winners: dict[str, dict[str, Any]] = {}
    conflicts: list[dict[str, Any]] = []
    ordered = sorted(layered, key=lambda pair: (LAYER_RANK.get(pair[0], 0), pair[1]["id"]))
    for layer, item in ordered:
        tagged = {**item, "scope_kind": layer}
        key = key_fn(tagged)
        if not key:
            winners[f"anon:{tagged['id']}"] = tagged
            continue
        existing = winners.get(key)
        if existing is None:
            winners[key] = tagged
            continue
        if existing.get("body") == tagged.get("body") and existing.get("id") == tagged.get("id"):
            winners[key] = tagged
            continue
        if bool(existing.get("mandatory")) and existing.get("body") != tagged.get("body"):
            conflicts.append(
                {
                    "reason_code": "mandatory_override_blocked",
                    "key": key,
                    "kept_item_id": existing["id"],
                    "blocked_item_id": tagged["id"],
                    "kept_layer": _item_layer(existing),
                    "blocked_layer": layer,
                }
            )
            continue
        winners[key] = tagged
    return list(winners.values()), conflicts


class Store(Protocol):
    def begin_idempotency(self, scope: Scope, key: str, resource: str) -> str | None: ...
    def complete_idempotency(self, scope: Scope, key: str, resource: str, resource_id: str) -> None: ...
    def append_event(self, event: dict[str, Any]) -> None: ...
    def put_item(self, item: dict[str, Any]) -> None: ...
    def get_item(self, item_id: str, scope: Scope) -> dict[str, Any]: ...
    def list_items(self, scope: Scope, status: str | None = None) -> list[dict[str, Any]]: ...


class CommonContextService:
    def __init__(self, store: Store):
        self.store = store

    def propose_item(
        self,
        scope: Scope,
        actor_id: str,
        correlation_id: str,
        idempotency_key: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        title = str(payload.get("title") or "").strip()
        body = str(payload.get("body") or "").strip()
        if not title or not body:
            raise ValidationError("title and body are required")
        item_type = str(payload.get("item_type") or "general").strip() or "general"
        if item_type not in ITEM_TYPES:
            raise ValidationError(f"item_type must be one of: {', '.join(sorted(ITEM_TYPES))}")
        skill_name = str(payload.get("name") or "").strip() or None
        if item_type == "skill" and not skill_name:
            raise ValidationError("skill items require name")
        mandatory = bool(payload.get("mandatory") or False)
        if scope.scope_kind == "user":
            if item_type == "agents_entry":
                raise ValidationError("user scope cannot author agents_entry")
            if item_type == "general":
                raise ValidationError("user scope cannot author general items")
            if mandatory:
                raise ValidationError("user scope cannot set mandatory=true")
        existing = self.store.begin_idempotency(scope, idempotency_key, "common_item")
        if existing:
            return self.store.get_item(existing, scope)
        item_id = _new_id("cci")
        scores = {
            "frequency": float(payload.get("frequency") or 1.0),
            "recency": float(payload.get("recency") or 1.0),
            "confidence": float(payload.get("confidence") or 0.5),
            "user_pinning": float(payload.get("user_pinning") or 0.0),
            "task_similarity": float(payload.get("task_similarity") or 0.5),
            "project_relevance": float(payload.get("project_relevance") or 0.5),
            "effectiveness": float(payload.get("effectiveness") or 0.5),
        }
        score = (
            scores["frequency"] * 0.2
            + scores["recency"] * 0.15
            + scores["confidence"] * 0.2
            + scores["user_pinning"] * 0.15
            + scores["task_similarity"] * 0.1
            + scores["project_relevance"] * 0.1
            + scores["effectiveness"] * 0.1
        )
        when_to_use = payload.get("when_to_use")
        if when_to_use is not None and not isinstance(when_to_use, list):
            raise ValidationError("when_to_use must be a list of strings")
        item = {
            "id": item_id,
            "tenant_id": scope.tenant_id,
            "workspace_id": scope.workspace_id,
            "project_id": scope.project_id,
            "scope_kind": scope.scope_kind,
            "user_id": scope.user_id,
            "item_type": item_type,
            "title": title,
            "body": body,
            "status": "proposed",
            "version": 1,
            "score": score,
            "score_components": scores,
            "workflow_type": payload.get("workflow_type"),
            "task_type": payload.get("task_type"),
            "slug": str(payload.get("slug") or "").strip() or None,
            "name": skill_name,
            "description": str(payload.get("description") or "").strip() or None,
            "when_to_use": when_to_use,
            "priority": int(payload.get("priority") or 0),
            "mandatory": mandatory,
            "applicability": payload.get("applicability"),
            "created_by": actor_id,
            "correlation_id": correlation_id,
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.put_item(item)
        self.store.complete_idempotency(scope, idempotency_key, "common_item", item_id)
        self.store.append_event(
            {
                "event_type": "common_item.proposed",
                "item_id": item_id,
                "item_type": item_type,
                "scope_kind": scope.scope_kind,
            }
        )
        return item

    def approve_item(self, scope: Scope, item_id: str, actor_id: str) -> dict[str, Any]:
        item = self.store.get_item(item_id, scope)
        if item["status"] == "approved":
            return item
        if item["status"] not in {"proposed", "under_review"}:
            raise ConflictError("item cannot be approved from current status")
        item_type = str(item.get("item_type") or "general")
        if item_type == "agents_entry":
            for other in self.store.list_items(scope, status="approved"):
                if other["id"] != item_id and str(other.get("item_type") or "") == "agents_entry":
                    raise ConflictError("project already has an approved agents_entry")
        if item_type == "skill":
            name = str(item.get("name") or "").strip()
            for other in self.store.list_items(scope, status="approved"):
                if (
                    other["id"] != item_id
                    and str(other.get("item_type") or "") == "skill"
                    and str(other.get("name") or "").strip() == name
                ):
                    raise ConflictError(f"approved skill name already exists: {name}")
        item["status"] = "approved"
        item["approved_by"] = actor_id
        item["updated_at"] = _now()
        self.store.put_item(item)
        self.store.append_event(
            {"event_type": "common_item.approved", "item_id": item_id, "item_type": item_type}
        )
        return item

    def suppress_item(self, scope: Scope, item_id: str, actor_id: str, reason: str = "") -> dict[str, Any]:
        item = self.store.get_item(item_id, scope)
        if item["status"] == "suppressed":
            return item
        if item["status"] in {"archived", "deprecated"}:
            raise ConflictError("item cannot be suppressed from current status")
        item["status"] = "suppressed"
        item["suppressed_by"] = actor_id
        item["suppress_reason"] = reason.strip()
        item["updated_at"] = _now()
        self.store.put_item(item)
        self.store.append_event(
            {"event_type": "common_item.suppressed", "item_id": item_id, "reason": item["suppress_reason"]}
        )
        return item

    def reject_item(self, scope: Scope, item_id: str, actor_id: str, reason: str = "") -> dict[str, Any]:
        item = self.store.get_item(item_id, scope)
        if item["status"] == "rejected":
            return item
        if item["status"] not in {"proposed", "under_review"}:
            raise ConflictError("item cannot be rejected from current status")
        item["status"] = "rejected"
        item["rejected_by"] = actor_id
        item["reject_reason"] = reason.strip()
        item["updated_at"] = _now()
        self.store.put_item(item)
        self.store.append_event(
            {"event_type": "common_item.rejected", "item_id": item_id, "reason": item["reject_reason"]}
        )
        return item

    def resolve_bundle(self, scope: Scope, token_budget: int = 800) -> dict[str, Any]:
        if token_budget < 1:
            raise ValidationError("token_budget must be >= 1")
        approved = [i for i in self.store.list_items(scope, status="approved")]
        approved.sort(key=lambda i: i["score"], reverse=True)
        included: list[dict[str, Any]] = []
        used = 0
        for item in approved:
            cost = _token_estimate(item["body"])
            if used + cost > token_budget:
                continue
            included.append(
                {
                    "id": item["id"],
                    "title": item["title"],
                    "body": item["body"],
                    "score": item["score"],
                    "item_type": item.get("item_type") or "general",
                }
            )
            used += cost
        return {
            "project_id": scope.project_id,
            "token_budget": token_budget,
            "tokens_used": used,
            "included": included,
            "omitted_count": max(0, len(approved) - len(included)),
            "selection_reason": "score_desc_within_token_budget",
        }

    def _layer_scopes(
        self, resolve_scope: Scope, *, user_id: str | None
    ) -> list[tuple[str, Scope]]:
        layers: list[tuple[str, Scope]] = [
            ("org", org_scope(resolve_scope.tenant_id, resolve_scope.workspace_id)),
            ("project", project_scope(resolve_scope.tenant_id, resolve_scope.workspace_id, resolve_scope.project_id)),
        ]
        uid = (user_id or "").strip()
        if uid:
            layers.append(("user", user_scope(resolve_scope.tenant_id, resolve_scope.workspace_id, uid)))
        return layers

    def _load_layered_guidance(
        self,
        resolve_scope: Scope,
        *,
        user_id: str | None,
        include_general_common_context: bool,
    ) -> tuple[list[tuple[str, dict[str, Any]]], list[str]]:
        layered: list[tuple[str, dict[str, Any]]] = []
        considered: list[str] = []
        for layer, layer_scope in self._layer_scopes(resolve_scope, user_id=user_id):
            considered.append(layer)
            for item in self.store.list_items(layer_scope, status="approved"):
                kind = str(item.get("item_type") or "general")
                if kind in GUIDANCE_KINDS or (include_general_common_context and kind == "general"):
                    layered.append((layer, item))
        return layered, considered

    def resolve_guidance(
        self,
        scope: Scope,
        *,
        task_summary: str = "",
        workflow_type: str = "coding",
        include_skill_bodies: bool = False,
        budget_overrides: dict[str, Any] | None = None,
        include_general_common_context: bool = False,
        user_id: str | None = None,
        task_overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        _ = workflow_type
        budgets = {
            "entry_budget": DEFAULT_ENTRY_BUDGET,
            "always_rules_budget": DEFAULT_ALWAYS_RULES_BUDGET,
            "skill_catalog_budget": DEFAULT_SKILL_CATALOG_BUDGET,
        }
        if budget_overrides:
            for key, value in budget_overrides.items():
                if key in budgets:
                    budgets[key] = max(1, int(value))
        overrides = _normalize_task_overrides(task_overrides)

        resolve_scope = project_scope(scope.tenant_id, scope.workspace_id, scope.project_id)
        uid = (user_id or scope.user_id or "").strip() or None
        layered, layers_considered = self._load_layered_guidance(
            resolve_scope,
            user_id=uid,
            include_general_common_context=include_general_common_context,
        )

        entry_candidates = [(layer, i) for layer, i in layered if str(i.get("item_type") or "") == "agents_entry"]
        rule_candidates = [(layer, i) for layer, i in layered if str(i.get("item_type") or "") == "always_rule"]
        skill_candidates = [(layer, i) for layer, i in layered if str(i.get("item_type") or "") == "skill"]

        conflicts: list[dict[str, Any]] = []
        agents_entry = None
        token_estimate = 0
        suppressed: list[dict[str, Any]] = []

        # agents_entry: project wins over org; user never authors entry
        entry_by_layer: dict[str, list[dict[str, Any]]] = {"project": [], "org": []}
        for layer, item in entry_candidates:
            if layer in entry_by_layer:
                entry_by_layer[layer].append(item)
        chosen_entry = None
        chosen_layer = None
        for layer in ("project", "org"):
            entries = entry_by_layer[layer]
            if not entries:
                continue
            if len(entries) > 1:
                conflicts.append(
                    {
                        "reason_code": "multiple_agents_entry",
                        "layer": layer,
                        "item_ids": [e["id"] for e in entries],
                    }
                )
            entries.sort(key=lambda i: (-float(i.get("score") or 0), i["id"]))
            chosen_entry = entries[0]
            chosen_layer = layer
            for extra in entries[1:]:
                suppressed.append({"item_id": extra["id"], "reason_code": "duplicate_agents_entry", "layer": layer})
            break
        if chosen_entry is not None and chosen_layer is not None:
            cost = _token_estimate(chosen_entry["body"])
            if cost <= budgets["entry_budget"]:
                agents_entry = {
                    "item_id": chosen_entry["id"],
                    "version": int(chosen_entry.get("version") or 1),
                    "title": chosen_entry["title"],
                    "body": chosen_entry["body"],
                    "layer": chosen_layer,
                    "token_estimate": cost,
                }
                token_estimate += cost
            else:
                suppressed.append(
                    {
                        "item_id": chosen_entry["id"],
                        "reason_code": "budget_exceeded",
                        "layer": chosen_layer,
                    }
                )

        merged_rules, rule_conflicts = _merge_by_key(rule_candidates, key_fn=_rule_key)
        conflicts.extend(rule_conflicts)
        query = task_summary.strip().lower()
        merged_rules.sort(
            key=lambda i: (
                -int(bool(i.get("mandatory"))),
                -int(i.get("priority") or 0),
                -float(i.get("score") or 0),
                i["id"],
            )
        )
        always_rules: list[dict[str, Any]] = []
        rules_used = 0
        for rule in merged_rules:
            cost = _token_estimate(rule["body"])
            if rules_used + cost > budgets["always_rules_budget"]:
                suppressed.append(
                    {
                        "item_id": rule["id"],
                        "reason_code": "budget_exceeded",
                        "layer": _item_layer(rule),
                    }
                )
                continue
            reason = "applicability_match"
            if query and rule.get("body") and query not in str(rule.get("body")).lower():
                reason = "always_on"
            always_rules.append(
                {
                    "item_id": rule["id"],
                    "version": int(rule.get("version") or 1),
                    "title": rule["title"],
                    "body": rule["body"],
                    "slug": rule.get("slug"),
                    "priority": int(rule.get("priority") or 0),
                    "mandatory": bool(rule.get("mandatory")),
                    "layer": _item_layer(rule),
                    "reason_code": reason,
                    "token_estimate": cost,
                }
            )
            rules_used += cost
            token_estimate += cost

        if overrides["suppress_rule_slugs"]:
            kept_rules: list[dict[str, Any]] = []
            for rule in always_rules:
                slug = str(rule.get("slug") or "").strip()
                if slug and slug in overrides["suppress_rule_slugs"]:
                    if rule.get("mandatory"):
                        conflicts.append(
                            {
                                "reason_code": "task_override_blocked",
                                "item_id": rule["item_id"],
                                "slug": slug,
                                "layer": rule.get("layer"),
                            }
                        )
                        kept_rules.append(rule)
                    else:
                        suppressed.append(
                            {
                                "item_id": rule["item_id"],
                                "reason_code": "task_override",
                                "layer": rule.get("layer"),
                                "slug": slug,
                            }
                        )
                        token_estimate -= int(rule.get("token_estimate") or 0)
                else:
                    kept_rules.append(rule)
            always_rules = kept_rules

        merged_skills, skill_conflicts = _merge_by_key(skill_candidates, key_fn=_skill_key)
        conflicts.extend(skill_conflicts)
        merged_skills.sort(key=lambda i: (-float(i.get("score") or 0), str(i.get("name") or ""), i["id"]))
        skill_catalog: list[dict[str, Any]] = []
        catalog_used = 0
        for skill in merged_skills:
            descriptor = {
                "item_id": skill["id"],
                "name": skill.get("name"),
                "description": skill.get("description") or skill["title"],
                "version": int(skill.get("version") or 1),
                "when_to_use": skill.get("when_to_use") or [],
                "layer": _item_layer(skill),
                "reason_code": "catalog_match",
            }
            if include_skill_bodies:
                descriptor["body"] = skill["body"]
            cost = _token_estimate(str(descriptor.get("description") or "") + str(descriptor.get("name") or ""))
            if include_skill_bodies:
                cost += _token_estimate(skill["body"])
            if catalog_used + cost > budgets["skill_catalog_budget"]:
                suppressed.append(
                    {
                        "item_id": skill["id"],
                        "reason_code": "budget_exceeded",
                        "layer": _item_layer(skill),
                    }
                )
                continue
            skill_catalog.append(descriptor)
            catalog_used += cost
            token_estimate += cost

        if overrides["suppress_skill_names"]:
            kept_skills: list[dict[str, Any]] = []
            for skill in skill_catalog:
                name = str(skill.get("name") or "").strip()
                if name and name in overrides["suppress_skill_names"]:
                    suppressed.append(
                        {
                            "item_id": skill["item_id"],
                            "reason_code": "task_override",
                            "layer": skill.get("layer"),
                            "name": name,
                        }
                    )
                else:
                    kept_skills.append(skill)
            skill_catalog = kept_skills

        empty_reason = None
        if agents_entry is None and not always_rules and not skill_catalog:
            empty_reason = "no_approved_guidance"

        bundle_id = _new_id("bnd")
        audit_id = _new_id("aud")
        bundle = {
            "bundle_id": bundle_id,
            "schema_version": "1.0",
            "project_id": resolve_scope.project_id,
            "user_id": uid,
            "layers_considered": layers_considered,
            "resolved_at": _now(),
            "agents_entry": agents_entry,
            "always_rules": always_rules,
            "skills": skill_catalog,
            "suppressed_items": suppressed,
            "conflicts": conflicts,
            "token_estimate": max(0, token_estimate),
            "audit_record_id": audit_id,
            "empty_reason": empty_reason,
            "budgets": budgets,
            "task_summary": task_summary or None,
            "task_overrides": {
                "suppress_rule_slugs": sorted(overrides["suppress_rule_slugs"]),
                "suppress_skill_names": sorted(overrides["suppress_skill_names"]),
            }
            if (overrides["suppress_rule_slugs"] or overrides["suppress_skill_names"])
            else None,
        }
        self.store.append_event(
            {
                "event_type": "AgentWorkspaceGuidanceBundleResolved",
                "bundle_id": bundle_id,
                "project_id": resolve_scope.project_id,
                "user_id": uid,
                "layers_considered": layers_considered,
                "audit_record_id": audit_id,
                "counts": {
                    "always_rules": len(always_rules),
                    "skills": len(skill_catalog),
                    "suppressed": len(suppressed),
                    "conflicts": len(conflicts),
                },
            }
        )
        return bundle

    def list_skills(
        self,
        scope: Scope,
        query: str = "",
        *,
        user_id: str | None = None,
    ) -> list[dict[str, Any]]:
        resolve_scope = project_scope(scope.tenant_id, scope.workspace_id, scope.project_id)
        uid = (user_id or scope.user_id or "").strip() or None
        layered, _ = self._load_layered_guidance(
            resolve_scope, user_id=uid, include_general_common_context=False
        )
        skill_candidates = [(layer, i) for layer, i in layered if str(i.get("item_type") or "") == "skill"]
        merged, _ = _merge_by_key(skill_candidates, key_fn=_skill_key)
        q = query.strip().lower()
        out: list[dict[str, Any]] = []
        for skill in merged:
            name = str(skill.get("name") or "")
            description = str(skill.get("description") or skill.get("title") or "")
            when = skill.get("when_to_use") or []
            hay = " ".join([name, description, " ".join(str(x) for x in when)]).lower()
            if q and q not in hay:
                continue
            out.append(
                {
                    "item_id": skill["id"],
                    "name": name,
                    "description": description,
                    "version": int(skill.get("version") or 1),
                    "when_to_use": when,
                    "layer": _item_layer(skill),
                    "reason_code": "catalog_match",
                }
            )
        out.sort(key=lambda s: s["name"] or "")
        return out

    def get_skill(
        self,
        scope: Scope,
        *,
        skill_id: str | None = None,
        name: str | None = None,
        bundle_id: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        sid = (skill_id or "").strip()
        sname = (name or "").strip()
        if not sid and not sname:
            raise ValidationError("skill_id or name is required")
        resolve_scope = project_scope(scope.tenant_id, scope.workspace_id, scope.project_id)
        uid = (user_id or scope.user_id or "").strip() or None
        layered, _ = self._load_layered_guidance(
            resolve_scope, user_id=uid, include_general_common_context=False
        )
        skill_candidates = [(layer, i) for layer, i in layered if str(i.get("item_type") or "") == "skill"]
        merged, _ = _merge_by_key(skill_candidates, key_fn=_skill_key)
        item = None
        if sid:
            for candidate in merged:
                if candidate["id"] == sid:
                    item = candidate
                    break
            if item is None:
                # Fallback: id may exist on a layer but lost merge race — still allow fetch by id
                for layer, layer_scope in self._layer_scopes(resolve_scope, user_id=uid):
                    _ = layer
                    try:
                        found = self.store.get_item(sid, layer_scope)
                    except NotFoundError:
                        continue
                    if str(found.get("item_type") or "") == "skill" and found.get("status") == "approved":
                        item = found
                        break
        else:
            matches = [i for i in merged if str(i.get("name") or "") == sname]
            if matches:
                item = matches[0]
        if item is None or str(item.get("item_type") or "") != "skill" or item.get("status") != "approved":
            raise NotFoundError("skill not found")
        result = {
            "item_id": item["id"],
            "name": item.get("name"),
            "version": int(item.get("version") or 1),
            "body": item["body"],
            "content_hash": f"sha256:{len(item['body'])}:{item['id']}",
            "description": item.get("description") or item.get("title"),
            "when_to_use": item.get("when_to_use") or [],
            "layer": _item_layer(item),
        }
        self.store.append_event(
            {
                "event_type": "AgentWorkspaceGuidanceSkillFetched",
                "item_id": item["id"],
                "name": item.get("name"),
                "bundle_id": bundle_id,
                "project_id": resolve_scope.project_id,
                "layer": result["layer"],
            }
        )
        return result

    def ensure_mcp_first_seed(self, scope: Scope, actor_id: str, correlation_id: str) -> dict[str, Any]:
        """Idempotently seed MCP-first guidance pack when no approved guidance exists."""
        seed_scope = (
            scope
            if scope.scope_kind in {"org", "project"}
            else project_scope(scope.tenant_id, scope.workspace_id, scope.project_id)
        )
        approved = self.store.list_items(seed_scope, status="approved")
        has_guidance = any(str(i.get("item_type") or "") in GUIDANCE_KINDS for i in approved)
        if has_guidance:
            return {"seeded": False, "reason": "guidance_already_present", "item_ids": []}

        all_items = self.store.list_items(seed_scope)
        if any(str(i.get("item_type") or "") in GUIDANCE_KINDS for i in all_items):
            return {"seeded": False, "reason": "guidance_items_exist", "item_ids": []}

        item_ids: list[str] = []
        seed_key = seed_scope.project_id if seed_scope.scope_kind == "project" else f"org:{seed_scope.workspace_id}"
        for index, payload in enumerate(mcp_first_seed_payloads()):
            item = self.propose_item(
                seed_scope,
                actor_id,
                correlation_id,
                f"awg-seed-mcp-first:{seed_key}:{index}:{payload.get('item_type')}:{payload.get('name') or payload.get('slug') or 'entry'}",
                payload,
            )
            approved_item = self.approve_item(seed_scope, item["id"], actor_id)
            item_ids.append(approved_item["id"])
        self.store.append_event(
            {
                "event_type": "AgentWorkspaceGuidanceSeedApplied",
                "project_id": seed_scope.project_id,
                "scope_kind": seed_scope.scope_kind,
                "seed_pack": "awg-seed-mcp-first-programming",
                "item_ids": item_ids,
            }
        )
        return {
            "seeded": True,
            "reason": "applied",
            "item_ids": item_ids,
            "seed_pack": "awg-seed-mcp-first-programming",
            "scope_kind": seed_scope.scope_kind,
        }

    def export_guidance_layout(
        self,
        scope: Scope,
        *,
        layout: str = "cursor",
        dry_run: bool = True,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Return planned filesystem paths for approved guidance (dry-run export)."""
        if layout not in {"cursor", "claude_compatible", "generic_agents_md"}:
            raise ValidationError("layout must be cursor, claude_compatible, or generic_agents_md")
        _ = dry_run  # write path deferred; always plan-only in this slice
        resolve_scope = project_scope(scope.tenant_id, scope.workspace_id, scope.project_id)
        uid = (user_id or scope.user_id or "").strip() or None
        layered, _ = self._load_layered_guidance(
            resolve_scope, user_id=uid, include_general_common_context=False
        )
        # Export project+org winners (user personal pack is session-only; exclude from disk export)
        exportable = [(layer, i) for layer, i in layered if layer in {"org", "project"}]
        entry_merged = [i for layer, i in exportable if str(i.get("item_type")) == "agents_entry" and layer == "project"]
        if not entry_merged:
            entry_merged = [i for layer, i in exportable if str(i.get("item_type")) == "agents_entry" and layer == "org"]
        rules, _ = _merge_by_key(
            [(layer, i) for layer, i in exportable if str(i.get("item_type")) == "always_rule"],
            key_fn=_rule_key,
        )
        skills, _ = _merge_by_key(
            [(layer, i) for layer, i in exportable if str(i.get("item_type")) == "skill"],
            key_fn=_skill_key,
        )
        approved = entry_merged + rules + skills
        planned: list[dict[str, Any]] = []
        for item in approved:
            kind = str(item.get("item_type"))
            path = None
            if kind == "agents_entry":
                path = "AGENTS.md" if layout != "claude_compatible" else "AGENTS.md"
            elif kind == "always_rule":
                slug = str(item.get("slug") or item.get("title") or item["id"]).lower()
                slug = "".join(c if c.isalnum() or c in "-_" else "-" for c in slug).strip("-") or item["id"]
                if layout == "cursor":
                    path = f".cursor/rules/{slug}.mdc"
                else:
                    path = f".agent/rules/{slug}.md"
            elif kind == "skill":
                name = str(item.get("name") or item["id"])
                if layout == "cursor":
                    path = f".cursor/skills/{name}/SKILL.md"
                else:
                    path = f".agents/skills/{name}/SKILL.md"
            if path:
                planned.append(
                    {
                        "item_id": item["id"],
                        "item_type": kind,
                        "path": path,
                        "layer": _item_layer(item),
                        "action": "create_or_update_managed",
                    }
                )
        export_id = _new_id("exp")
        result = {
            "export_id": export_id,
            "layout": layout,
            "dry_run": True,
            "written": [],
            "skipped": [],
            "conflicts": [],
            "planned": planned,
            "audit_record_id": _new_id("aud"),
        }
        self.store.append_event(
            {
                "event_type": "AgentWorkspaceGuidanceExported",
                "export_id": export_id,
                "project_id": resolve_scope.project_id,
                "layout": layout,
                "planned_count": len(planned),
            }
        )
        return result
