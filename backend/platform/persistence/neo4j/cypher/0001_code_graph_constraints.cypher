// Code-Knowledge Graph Neo4j constraints and indexes.
// Applied by Neo4jStore.ensure_schema() on service startup when store_backend=neo4j.
// Node model mirrors the Phase 7 Store port (unified CodeSymbol + CODE_REL edges).

CREATE CONSTRAINT code_symbol_id IF NOT EXISTS
FOR (n:CodeSymbol) REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT code_outbox_event_id IF NOT EXISTS
FOR (n:CodeOutboxEvent) REQUIRE n.event_id IS UNIQUE;

CREATE CONSTRAINT code_idempotency_key IF NOT EXISTS
FOR (n:CodeIdempotency) REQUIRE (n.scope_key, n.idempotency_key, n.resource_type) IS UNIQUE;

CREATE INDEX code_symbol_scope IF NOT EXISTS
FOR (n:CodeSymbol) ON (n.tenant_id, n.workspace_id, n.project_id);

CREATE INDEX code_symbol_qualified_name IF NOT EXISTS
FOR (n:CodeSymbol) ON (n.project_id, n.qualified_name);
