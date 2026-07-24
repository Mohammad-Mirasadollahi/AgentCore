"""Neo4j Cypher query strings for Code Graph CRUD."""

from __future__ import annotations

from .constants import REL

GET_SYMBOL = """
MATCH (n:CodeSymbol {id: $id})
WHERE n.tenant_id = $tenant_id
  AND n.workspace_id = $workspace_id
  AND n.project_id = $project_id
RETURN n
"""

PUT_SYMBOL = """
MERGE (n:CodeSymbol {id: $id})
SET n.tenant_id = $tenant_id,
    n.workspace_id = $workspace_id,
    n.project_id = $project_id,
    n.project_group_id = $project_group_id,
    n.kind = $kind,
    n.file_path = $file_path,
    n.name = $name,
    n.qualified_name = $qualified_name,
    n.signature = $signature,
    n.body = $body,
    n.hash_value = $hash_value,
    n.ai_documentation = $ai_documentation,
    n.doc_status = $doc_status,
    n.embedding = $embedding,
    n.visibility = $visibility,
    n.version = $version,
    n.created_at = $created_at,
    n.updated_at = $updated_at,
    n.language = $language
"""

DELETE_SYMBOL = """
MATCH (n:CodeSymbol {id: $id})
WHERE n.tenant_id = $tenant_id
  AND n.workspace_id = $workspace_id
  AND n.project_id = $project_id
DETACH DELETE n
"""

LIST_SYMBOLS = """
MATCH (n:CodeSymbol)
WHERE n.tenant_id = $tenant_id
  AND n.workspace_id = $workspace_id
  AND n.project_id = $project_id
WITH n
ORDER BY n.qualified_name, n.id
RETURN n {
  .id, .kind, .file_path, .name, .qualified_name, .signature,
  .body, .hash_value, .ai_documentation, .doc_status,
  .visibility, .version, .created_at, .updated_at, .language,
  embedding: []
} AS n
"""

LIST_SYMBOLS_FOR_FILE = """
MATCH (n:CodeSymbol)
WHERE n.tenant_id = $tenant_id
  AND n.workspace_id = $workspace_id
  AND n.project_id = $project_id
  AND n.file_path = $file_path
RETURN n
ORDER BY n.qualified_name, n.id
"""

GET_SYMBOL_BY_QUALIFIED_NAME = """
MATCH (n:CodeSymbol)
WHERE n.tenant_id = $tenant_id
  AND n.workspace_id = $workspace_id
  AND n.project_id = $project_id
  AND n.qualified_name = $qualified_name
RETURN n
LIMIT 1
"""

DELETE_FILE_EDGES = f"""
MATCH ()-[r:{REL}]->()
WHERE r.tenant_id = $tenant_id
  AND r.workspace_id = $workspace_id
  AND r.project_id = $project_id
  AND r.file_path = $file_path
DELETE r
"""

DELETE_EDGE = f"""
MATCH ()-[r:{REL} {{id: $id}}]->()
WHERE r.tenant_id = $tenant_id
  AND r.workspace_id = $workspace_id
  AND r.project_id = $project_id
DELETE r
"""

PUT_EDGE = f"""
MATCH (source:CodeSymbol {{id: $source_id}})
MATCH (target:CodeSymbol {{id: $target_id}})
MERGE (source)-[r:{REL} {{id: $id}}]->(target)
SET r.tenant_id = $tenant_id,
    r.workspace_id = $workspace_id,
    r.project_id = $project_id,
    r.project_group_id = $project_group_id,
    r.rel_type = $rel_type,
    r.confidence = $confidence,
    r.file_path = $file_path,
    r.metadata_json = $metadata_json
"""

LIST_EDGES = f"""
MATCH (source:CodeSymbol)-[r:{REL}]->(target:CodeSymbol)
WHERE r.tenant_id = $tenant_id
  AND r.workspace_id = $workspace_id
  AND r.project_id = $project_id
RETURN r.id AS id,
       r.rel_type AS rel_type,
       r.confidence AS confidence,
       r.metadata_json AS metadata_json,
       source.id AS source_id,
       target.id AS target_id
ORDER BY r.id
"""

BEGIN_IDEMPOTENCY = """
MATCH (n:CodeIdempotency {
    scope_key: $scope_key,
    idempotency_key: $idempotency_key,
    resource_type: $resource_type
})
RETURN n.resource_id AS resource_id
"""

COMPLETE_IDEMPOTENCY = """
MERGE (n:CodeIdempotency {
    scope_key: $scope_key,
    idempotency_key: $idempotency_key,
    resource_type: $resource_type
})
ON CREATE SET n.resource_id = $resource_id
RETURN n.resource_id AS resource_id
"""

APPEND_EVENT = """
CREATE (n:CodeOutboxEvent {
    event_id: $event_id,
    event_type: $event_type,
    payload_json: $payload_json,
    created_at: datetime()
})
"""

OUTBOX = """
MATCH (n:CodeOutboxEvent)
RETURN n.payload_json AS payload_json
ORDER BY n.created_at, n.event_id
"""

WIPE_SYMBOLS = """
MATCH (n:CodeSymbol)
WHERE n.tenant_id = $tenant_id
  AND n.workspace_id = $workspace_id
  AND n.project_id = $project_id
WITH collect(n) AS nodes
FOREACH (n IN nodes | DETACH DELETE n)
RETURN size(nodes) AS deleted
"""

WIPE_EDGES = f"""
MATCH ()-[r:{REL}]->()
WHERE r.tenant_id = $tenant_id
  AND r.workspace_id = $workspace_id
  AND r.project_id = $project_id
WITH collect(r) AS rels
FOREACH (r IN rels | DELETE r)
RETURN size(rels) AS deleted
"""

WIPE_IDEMPOTENCY = """
MATCH (n:CodeIdempotency {scope_key: $scope_key})
WITH collect(n) AS nodes
FOREACH (n IN nodes | DELETE n)
RETURN size(nodes) AS deleted
"""
