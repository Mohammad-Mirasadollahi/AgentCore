from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
import json
import re
from typing import Any, Protocol
from uuid import uuid4


class ConnectorState(StrEnum):
    PENDING = "pending_configuration"
    VALIDATING = "validating"
    READY = "ready"
    DEGRADED = "degraded"
    DISABLED = "disabled"
    FAILED = "failed"
    REVOKED = "revoked"


class DeliveryState(StrEnum):
    PENDING = "pending"
    DELIVERED = "delivered"
    RETRYING = "retrying"
    DEAD_LETTERED = "dead_lettered"


class SubscriptionState(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class TicketState(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELED = "canceled"


class MappingState(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"


REQUIRED_MESSAGE_FIELDS = (
    "message_id",
    "schema_version",
    "sender",
    "sender_type",
    "tenant_id",
    "project_id",
    "intent",
    "domain",
    "payload",
    "status",
    "refs",
    "correlation_id",
    "created_at",
)

ALLOWED_INTENTS = {
    "TASK_STARTED",
    "TASK_COMPLETED",
    "TASK_BLOCKED",
    "API_READY",
    "DOC_DRIFT_FOUND",
    "TEST_FAILURE_DETECTED",
    "HUMAN_APPROVAL_REQUIRED",
    "APPROVAL_RESOLVED",
    "DEPLOYMENT_COMPLETED",
    "DOWNSTREAM_TASK_REQUESTED",
    "CODE_RELEASED",
}

DEPARTMENT_TRIGGERS = {
    "CODE_RELEASED": ("marketing", "support", "devops"),
    "DEPLOYMENT_COMPLETED": ("support", "devops"),
    "API_READY": ("frontend", "docs"),
}


class AdapterError(Exception):
    def __init__(self, code: str, category: str, message: str):
        super().__init__(message)
        self.code, self.category, self.message = code, category, message


class ValidationError(AdapterError):
    def __init__(self, message: str):
        super().__init__("validation_error", "validation_error", message)


class ConflictError(AdapterError):
    def __init__(self, message: str):
        super().__init__("conflict_error", "conflict_error", message)


class NotFoundError(AdapterError):
    def __init__(self, message: str):
        super().__init__("not_found", "not_found_error", message)


@dataclass(frozen=True)
class Scope:
    tenant_id: str
    workspace_id: str
    project_id: str
    project_group_id: str | None = None

    def __post_init__(self) -> None:
        if not all((self.tenant_id.strip(), self.workspace_id.strip(), self.project_id.strip())):
            raise ValidationError("tenant_id, workspace_id, and project_id are required")


@dataclass
class Connector:
    id: str
    scope: Scope
    actor_id: str
    correlation_id: str
    vendor: str
    name: str
    capabilities: list[str]
    auth_profile: str
    trust_level: str
    status: ConnectorState
    credential_fingerprint: str
    created_at: str
    updated_at: str
    version: int = 1

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.scope.tenant_id,
            "workspace_id": self.scope.workspace_id,
            "project_id": self.scope.project_id,
            "actor_id": self.actor_id,
            "correlation_id": self.correlation_id,
            "vendor": self.vendor,
            "name": self.name,
            "capabilities": self.capabilities,
            "auth_profile": self.auth_profile,
            "trust_level": self.trust_level,
            "status": self.status.value,
            "credential_fingerprint": self.credential_fingerprint,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class AdapterMapping:
    id: str
    scope: Scope
    connector_id: str
    vendor_schema_version: str
    field_map: dict[str, str]
    status: MappingState
    created_at: str
    updated_at: str
    version: int = 1

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.scope.tenant_id,
            "workspace_id": self.scope.workspace_id,
            "project_id": self.scope.project_id,
            "connector_id": self.connector_id,
            "vendor_schema_version": self.vendor_schema_version,
            "field_map": self.field_map,
            "status": self.status.value,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class Subscription:
    id: str
    scope: Scope
    actor_id: str
    correlation_id: str
    channel: str
    subscriber_type: str
    endpoint: str
    filter_intents: list[str]
    filter_domains: list[str]
    status: SubscriptionState
    fail_mode: str
    created_at: str
    updated_at: str
    version: int = 1

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.scope.tenant_id,
            "workspace_id": self.scope.workspace_id,
            "project_id": self.scope.project_id,
            "actor_id": self.actor_id,
            "correlation_id": self.correlation_id,
            "channel": self.channel,
            "subscriber_type": self.subscriber_type,
            "endpoint": self.endpoint,
            "filter_intents": self.filter_intents,
            "filter_domains": self.filter_domains,
            "status": self.status.value,
            "fail_mode": self.fail_mode,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class BrokerEvent:
    id: str
    scope: Scope
    channel: str
    message: dict[str, Any]
    created_at: str

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.scope.tenant_id,
            "workspace_id": self.scope.workspace_id,
            "project_id": self.scope.project_id,
            "channel": self.channel,
            "message": self.message,
            "created_at": self.created_at,
        }


@dataclass
class Delivery:
    id: str
    scope: Scope
    event_id: str
    subscription_id: str
    status: DeliveryState
    attempts: int
    last_error: str | None
    created_at: str
    updated_at: str

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.scope.tenant_id,
            "workspace_id": self.scope.workspace_id,
            "project_id": self.scope.project_id,
            "event_id": self.event_id,
            "subscription_id": self.subscription_id,
            "status": self.status.value,
            "attempts": self.attempts,
            "last_error": self.last_error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class DeadLetterRecord:
    id: str
    scope: Scope
    event_id: str
    subscription_id: str
    reason: str
    message: dict[str, Any]
    created_at: str

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.scope.tenant_id,
            "workspace_id": self.scope.workspace_id,
            "project_id": self.scope.project_id,
            "event_id": self.event_id,
            "subscription_id": self.subscription_id,
            "reason": self.reason,
            "message": self.message,
            "created_at": self.created_at,
        }


@dataclass
class ExternalTicket:
    id: str
    scope: Scope
    actor_id: str
    correlation_id: str
    connector_id: str
    external_ref: str
    title: str
    status: TicketState
    department: str
    source_event_id: str | None
    evidence_refs: list[str]
    created_at: str
    updated_at: str
    version: int = 1

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.scope.tenant_id,
            "workspace_id": self.scope.workspace_id,
            "project_id": self.scope.project_id,
            "actor_id": self.actor_id,
            "correlation_id": self.correlation_id,
            "connector_id": self.connector_id,
            "external_ref": self.external_ref,
            "title": self.title,
            "status": self.status.value,
            "department": self.department,
            "source_event_id": self.source_event_id,
            "evidence_refs": self.evidence_refs,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class DepartmentTask:
    id: str
    scope: Scope
    department: str
    title: str
    trigger_intent: str
    source_message_id: str
    approval_required: bool
    status: str
    created_at: str

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.scope.tenant_id,
            "workspace_id": self.scope.workspace_id,
            "project_id": self.scope.project_id,
            "department": self.department,
            "title": self.title,
            "trigger_intent": self.trigger_intent,
            "source_message_id": self.source_message_id,
            "approval_required": self.approval_required,
            "status": self.status,
            "created_at": self.created_at,
        }


