from __future__ import annotations

from typing import Any

from .core import (
    AdapterMapping,
    BrokerEvent,
    ConflictError,
    Connector,
    ConnectorState,
    DeadLetterRecord,
    Delivery,
    DeliveryState,
    DepartmentTask,
    ExternalTicket,
    MappingState,
    NotFoundError,
    Scope,
    Subscription,
    SubscriptionState,
    TicketState,
    digest,
)


def _timestamp(value: Any) -> str:
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


class PostgresStore:
    """PostgreSQL adapter for the Adapter / Interop Store port."""

    def __init__(self, database_url: str) -> None:
        if not database_url.startswith(("postgresql://", "postgresql+psycopg://")):
            raise ValueError("Adapter database URL must use PostgreSQL")
        try:
            import psycopg
            from psycopg.rows import dict_row
            from psycopg.types.json import Jsonb
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("psycopg is required for PostgreSQL persistence") from exc
        normalized_url = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
        self._connection = psycopg.connect(normalized_url, autocommit=True, row_factory=dict_row)
        self._json = Jsonb

    @staticmethod
    def _scope_key(scope: Scope) -> str:
        return "|".join((scope.tenant_id, scope.workspace_id, scope.project_id, scope.project_group_id or ""))

    def _connector(self, row: dict[str, Any], scope: Scope) -> Connector:
        return Connector(
            row["id"], scope, row["actor_id"], row["correlation_id"], row["vendor"], row["name"], row["capabilities"],
            row["auth_profile"], row["trust_level"], ConnectorState(row["status"]), row["credential_fingerprint"],
            _timestamp(row["created_at"]), _timestamp(row["updated_at"]), row["version"],
        )

    def _mapping(self, row: dict[str, Any], scope: Scope) -> AdapterMapping:
        return AdapterMapping(
            row["id"], scope, row["connector_id"], row["vendor_schema_version"], row["field_map"],
            MappingState(row["status"]), _timestamp(row["created_at"]), _timestamp(row["updated_at"]), row["version"],
        )

    def _subscription(self, row: dict[str, Any], scope: Scope) -> Subscription:
        return Subscription(
            row["id"], scope, row["actor_id"], row["correlation_id"], row["channel"], row["subscriber_type"],
            row["endpoint"], row["filter_intents"], row["filter_domains"], SubscriptionState(row["status"]),
            row["fail_mode"], _timestamp(row["created_at"]), _timestamp(row["updated_at"]), row["version"],
        )

    def _event(self, row: dict[str, Any], scope: Scope) -> BrokerEvent:
        return BrokerEvent(row["id"], scope, row["channel"], row["message"], _timestamp(row["created_at"]))

    def _delivery(self, row: dict[str, Any], scope: Scope) -> Delivery:
        return Delivery(
            row["id"], scope, row["event_id"], row["subscription_id"], DeliveryState(row["status"]),
            row["attempts"], row["last_error"], _timestamp(row["created_at"]), _timestamp(row["updated_at"]),
        )

    def _dead(self, row: dict[str, Any], scope: Scope) -> DeadLetterRecord:
        return DeadLetterRecord(
            row["id"], scope, row["event_id"], row["subscription_id"], row["reason"], row["message"],
            _timestamp(row["created_at"]),
        )

    def _ticket(self, row: dict[str, Any], scope: Scope) -> ExternalTicket:
        return ExternalTicket(
            row["id"], scope, row["actor_id"], row["correlation_id"], row["connector_id"], row["external_ref"],
            row["title"], TicketState(row["status"]), row["department"], row["source_event_id"], row["evidence_refs"],
            _timestamp(row["created_at"]), _timestamp(row["updated_at"]), row["version"],
        )

    def _department(self, row: dict[str, Any], scope: Scope) -> DepartmentTask:
        return DepartmentTask(
            row["id"], scope, row["department"], row["title"], row["trigger_intent"], row["source_message_id"],
            row["approval_required"], row["status"], _timestamp(row["created_at"]),
        )

    def get_connector(self, connector_id: str, scope: Scope) -> Connector:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """SELECT * FROM adapter.connectors WHERE id=%s AND tenant_id=%s AND workspace_id=%s AND project_id=%s""",
                (connector_id, scope.tenant_id, scope.workspace_id, scope.project_id),
            )
            row = cursor.fetchone()
        if row is None:
            raise NotFoundError("connector not found in project scope")
        return self._connector(row, scope)

    def put_connector(self, connector: Connector) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO adapter.connectors
                   (id,tenant_id,workspace_id,project_id,project_group_id,actor_id,correlation_id,vendor,name,capabilities,
                    auth_profile,trust_level,status,credential_fingerprint,version,created_at,updated_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (id) DO UPDATE SET status=EXCLUDED.status,capabilities=EXCLUDED.capabilities,
                   credential_fingerprint=EXCLUDED.credential_fingerprint,version=EXCLUDED.version,updated_at=EXCLUDED.updated_at""",
                (connector.id, connector.scope.tenant_id, connector.scope.workspace_id, connector.scope.project_id,
                 connector.scope.project_group_id, connector.actor_id, connector.correlation_id, connector.vendor,
                 connector.name, self._json(connector.capabilities), connector.auth_profile, connector.trust_level,
                 connector.status.value, connector.credential_fingerprint, connector.version, connector.created_at,
                 connector.updated_at),
            )

    def list_connectors(self, scope: Scope) -> list[Connector]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """SELECT * FROM adapter.connectors WHERE tenant_id=%s AND workspace_id=%s AND project_id=%s
                   ORDER BY created_at,id""",
                (scope.tenant_id, scope.workspace_id, scope.project_id),
            )
            return [self._connector(row, scope) for row in cursor.fetchall()]

    def put_mapping(self, mapping: AdapterMapping) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO adapter.mappings
                   (id,tenant_id,workspace_id,project_id,project_group_id,connector_id,vendor_schema_version,field_map,
                    status,version,created_at,updated_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (id) DO UPDATE SET field_map=EXCLUDED.field_map,status=EXCLUDED.status,
                   version=EXCLUDED.version,updated_at=EXCLUDED.updated_at""",
                (mapping.id, mapping.scope.tenant_id, mapping.scope.workspace_id, mapping.scope.project_id,
                 mapping.scope.project_group_id, mapping.connector_id, mapping.vendor_schema_version,
                 self._json(mapping.field_map), mapping.status.value, mapping.version, mapping.created_at, mapping.updated_at),
            )

    def list_mappings(self, scope: Scope, connector_id: str | None = None) -> list[AdapterMapping]:
        with self._connection.cursor() as cursor:
            if connector_id is None:
                cursor.execute(
                    """SELECT * FROM adapter.mappings WHERE tenant_id=%s AND workspace_id=%s AND project_id=%s
                       ORDER BY created_at,id""",
                    (scope.tenant_id, scope.workspace_id, scope.project_id),
                )
            else:
                cursor.execute(
                    """SELECT * FROM adapter.mappings WHERE tenant_id=%s AND workspace_id=%s AND project_id=%s
                       AND connector_id=%s ORDER BY created_at,id""",
                    (scope.tenant_id, scope.workspace_id, scope.project_id, connector_id),
                )
            return [self._mapping(row, scope) for row in cursor.fetchall()]

    def get_subscription(self, subscription_id: str, scope: Scope) -> Subscription:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """SELECT * FROM adapter.subscriptions WHERE id=%s AND tenant_id=%s AND workspace_id=%s AND project_id=%s""",
                (subscription_id, scope.tenant_id, scope.workspace_id, scope.project_id),
            )
            row = cursor.fetchone()
        if row is None:
            raise NotFoundError("subscription not found in project scope")
        return self._subscription(row, scope)

    def put_subscription(self, subscription: Subscription) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO adapter.subscriptions
                   (id,tenant_id,workspace_id,project_id,project_group_id,actor_id,correlation_id,channel,subscriber_type,
                    endpoint,filter_intents,filter_domains,status,fail_mode,version,created_at,updated_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (id) DO UPDATE SET status=EXCLUDED.status,filter_intents=EXCLUDED.filter_intents,
                   filter_domains=EXCLUDED.filter_domains,version=EXCLUDED.version,updated_at=EXCLUDED.updated_at""",
                (subscription.id, subscription.scope.tenant_id, subscription.scope.workspace_id, subscription.scope.project_id,
                 subscription.scope.project_group_id, subscription.actor_id, subscription.correlation_id, subscription.channel,
                 subscription.subscriber_type, subscription.endpoint, self._json(subscription.filter_intents),
                 self._json(subscription.filter_domains), subscription.status.value, subscription.fail_mode,
                 subscription.version, subscription.created_at, subscription.updated_at),
            )

    def list_subscriptions(self, scope: Scope) -> list[Subscription]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """SELECT * FROM adapter.subscriptions WHERE tenant_id=%s AND workspace_id=%s AND project_id=%s
                   ORDER BY created_at,id""",
                (scope.tenant_id, scope.workspace_id, scope.project_id),
            )
            return [self._subscription(row, scope) for row in cursor.fetchall()]

    def put_event(self, event: BrokerEvent) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO adapter.broker_events
                   (id,tenant_id,workspace_id,project_id,project_group_id,channel,message,created_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (id) DO NOTHING""",
                (event.id, event.scope.tenant_id, event.scope.workspace_id, event.scope.project_id,
                 event.scope.project_group_id, event.channel, self._json(event.message), event.created_at),
            )

    def get_event(self, event_id: str, scope: Scope) -> BrokerEvent:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """SELECT * FROM adapter.broker_events WHERE id=%s AND tenant_id=%s AND workspace_id=%s AND project_id=%s""",
                (event_id, scope.tenant_id, scope.workspace_id, scope.project_id),
            )
            row = cursor.fetchone()
        if row is None:
            raise NotFoundError("broker event not found in project scope")
        return self._event(row, scope)

    def list_events(self, scope: Scope, channel: str | None = None) -> list[BrokerEvent]:
        with self._connection.cursor() as cursor:
            if channel is None:
                cursor.execute(
                    """SELECT * FROM adapter.broker_events WHERE tenant_id=%s AND workspace_id=%s AND project_id=%s
                       ORDER BY created_at,id""",
                    (scope.tenant_id, scope.workspace_id, scope.project_id),
                )
            else:
                cursor.execute(
                    """SELECT * FROM adapter.broker_events WHERE tenant_id=%s AND workspace_id=%s AND project_id=%s
                       AND channel=%s ORDER BY created_at,id""",
                    (scope.tenant_id, scope.workspace_id, scope.project_id, channel),
                )
            return [self._event(row, scope) for row in cursor.fetchall()]

    def put_delivery(self, delivery: Delivery) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO adapter.deliveries
                   (id,tenant_id,workspace_id,project_id,project_group_id,event_id,subscription_id,status,attempts,
                    last_error,created_at,updated_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (id) DO UPDATE SET status=EXCLUDED.status,attempts=EXCLUDED.attempts,
                   last_error=EXCLUDED.last_error,updated_at=EXCLUDED.updated_at""",
                (delivery.id, delivery.scope.tenant_id, delivery.scope.workspace_id, delivery.scope.project_id,
                 delivery.scope.project_group_id, delivery.event_id, delivery.subscription_id, delivery.status.value,
                 delivery.attempts, delivery.last_error, delivery.created_at, delivery.updated_at),
            )

    def list_deliveries(self, scope: Scope) -> list[Delivery]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """SELECT * FROM adapter.deliveries WHERE tenant_id=%s AND workspace_id=%s AND project_id=%s
                   ORDER BY created_at,id""",
                (scope.tenant_id, scope.workspace_id, scope.project_id),
            )
            return [self._delivery(row, scope) for row in cursor.fetchall()]

    def put_dead_letter(self, record: DeadLetterRecord) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO adapter.dead_letters
                   (id,tenant_id,workspace_id,project_id,project_group_id,event_id,subscription_id,reason,message,created_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (id) DO NOTHING""",
                (record.id, record.scope.tenant_id, record.scope.workspace_id, record.scope.project_id,
                 record.scope.project_group_id, record.event_id, record.subscription_id, record.reason,
                 self._json(record.message), record.created_at),
            )

    def list_dead_letters(self, scope: Scope) -> list[DeadLetterRecord]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """SELECT * FROM adapter.dead_letters WHERE tenant_id=%s AND workspace_id=%s AND project_id=%s
                   ORDER BY created_at,id""",
                (scope.tenant_id, scope.workspace_id, scope.project_id),
            )
            return [self._dead(row, scope) for row in cursor.fetchall()]

    def get_ticket(self, ticket_id: str, scope: Scope) -> ExternalTicket:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """SELECT * FROM adapter.external_tickets WHERE id=%s AND tenant_id=%s AND workspace_id=%s AND project_id=%s""",
                (ticket_id, scope.tenant_id, scope.workspace_id, scope.project_id),
            )
            row = cursor.fetchone()
        if row is None:
            raise NotFoundError("external ticket not found in project scope")
        return self._ticket(row, scope)

    def put_ticket(self, ticket: ExternalTicket) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO adapter.external_tickets
                   (id,tenant_id,workspace_id,project_id,project_group_id,actor_id,correlation_id,connector_id,external_ref,
                    title,status,department,source_event_id,evidence_refs,version,created_at,updated_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (id) DO UPDATE SET status=EXCLUDED.status,version=EXCLUDED.version,updated_at=EXCLUDED.updated_at""",
                (ticket.id, ticket.scope.tenant_id, ticket.scope.workspace_id, ticket.scope.project_id,
                 ticket.scope.project_group_id, ticket.actor_id, ticket.correlation_id, ticket.connector_id,
                 ticket.external_ref, ticket.title, ticket.status.value, ticket.department, ticket.source_event_id,
                 self._json(ticket.evidence_refs), ticket.version, ticket.created_at, ticket.updated_at),
            )

    def list_tickets(self, scope: Scope) -> list[ExternalTicket]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """SELECT * FROM adapter.external_tickets WHERE tenant_id=%s AND workspace_id=%s AND project_id=%s
                   ORDER BY created_at,id""",
                (scope.tenant_id, scope.workspace_id, scope.project_id),
            )
            return [self._ticket(row, scope) for row in cursor.fetchall()]

    def put_department_task(self, task: DepartmentTask) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO adapter.department_tasks
                   (id,tenant_id,workspace_id,project_id,project_group_id,department,title,trigger_intent,
                    source_message_id,approval_required,status,created_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (id) DO NOTHING""",
                (task.id, task.scope.tenant_id, task.scope.workspace_id, task.scope.project_id, task.scope.project_group_id,
                 task.department, task.title, task.trigger_intent, task.source_message_id, task.approval_required,
                 task.status, task.created_at),
            )

    def list_department_tasks(self, scope: Scope) -> list[DepartmentTask]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """SELECT * FROM adapter.department_tasks WHERE tenant_id=%s AND workspace_id=%s AND project_id=%s
                   ORDER BY created_at,id""",
                (scope.tenant_id, scope.workspace_id, scope.project_id),
            )
            return [self._department(row, scope) for row in cursor.fetchall()]

    def idempotent(self, scope: Scope, command: str, key: str, payload: dict[str, Any]) -> str | None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """SELECT fingerprint,record_id FROM adapter.idempotency
                   WHERE scope_key=%s AND command=%s AND idempotency_key=%s""",
                (self._scope_key(scope), command, key),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        if row["fingerprint"] != digest(payload):
            raise ConflictError("idempotency key was reused with a different payload")
        return row["record_id"]

    def remember(self, scope: Scope, command: str, key: str, payload: dict[str, Any], record_id: str) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO adapter.idempotency
                   (scope_key,command,idempotency_key,fingerprint,record_id) VALUES (%s,%s,%s,%s,%s)""",
                (self._scope_key(scope), command, key, digest(payload), record_id),
            )

    def event(self, payload: dict[str, Any]) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO adapter.outbox (event_id,event_type,payload,occurred_at) VALUES (%s,%s,%s,%s)",
                (payload["event_id"], payload["event_type"], self._json(payload), payload["occurred_at"]),
            )

    def outbox(self) -> list[dict[str, Any]]:
        with self._connection.cursor() as cursor:
            cursor.execute("SELECT payload FROM adapter.outbox ORDER BY occurred_at,event_id")
            return [row["payload"] for row in cursor.fetchall()]

    def close(self) -> None:
        self._connection.close()
