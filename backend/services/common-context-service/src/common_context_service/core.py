from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import uuid4

from .seed_mcp_first import mcp_first_seed_payloads

GUIDANCE_KINDS = frozenset({"agents_entry", "always_rule", "skill"})
ITEM_TYPES = GUIDANCE_KINDS | frozenset({"general"})

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

    def __post_init__(self) -> None:
        if not all((self.tenant_id.strip(), self.workspace_id.strip(), self.project_id.strip())):
            raise ValidationError("tenant_id, workspace_id, and project_id are required")


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def _token_estimate(text: str) -> int:
    return max(20, len(text) // 4)


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
            "mandatory": bool(payload.get("mandatory") or False),
            "applicability": payload.get("applicability"),
            "created_by": actor_id,
            "correlation_id": correlation_id,
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.put_item(item)
        self.store.complete_idempotency(scope, idempotency_key, "common_item", item_id)
        self.store.append_event(
            {"event_type": "common_item.proposed", "item_id": item_id, "item_type": item_type}
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

    def resolve_guidance(
        self,
        scope: Scope,
        *,
        task_summary: str = "",
        workflow_type: str = "coding",
        include_skill_bodies: bool = False,
        budget_overrides: dict[str, Any] | None = None,
        include_general_common_context: bool = False,
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

        approved = self.store.list_items(scope, status="approved")
        guidance = [
            i
            for i in approved
            if str(i.get("item_type") or "general") in GUIDANCE_KINDS
            or (include_general_common_context and str(i.get("item_type") or "general") == "general")
        ]

        entries = [i for i in guidance if str(i.get("item_type") or "") == "agents_entry"]
        rules = [i for i in guidance if str(i.get("item_type") or "") == "always_rule"]
        skills = [i for i in guidance if str(i.get("item_type") or "") == "skill"]

        conflicts: list[dict[str, Any]] = []
        agents_entry = None
        token_estimate = 0
        suppressed: list[dict[str, Any]] = []

        if len(entries) > 1:
            conflicts.append(
                {
                    "reason_code": "multiple_agents_entry",
                    "item_ids": [e["id"] for e in entries],
                }
            )
        if entries:
            # Deterministic: highest score, then id
            entries.sort(key=lambda i: (-float(i.get("score") or 0), i["id"]))
            chosen = entries[0]
            cost = _token_estimate(chosen["body"])
            if cost <= budgets["entry_budget"]:
                agents_entry = {
                    "item_id": chosen["id"],
                    "version": int(chosen.get("version") or 1),
                    "title": chosen["title"],
                    "body": chosen["body"],
                    "token_estimate": cost,
                }
                token_estimate += cost
            else:
                suppressed.append({"item_id": chosen["id"], "reason_code": "budget_exceeded"})
            for extra in entries[1:]:
                suppressed.append({"item_id": extra["id"], "reason_code": "duplicate_agents_entry"})

        query = task_summary.strip().lower()
        rules.sort(
            key=lambda i: (
                -int(bool(i.get("mandatory"))),
                -int(i.get("priority") or 0),
                -float(i.get("score") or 0),
                i["id"],
            )
        )
        always_rules: list[dict[str, Any]] = []
        rules_used = 0
        for rule in rules:
            cost = _token_estimate(rule["body"])
            if rules_used + cost > budgets["always_rules_budget"]:
                suppressed.append({"item_id": rule["id"], "reason_code": "budget_exceeded"})
                continue
            reason = "applicability_match"
            if query and rule.get("body") and query not in str(rule.get("body")).lower():
                # Still include always-on rules; soft signal only
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
                    "reason_code": reason,
                    "token_estimate": cost,
                }
            )
            rules_used += cost
            token_estimate += cost

        skills.sort(key=lambda i: (-float(i.get("score") or 0), str(i.get("name") or ""), i["id"]))
        skill_catalog: list[dict[str, Any]] = []
        catalog_used = 0
        for skill in skills:
            descriptor = {
                "item_id": skill["id"],
                "name": skill.get("name"),
                "description": skill.get("description") or skill["title"],
                "version": int(skill.get("version") or 1),
                "when_to_use": skill.get("when_to_use") or [],
                "reason_code": "catalog_match",
            }
            if include_skill_bodies:
                descriptor["body"] = skill["body"]
            cost = _token_estimate(str(descriptor.get("description") or "") + str(descriptor.get("name") or ""))
            if include_skill_bodies:
                cost += _token_estimate(skill["body"])
            if catalog_used + cost > budgets["skill_catalog_budget"]:
                suppressed.append({"item_id": skill["id"], "reason_code": "budget_exceeded"})
                continue
            skill_catalog.append(descriptor)
            catalog_used += cost
            token_estimate += cost

        empty_reason = None
        if agents_entry is None and not always_rules and not skill_catalog:
            empty_reason = "no_approved_guidance"

        bundle_id = _new_id("bnd")
        audit_id = _new_id("aud")
        bundle = {
            "bundle_id": bundle_id,
            "schema_version": "1.0",
            "project_id": scope.project_id,
            "resolved_at": _now(),
            "agents_entry": agents_entry,
            "always_rules": always_rules,
            "skills": skill_catalog,
            "suppressed_items": suppressed,
            "conflicts": conflicts,
            "token_estimate": token_estimate,
            "audit_record_id": audit_id,
            "empty_reason": empty_reason,
            "budgets": budgets,
            "task_summary": task_summary or None,
        }
        self.store.append_event(
            {
                "event_type": "AgentWorkspaceGuidanceBundleResolved",
                "bundle_id": bundle_id,
                "project_id": scope.project_id,
                "audit_record_id": audit_id,
                "counts": {
                    "always_rules": len(always_rules),
                    "skills": len(skill_catalog),
                    "suppressed": len(suppressed),
                },
            }
        )
        return bundle

    def list_skills(self, scope: Scope, query: str = "") -> list[dict[str, Any]]:
        q = query.strip().lower()
        skills = [
            i
            for i in self.store.list_items(scope, status="approved")
            if str(i.get("item_type") or "") == "skill"
        ]
        out: list[dict[str, Any]] = []
        for skill in skills:
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
    ) -> dict[str, Any]:
        sid = (skill_id or "").strip()
        sname = (name or "").strip()
        if not sid and not sname:
            raise ValidationError("skill_id or name is required")
        if sid:
            item = self.store.get_item(sid, scope)
            if str(item.get("item_type") or "") != "skill" or item.get("status") != "approved":
                raise NotFoundError("skill not found")
        else:
            matches = [
                i
                for i in self.store.list_items(scope, status="approved")
                if str(i.get("item_type") or "") == "skill" and str(i.get("name") or "") == sname
            ]
            if not matches:
                raise NotFoundError("skill not found")
            item = matches[0]
        result = {
            "item_id": item["id"],
            "name": item.get("name"),
            "version": int(item.get("version") or 1),
            "body": item["body"],
            "content_hash": f"sha256:{len(item['body'])}:{item['id']}",
            "description": item.get("description") or item.get("title"),
            "when_to_use": item.get("when_to_use") or [],
        }
        self.store.append_event(
            {
                "event_type": "AgentWorkspaceGuidanceSkillFetched",
                "item_id": item["id"],
                "name": item.get("name"),
                "bundle_id": bundle_id,
                "project_id": scope.project_id,
            }
        )
        return result

    def ensure_mcp_first_seed(self, scope: Scope, actor_id: str, correlation_id: str) -> dict[str, Any]:
        """Idempotently seed MCP-first guidance pack when no approved guidance exists."""
        approved = self.store.list_items(scope, status="approved")
        has_guidance = any(str(i.get("item_type") or "") in GUIDANCE_KINDS for i in approved)
        if has_guidance:
            return {"seeded": False, "reason": "guidance_already_present", "item_ids": []}

        # Also skip if proposed guidance already exists (avoid duplicate proposes)
        all_items = self.store.list_items(scope)
        if any(str(i.get("item_type") or "") in GUIDANCE_KINDS for i in all_items):
            return {"seeded": False, "reason": "guidance_items_exist", "item_ids": []}

        item_ids: list[str] = []
        for index, payload in enumerate(mcp_first_seed_payloads()):
            item = self.propose_item(
                scope,
                actor_id,
                correlation_id,
                f"awg-seed-mcp-first:{scope.project_id}:{index}:{payload.get('item_type')}:{payload.get('name') or payload.get('slug') or 'entry'}",
                payload,
            )
            approved_item = self.approve_item(scope, item["id"], actor_id)
            item_ids.append(approved_item["id"])
        self.store.append_event(
            {
                "event_type": "AgentWorkspaceGuidanceSeedApplied",
                "project_id": scope.project_id,
                "seed_pack": "awg-seed-mcp-first-programming",
                "item_ids": item_ids,
            }
        )
        return {"seeded": True, "reason": "applied", "item_ids": item_ids, "seed_pack": "awg-seed-mcp-first-programming"}

    def export_guidance_layout(
        self,
        scope: Scope,
        *,
        layout: str = "cursor",
        dry_run: bool = True,
    ) -> dict[str, Any]:
        """Return planned filesystem paths for approved guidance (dry-run export)."""
        if layout not in {"cursor", "claude_compatible", "generic_agents_md"}:
            raise ValidationError("layout must be cursor, claude_compatible, or generic_agents_md")
        _ = dry_run  # write path deferred; always plan-only in this slice
        approved = [
            i
            for i in self.store.list_items(scope, status="approved")
            if str(i.get("item_type") or "") in GUIDANCE_KINDS
        ]
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
                "project_id": scope.project_id,
                "layout": layout,
                "planned_count": len(planned),
            }
        )
        return result