class Store(Protocol):
    def get_connector(self, connector_id: str, scope: Scope) -> Connector: ...
    def put_connector(self, connector: Connector) -> None: ...
    def list_connectors(self, scope: Scope) -> list[Connector]: ...
    def put_mapping(self, mapping: AdapterMapping) -> None: ...
    def list_mappings(self, scope: Scope, connector_id: str | None = None) -> list[AdapterMapping]: ...
    def get_subscription(self, subscription_id: str, scope: Scope) -> Subscription: ...
    def put_subscription(self, subscription: Subscription) -> None: ...
    def list_subscriptions(self, scope: Scope) -> list[Subscription]: ...
    def put_event(self, event: BrokerEvent) -> None: ...
    def list_events(self, scope: Scope, channel: str | None = None) -> list[BrokerEvent]: ...
    def get_event(self, event_id: str, scope: Scope) -> BrokerEvent: ...
    def put_delivery(self, delivery: Delivery) -> None: ...
    def list_deliveries(self, scope: Scope) -> list[Delivery]: ...
    def put_dead_letter(self, record: DeadLetterRecord) -> None: ...
    def list_dead_letters(self, scope: Scope) -> list[DeadLetterRecord]: ...
    def get_ticket(self, ticket_id: str, scope: Scope) -> ExternalTicket: ...
    def put_ticket(self, ticket: ExternalTicket) -> None: ...
    def list_tickets(self, scope: Scope) -> list[ExternalTicket]: ...
    def put_department_task(self, task: DepartmentTask) -> None: ...
    def list_department_tasks(self, scope: Scope) -> list[DepartmentTask]: ...
    def idempotent(self, scope: Scope, command: str, key: str, payload: dict[str, Any]) -> str | None: ...
    def remember(self, scope: Scope, command: str, key: str, payload: dict[str, Any], record_id: str) -> None: ...
    def event(self, payload: dict[str, Any]) -> None: ...
    def outbox(self) -> list[dict[str, Any]]: ...


class AdapterService:
    def __init__(self, store: Store, max_delivery_attempts: int = 2):
        self.store = store
        self.max_delivery_attempts = max_delivery_attempts

    def register_connector(self, scope: Scope, actor: str, correlation_id: str, key: str, payload: dict[str, Any]) -> Connector:
        self._require_key(key)
        payload = sanitize(payload)
        missing = [field for field in ("vendor", "name", "capabilities", "auth_profile") if not payload.get(field)]
        if missing:
            raise ValidationError("missing required fields: " + ", ".join(missing))
        command_payload = {
            "vendor": payload["vendor"],
            "name": payload["name"],
            "capabilities": sorted(set(payload.get("capabilities") or [])),
            "auth_profile": payload["auth_profile"],
            "trust_level": payload.get("trust_level") or "standard",
            "credential": payload.get("credential") or "unset",
        }
        prior = self.store.idempotent(scope, "register_connector", key, command_payload)
        if prior:
            return self.store.get_connector(prior, scope)
        timestamp = now()
        connector = Connector(
            str(uuid4()),
            scope,
            actor,
            correlation_id,
            command_payload["vendor"],
            command_payload["name"],
            command_payload["capabilities"],
            command_payload["auth_profile"],
            command_payload["trust_level"],
            ConnectorState.PENDING,
            digest(command_payload["credential"]),
            timestamp,
            timestamp,
        )
        self.store.put_connector(connector)
        mapping = AdapterMapping(
            str(uuid4()),
            scope,
            connector.id,
            str(payload.get("vendor_schema_version") or "1.0.0"),
            dict(payload.get("field_map") or {"status": "status", "task_id": "refs.task_id"}),
            MappingState.ACTIVE,
            timestamp,
            timestamp,
        )
        self.store.put_mapping(mapping)
        self.store.remember(scope, "register_connector", key, command_payload, connector.id)
        self.emit("ConnectorRegistered", connector.public(), scope, actor, correlation_id, key, connector.id, [])
        return connector

    def validate_connector(self, scope: Scope, actor: str, correlation_id: str, key: str, connector_id: str) -> Connector:
        self._require_key(key)
        payload = {"connector_id": connector_id}
        prior = self.store.idempotent(scope, "validate_connector", key, payload)
        if prior:
            return self.store.get_connector(prior, scope)
        connector = self.store.get_connector(connector_id, scope)
        connector.status = ConnectorState.VALIDATING
        connector.updated_at = now()
        if not connector.capabilities:
            connector.status = ConnectorState.FAILED
            self.store.put_connector(connector)
            raise ValidationError("connector has no capabilities")
        if not connector.credential_fingerprint:
            connector.status = ConnectorState.FAILED
            self.store.put_connector(connector)
            raise ValidationError("connector credential is missing")
        connector.status = ConnectorState.READY
        connector.version += 1
        connector.updated_at = now()
        self.store.put_connector(connector)
        self.store.remember(scope, "validate_connector", key, payload, connector.id)
        self.emit("ConnectorValidated", connector.public(), scope, actor, correlation_id, key, connector.id, [])
        self.emit("CapabilityChanged", {"connector_id": connector.id, "capabilities": connector.capabilities}, scope, actor, correlation_id, key, connector.id, [])
        return connector

    def rotate_credential(self, scope: Scope, actor: str, correlation_id: str, key: str, connector_id: str, credential: str) -> Connector:
        self._require_key(key)
        if not credential:
            raise ValidationError("credential is required")
        payload = {"connector_id": connector_id, "credential": digest(credential)}
        prior = self.store.idempotent(scope, "rotate_credential", key, payload)
        if prior:
            return self.store.get_connector(prior, scope)
        connector = self.store.get_connector(connector_id, scope)
        connector.credential_fingerprint = payload["credential"]
        connector.version += 1
        connector.updated_at = now()
        if connector.status == ConnectorState.REVOKED:
            raise ConflictError("revoked connector cannot rotate credentials")
        self.store.put_connector(connector)
        self.store.remember(scope, "rotate_credential", key, payload, connector.id)
        return connector

    def subscribe(self, scope: Scope, actor: str, correlation_id: str, key: str, payload: dict[str, Any]) -> Subscription:
        self._require_key(key)
        payload = sanitize(payload)
        missing = [field for field in ("channel", "subscriber_type", "endpoint") if not payload.get(field)]
        if missing:
            raise ValidationError("missing required fields: " + ", ".join(missing))
        command_payload = {
            "channel": payload["channel"],
            "subscriber_type": payload["subscriber_type"],
            "endpoint": payload["endpoint"],
            "filter_intents": sorted(set(payload.get("filter_intents") or [])),
            "filter_domains": sorted(set(payload.get("filter_domains") or [])),
            "fail_mode": payload.get("fail_mode") or "none",
        }
        prior = self.store.idempotent(scope, "subscribe", key, command_payload)
        if prior:
            return self.store.get_subscription(prior, scope)
        timestamp = now()
        subscription = Subscription(
            str(uuid4()),
            scope,
            actor,
            correlation_id,
            command_payload["channel"],
            command_payload["subscriber_type"],
            command_payload["endpoint"],
            command_payload["filter_intents"],
            command_payload["filter_domains"],
            SubscriptionState.ACTIVE,
            command_payload["fail_mode"],
            timestamp,
            timestamp,
        )
        self.store.put_subscription(subscription)
        self.store.remember(scope, "subscribe", key, command_payload, subscription.id)
        return subscription

    def normalize_vendor_event(self, scope: Scope, actor: str, correlation_id: str, key: str, connector_id: str, vendor_payload: dict[str, Any]) -> dict[str, Any]:
        self._require_key(key)
        connector = self.store.get_connector(connector_id, scope)
        if connector.status != ConnectorState.READY:
            raise ConflictError("connector is not ready")
        mappings = self.store.list_mappings(scope, connector_id)
        mapping = next((item for item in mappings if item.status == MappingState.ACTIVE), None)
        if mapping is None:
            raise ValidationError("active adapter mapping is required")
        vendor_payload = sanitize(vendor_payload)
        command_payload = {"connector_id": connector_id, "vendor_payload": vendor_payload}
        prior = self.store.idempotent(scope, "normalize_vendor_event", key, command_payload)
        if prior:
            return {"message": json.loads(prior), "connector_id": connector_id}
        message = self._vendor_to_universal(scope, connector, mapping, vendor_payload, correlation_id)
        self.validate_message(message, scope)
        self.store.remember(scope, "normalize_vendor_event", key, command_payload, json.dumps(message, sort_keys=True))
        self.emit("AdapterNormalizedOutput", {"connector_id": connector_id, "message": message}, scope, actor, correlation_id, key, message["message_id"], message.get("refs") or [])
        return {"message": message, "connector_id": connector_id}

    def publish_agent_event(self, scope: Scope, actor: str, correlation_id: str, key: str, message: dict[str, Any]) -> dict[str, Any]:
        self._require_key(key)
        message = sanitize(message)
        command_payload = {"message": message}
        prior = self.store.idempotent(scope, "publish_agent_event", key, command_payload)
        if prior:
            event = self.store.get_event(prior, scope)
            return self._publish_result(event)
        validated = self.validate_message(message, scope)
        channel = channel_for(validated["intent"], validated["domain"])
        timestamp = now()
        event = BrokerEvent(str(uuid4()), scope, channel, validated, timestamp)
        self.store.put_event(event)
        self.store.remember(scope, "publish_agent_event", key, command_payload, event.id)
        self.emit("AgentEventReceived", event.public(), scope, actor, correlation_id, key, event.id, validated.get("refs") or [])
        self.emit("BrokerEventPublished", event.public(), scope, actor, correlation_id, key, event.id, validated.get("refs") or [])
        deliveries = self._deliver(scope, event)
        department_tasks = self._trigger_department_workflows(scope, validated, event.id)
        result = self._publish_result(event)
        result["deliveries"] = [item.public() for item in deliveries]
        result["department_tasks"] = [item.public() for item in department_tasks]
        return result

    def replay(self, scope: Scope, actor: str, correlation_id: str, key: str, channel: str | None = None) -> dict[str, Any]:
        self._require_key(key)
        payload = {"channel": channel}
        prior = self.store.idempotent(scope, "replay", key, payload)
        if prior:
            return json.loads(prior)
        events = self.store.list_events(scope, channel)
        replayed = []
        for event in events:
            deliveries = self._deliver(scope, event, replay=True)
            replayed.append({"event_id": event.id, "deliveries": [item.public() for item in deliveries]})
        result = {"replayed_count": len(replayed), "items": replayed}
        self.store.remember(scope, "replay", key, payload, json.dumps(result, sort_keys=True))
        return result

    def create_external_ticket(self, scope: Scope, actor: str, correlation_id: str, key: str, payload: dict[str, Any]) -> ExternalTicket:
        self._require_key(key)
        payload = sanitize(payload)
        missing = [field for field in ("connector_id", "title", "department") if not payload.get(field)]
        if missing:
            raise ValidationError("missing required fields: " + ", ".join(missing))
        connector = self.store.get_connector(payload["connector_id"], scope)
        if connector.status != ConnectorState.READY:
            raise ConflictError("connector is not ready")
        command_payload = {
            "connector_id": payload["connector_id"],
            "title": payload["title"],
            "department": payload["department"],
            "external_ref": payload.get("external_ref") or f"ext:{uuid4()}",
            "source_event_id": payload.get("source_event_id"),
            "evidence_refs": sorted(set(payload.get("evidence_refs") or [])),
        }
        prior = self.store.idempotent(scope, "create_external_ticket", key, command_payload)
        if prior:
            return self.store.get_ticket(prior, scope)
        timestamp = now()
        ticket = ExternalTicket(
            str(uuid4()),
            scope,
            actor,
            correlation_id,
            command_payload["connector_id"],
            command_payload["external_ref"],
            command_payload["title"],
            TicketState.OPEN,
            command_payload["department"],
            command_payload.get("source_event_id"),
            command_payload["evidence_refs"],
            timestamp,
            timestamp,
        )
        self.store.put_ticket(ticket)
        self.store.remember(scope, "create_external_ticket", key, command_payload, ticket.id)
        self.emit("ExternalTicketCreated", ticket.public(), scope, actor, correlation_id, key, ticket.id, ticket.evidence_refs)
        return ticket

    def sync_external_status(self, scope: Scope, actor: str, correlation_id: str, key: str, ticket_id: str, status: str) -> ExternalTicket:
        self._require_key(key)
        payload = {"ticket_id": ticket_id, "status": status}
        prior = self.store.idempotent(scope, "sync_external_status", key, payload)
        if prior:
            return self.store.get_ticket(prior, scope)
        ticket = self.store.get_ticket(ticket_id, scope)
        try:
            ticket.status = TicketState(status)
        except ValueError as exc:
            raise ValidationError("invalid ticket status") from exc
        ticket.version += 1
        ticket.updated_at = now()
        self.store.put_ticket(ticket)
        self.store.remember(scope, "sync_external_status", key, payload, ticket.id)
        self.emit("ExternalStatusSynced", ticket.public(), scope, actor, correlation_id, key, ticket.id, ticket.evidence_refs)
        return ticket

    def validate_message(self, message: dict[str, Any], scope: Scope) -> dict[str, Any]:
        if not isinstance(message, dict):
            raise ValidationError("message must be an object")
        missing = [field for field in REQUIRED_MESSAGE_FIELDS if field not in message]
        if missing:
            raise ValidationError("missing required fields: " + ", ".join(missing))
        if message["schema_version"] != "1.0.0":
            raise ValidationError("unsupported schema_version")
        if message["intent"] not in ALLOWED_INTENTS:
            raise ValidationError("unsupported intent")
        if message["tenant_id"] != scope.tenant_id or message["project_id"] != scope.project_id:
            raise ValidationError("message scope does not match request scope")
        if not isinstance(message["payload"], dict):
            raise ValidationError("payload must be an object")
        if not isinstance(message["refs"], list):
            raise ValidationError("refs must be a list")
        if message.get("sender_type") not in {"agent", "ide", "human", "adapter", "system"}:
            raise ValidationError("invalid sender_type")
        return message

    def discover_capabilities(self, scope: Scope) -> list[dict[str, Any]]:
        return [
            {
                "connector_id": connector.id,
                "vendor": connector.vendor,
                "capabilities": connector.capabilities,
                "status": connector.status.value,
                "trust_level": connector.trust_level,
            }
            for connector in self.store.list_connectors(scope)
            if connector.status == ConnectorState.READY
        ]

    def get_connector_health(self, scope: Scope, connector_id: str) -> dict[str, Any]:
        connector = self.store.get_connector(connector_id, scope)
        return {
            "connector": connector.public(),
            "ready": connector.status == ConnectorState.READY,
            "delivery_count": len(self.store.list_deliveries(scope)),
            "dead_letter_count": len(self.store.list_dead_letters(scope)),
        }

    def list_subscriptions(self, scope: Scope) -> list[Subscription]:
        return self.store.list_subscriptions(scope)

    def get_dead_letter_queue(self, scope: Scope) -> list[DeadLetterRecord]:
        return self.store.list_dead_letters(scope)

    def get_adapter_mapping(self, scope: Scope, connector_id: str) -> list[AdapterMapping]:
        self.store.get_connector(connector_id, scope)
        return self.store.list_mappings(scope, connector_id)

    def list_department_tasks(self, scope: Scope) -> list[DepartmentTask]:
        return self.store.list_department_tasks(scope)

    def _vendor_to_universal(
        self,
        scope: Scope,
        connector: Connector,
        mapping: AdapterMapping,
        vendor_payload: dict[str, Any],
        correlation_id: str,
    ) -> dict[str, Any]:
        status = vendor_payload.get(mapping.field_map.get("status", "status")) or vendor_payload.get("status") or "in_progress"
        task_id = vendor_payload.get("task_id") or _nested(vendor_payload, mapping.field_map.get("task_id", "task_id"))
        intent = str(vendor_payload.get("intent") or "TASK_STARTED")
        return {
            "message_id": str(vendor_payload.get("id") or uuid4()),
            "schema_version": "1.0.0",
            "sender": connector.vendor,
            "sender_type": "adapter",
            "tenant_id": scope.tenant_id,
            "project_id": scope.project_id,
            "intent": intent,
            "domain": str(vendor_payload.get("domain") or "engineering"),
            "payload": {
                "vendor": connector.vendor,
                "raw_status": status,
                "summary": vendor_payload.get("summary") or vendor_payload.get("message") or "",
                "normalized_by": mapping.id,
            },
            "status": str(status),
            "refs": [value for value in [task_id, connector.id] if value],
            "correlation_id": str(vendor_payload.get("correlation_id") or correlation_id),
            "created_at": now(),
            "idempotency_key": vendor_payload.get("idempotency_key"),
        }

    def _deliver(self, scope: Scope, event: BrokerEvent, replay: bool = False) -> list[Delivery]:
        deliveries: list[Delivery] = []
        timestamp = now()
        for subscription in self.store.list_subscriptions(scope):
            if subscription.status != SubscriptionState.ACTIVE:
                continue
            if subscription.channel != event.channel and subscription.channel != "*":
                continue
            intent = event.message["intent"]
            domain = event.message["domain"]
            if subscription.filter_intents and intent not in subscription.filter_intents:
                continue
            if subscription.filter_domains and domain not in subscription.filter_domains:
                continue
            delivery = Delivery(str(uuid4()), scope, event.id, subscription.id, DeliveryState.PENDING, 1, None, timestamp, timestamp)
            if subscription.fail_mode == "always" and not replay:
                delivery.status = DeliveryState.RETRYING
                delivery.attempts = self.max_delivery_attempts
                delivery.last_error = "subscriber endpoint failed"
                delivery.status = DeliveryState.DEAD_LETTERED
                delivery.updated_at = now()
                self.store.put_delivery(delivery)
                dead = DeadLetterRecord(str(uuid4()), scope, event.id, subscription.id, delivery.last_error, event.message, now())
                self.store.put_dead_letter(dead)
                self.emit("BrokerDeliveryFailed", dead.public(), scope, "broker", event.message.get("correlation_id") or "", "", dead.id, event.message.get("refs") or [])
                self.emit("DeadLetterCreated", dead.public(), scope, "broker", event.message.get("correlation_id") or "", "", dead.id, event.message.get("refs") or [])
            else:
                delivery.status = DeliveryState.DELIVERED
                delivery.updated_at = now()
                self.store.put_delivery(delivery)
                if subscription.subscriber_type == "ide":
                    self.emit("IdeNotificationSent", {"subscription_id": subscription.id, "event_id": event.id, "endpoint": subscription.endpoint}, scope, "broker", event.message.get("correlation_id") or "", "", delivery.id, event.message.get("refs") or [])
            deliveries.append(delivery)
        return deliveries

    def _trigger_department_workflows(self, scope: Scope, message: dict[str, Any], event_id: str) -> list[DepartmentTask]:
        departments = DEPARTMENT_TRIGGERS.get(message["intent"], ())
        tasks: list[DepartmentTask] = []
        for department in departments:
            task = DepartmentTask(
                str(uuid4()),
                scope,
                department,
                f"{department} follow-up for {message['intent']}",
                message["intent"],
                message["message_id"],
                department in {"marketing", "support", "devops"},
                "open",
                now(),
            )
            self.store.put_department_task(task)
            self.emit(
                "DepartmentTaskCreated",
                {**task.public(), "source_event_id": event_id},
                scope,
                "system",
                message.get("correlation_id") or "",
                "",
                task.id,
                message.get("refs") or [],
            )
            tasks.append(task)
        return tasks

    def _publish_result(self, event: BrokerEvent) -> dict[str, Any]:
        return {"event": event.public(), "channel": event.channel}

    def _require_key(self, key: str) -> None:
        if not key:
            raise ValidationError("Idempotency-Key header is required")

    def emit(self, event_type: str, payload: dict[str, Any], scope: Scope, actor: str, correlation_id: str, key: str, causation_id: str, evidence_refs: list[str]) -> None:
        self.store.event(
            {
                "event_id": str(uuid4()),
                "event_type": event_type,
                "event_version": 1,
                "occurred_at": now(),
                "producer": "adapter-service",
                "tenant_id": scope.tenant_id,
                "workspace_id": scope.workspace_id,
                "project_id": scope.project_id,
                "project_group_id": scope.project_group_id,
                "actor_ref": actor,
                "correlation_id": correlation_id,
                "causation_id": causation_id,
                "idempotency_key": key,
                "payload": payload,
                "evidence_refs": evidence_refs,
            }
        )


def channel_for(intent: str, domain: str) -> str:
    if intent in {"API_READY", "DOC_DRIFT_FOUND"}:
        return "ide.notifications"
    if intent in {"CODE_RELEASED", "DEPLOYMENT_COMPLETED", "DOWNSTREAM_TASK_REQUESTED"}:
        return "department.workflows"
    if intent.startswith("TASK_"):
        return "agent.tasks"
    return f"domain.{domain}"


def _nested(payload: dict[str, Any], path: str) -> Any:
    current: Any = payload
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


SECRET = re.compile(r"(?i)((?:api[_-]?key|token|password|secret)\s*[:=]\s*)([^\s,;]+)")


def now() -> str:
    return datetime.now(UTC).isoformat()


def sanitize(value: Any) -> Any:
    if isinstance(value, str):
        return SECRET.sub(r"\1[REDACTED]", value)
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    if isinstance(value, dict):
        return {key: sanitize(item) for key, item in value.items()}
    return value


def digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return sha256(encoded).hexdigest()
