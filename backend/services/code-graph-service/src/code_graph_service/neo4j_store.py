from __future__ import annotations

import hashlib
import json
from typing import Any

from .core import (
    CallConfidence,
    ConflictError,
    DocStatus,
    GraphEdge,
    GraphSymbol,
    NotFoundError,
    Scope,
    SymbolKind,
)

# Structural graph edges share one relationship type; `rel_type` carries CALLS/IMPORTS/etc.
_REL = "CODE_REL"


class Neo4jStore:
    """Neo4j adapter for the Code Graph Store port (structural graph + outbox)."""

    def __init__(
        self,
        *,
        uri: str,
        user: str,
        password: str,
        database: str = "neo4j",
        driver: Any | None = None,
        ensure_schema: bool = True,
        gds_enabled: bool = True,
        gds_concurrency: int = 4,
    ) -> None:
        if driver is None:
            if not uri.startswith(("bolt://", "bolt+s://", "neo4j://", "neo4j+s://")):
                raise ValueError("Neo4j URI must use bolt://, bolt+s://, neo4j://, or neo4j+s://")
            try:
                from neo4j import GraphDatabase
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError("neo4j package is required for Neo4j persistence") from exc
            driver = GraphDatabase.driver(uri, auth=(user, password))
        self._driver = driver
        self._database = database
        self._gds_enabled = bool(gds_enabled)
        # GDS Community Edition hard-caps at 4 cores — never request more.
        self._gds_concurrency = max(1, min(int(gds_concurrency), 4))
        self._capabilities_cache: dict[str, Any] | None = None
        if ensure_schema:
            self.ensure_schema()

    def close(self) -> None:
        close = getattr(self._driver, "close", None)
        if callable(close):
            close()

    def ensure_schema(self) -> None:
        statements = (
            "CREATE CONSTRAINT code_symbol_id IF NOT EXISTS "
            "FOR (n:CodeSymbol) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT code_outbox_event_id IF NOT EXISTS "
            "FOR (n:CodeOutboxEvent) REQUIRE n.event_id IS UNIQUE",
            "CREATE CONSTRAINT code_idempotency_key IF NOT EXISTS "
            "FOR (n:CodeIdempotency) REQUIRE (n.scope_key, n.idempotency_key, n.resource_type) IS UNIQUE",
            "CREATE INDEX code_symbol_scope IF NOT EXISTS "
            "FOR (n:CodeSymbol) ON (n.tenant_id, n.workspace_id, n.project_id)",
            "CREATE INDEX code_symbol_qualified_name IF NOT EXISTS "
            "FOR (n:CodeSymbol) ON (n.project_id, n.qualified_name)",
            "CREATE INDEX code_symbol_kind IF NOT EXISTS "
            "FOR (n:CodeSymbol) ON (n.kind)",
            # Canonical Lucene fulltext (includes file_path). Legacy
            # `code_symbol_fulltext` without file_path is no longer created;
            # query still falls back if an old DB only has the legacy name.
            "CREATE FULLTEXT INDEX code_symbol_fulltext_v2 IF NOT EXISTS "
            "FOR (n:CodeSymbol) ON EACH "
            "[n.qualified_name, n.name, n.signature, n.file_path, n.ai_documentation]",
        )
        with self._driver.session(database=self._database) as session:
            for statement in statements:
                session.run(statement)
        self._capabilities_cache = None

    def capabilities(self) -> dict[str, Any]:
        """Probe APOC / GDS / fulltext (cached until schema refresh).

        ``gds`` is false when ``AGENTCORE_NEO4J_GDS_ENABLED`` is off, even if the
        plugin is installed. Also reports ``gds_enabled`` and ``gds_concurrency``
        (Community Edition hard-capped at 4).
        """
        if self._capabilities_cache is not None:
            return dict(self._capabilities_cache)
        caps: dict[str, Any] = {
            "apoc": False,
            "gds": False,
            "fulltext": False,
            "gds_enabled": self._gds_enabled,
            "gds_concurrency": self._gds_concurrency,
        }
        with self._driver.session(database=self._database) as session:
            try:
                record = session.run("RETURN apoc.version() AS version").single()
                caps["apoc"] = record is not None and bool(record.get("version"))
            except Exception:  # pragma: no cover - depends on runtime plugins
                caps["apoc"] = False
            if self._gds_enabled:
                try:
                    record = session.run("RETURN gds.version() AS version").single()
                    caps["gds"] = record is not None and bool(record.get("version"))
                except Exception:  # pragma: no cover
                    caps["gds"] = False
            else:
                caps["gds"] = False
            try:
                record = session.run(
                    "SHOW FULLTEXT INDEXES YIELD name "
                    "WHERE name IN ['code_symbol_fulltext_v2', 'code_symbol_fulltext'] "
                    "RETURN count(*) AS c"
                ).single()
                caps["fulltext"] = bool(record and int(record["c"]) > 0)
            except Exception:  # pragma: no cover
                caps["fulltext"] = False
        self._capabilities_cache = caps
        return dict(caps)

    def fulltext_search(
        self,
        scope: Scope,
        query: str,
        *,
        top_k: int = 20,
    ) -> list[dict[str, Any]]:
        """Neo4j Lucene fulltext search (BM25-like); empty when unavailable."""
        top_k = max(1, min(int(top_k), 100))
        q = (query or "").strip()
        if not q or not self.capabilities().get("fulltext"):
            return []
        lucene_q = _lucene_query(q)
        if not lucene_q:
            return []
        index_name = self._fulltext_index_name()
        with self._driver.session(database=self._database) as session:
            try:
                rows = list(
                    session.run(
                        """
                        CALL db.index.fulltext.queryNodes($index_name, $q)
                        YIELD node, score
                        WHERE node.tenant_id = $tenant_id
                          AND node.workspace_id = $workspace_id
                          AND node.project_id = $project_id
                        RETURN node.id AS symbol_id, score
                        ORDER BY score DESC
                        LIMIT $top_k
                        """,
                        index_name=index_name,
                        q=lucene_q,
                        tenant_id=scope.tenant_id,
                        workspace_id=scope.workspace_id,
                        project_id=scope.project_id,
                        top_k=top_k,
                    )
                )
            except Exception:
                return []
        return [
            {"symbol_id": row["symbol_id"], "score": float(row["score"]), "method": "neo4j.fulltext"}
            for row in rows
        ]

    def _fulltext_index_name(self) -> str:
        with self._driver.session(database=self._database) as session:
            try:
                record = session.run(
                    "SHOW FULLTEXT INDEXES YIELD name "
                    "WHERE name = 'code_symbol_fulltext_v2' RETURN name LIMIT 1"
                ).single()
                if record:
                    return "code_symbol_fulltext_v2"
            except Exception:
                pass
        return "code_symbol_fulltext"

    def shortest_path_ids(
        self,
        scope: Scope,
        start_id: str,
        end_id: str,
        *,
        max_depth: int = 12,
    ) -> list[str]:
        """Shortest undirected CODE_REL path via Cypher shortestPath; else []."""
        max_depth = max(1, min(int(max_depth), 20))
        # Cypher shortestPath is core Neo4j (no APOC required).
        depth = max(1, min(int(max_depth), 12))
        with self._driver.session(database=self._database) as session:
            try:
                record = session.run(
                    f"""
                    MATCH (a:CodeSymbol {{id: $start_id}}), (b:CodeSymbol {{id: $end_id}})
                    WHERE a.tenant_id = $tenant_id AND b.tenant_id = $tenant_id
                      AND a.workspace_id = $workspace_id AND b.workspace_id = $workspace_id
                      AND a.project_id = $project_id AND b.project_id = $project_id
                    MATCH path = shortestPath((a)-[:CODE_REL*..{depth}]-(b))
                    RETURN [n IN nodes(path) | n.id] AS ids
                    """,
                    start_id=start_id,
                    end_id=end_id,
                    tenant_id=scope.tenant_id,
                    workspace_id=scope.workspace_id,
                    project_id=scope.project_id,
                ).single()
            except Exception:
                return []
        if not record or not record.get("ids"):
            return []
        return [str(x) for x in record["ids"]]
    def expand_neighborhood(
        self,
        scope: Scope,
        symbol_id: str,
        *,
        max_depth: int = 2,
        rel_type: str | None = None,
        limit: int = 100,
    ) -> list[GraphEdge]:
        """Multi-hop neighborhood via APOC when available; otherwise one-hop listing."""
        max_depth = max(1, min(int(max_depth), 5))
        limit = max(1, min(int(limit), 500))
        caps = self.capabilities()
        if not caps.get("apoc"):
            edges = [
                edge
                for edge in self.list_edges(scope)
                if edge.source_id == symbol_id or edge.target_id == symbol_id
            ]
            if rel_type:
                edges = [edge for edge in edges if edge.rel_type == rel_type.upper()]
            return edges[:limit]

        rel_filter = ""
        params: dict[str, Any] = {
            "id": symbol_id,
            "tenant_id": scope.tenant_id,
            "workspace_id": scope.workspace_id,
            "project_id": scope.project_id,
            "max_depth": max_depth,
            "limit": limit,
        }
        if rel_type:
            rel_filter = "AND r.rel_type = $rel_type"
            params["rel_type"] = rel_type.upper()

        query = f"""
        MATCH (start:CodeSymbol {{id: $id}})
        WHERE start.tenant_id = $tenant_id
          AND start.workspace_id = $workspace_id
          AND start.project_id = $project_id
        CALL apoc.path.expandConfig(start, {{
          relationshipFilter: 'CODE_REL',
          minLevel: 1,
          maxLevel: $max_depth,
          uniqueness: 'RELATIONSHIP_GLOBAL',
          limit: $limit
        }})
        YIELD path
        WITH relationships(path) AS rels
        UNWIND rels AS r
        WITH DISTINCT r
        WHERE r.tenant_id = $tenant_id
          AND r.workspace_id = $workspace_id
          AND r.project_id = $project_id
          {rel_filter}
        MATCH (source:CodeSymbol)-[r]->(target:CodeSymbol)
        RETURN r.id AS id,
               r.rel_type AS rel_type,
               r.confidence AS confidence,
               r.metadata_json AS metadata_json,
               source.id AS source_id,
               target.id AS target_id
        LIMIT $limit
        """
        with self._driver.session(database=self._database) as session:
            rows = list(session.run(query, **params))
        return [
            GraphEdge(
                id=row["id"],
                scope=scope,
                rel_type=row["rel_type"],
                source_id=row["source_id"],
                target_id=row["target_id"],
                confidence=CallConfidence(row["confidence"]),
                metadata=json.loads(row["metadata_json"] or "{}"),
            )
            for row in rows
        ]

    def rank_symbols_by_degree(
        self,
        scope: Scope,
        *,
        top_k: int = 20,
    ) -> list[dict[str, Any]]:
        """Degree-based importance ranking.

        Prefers ``gds.degree`` when the GDS *Community* plugin is loaded (no
        Enterprise license key required). Always falls back to Cypher degree.
        See docs/07-code-knowledge-graph/32-intentional-fallbacks-and-neo4j-plugin-licensing.md.
        """
        top_k = max(1, min(int(top_k), 100))
        caps = self.capabilities()
        # Native Cypher projection (gds.graph.project aggregation) — not deprecated
        # gds.graph.project.cypher. Graph name must be unique per scope for concurrency.
        graph_name = "cgr_" + hashlib.sha256(self._scope_key(scope).encode()).hexdigest()[:16]
        with self._driver.session(database=self._database) as session:
            if caps.get("gds"):
                try:
                    session.run(
                        "CALL gds.graph.drop($graph_name, false) YIELD graphName RETURN graphName",
                        graph_name=graph_name,
                    )
                    session.run(
                        """
                        MATCH (source:CodeSymbol)
                        WHERE source.tenant_id = $tenant_id
                          AND source.workspace_id = $workspace_id
                          AND source.project_id = $project_id
                          AND source.kind <> 'documentation'
                          AND source.kind <> 'unresolved'
                        OPTIONAL MATCH (source)-[:CODE_REL]->(target:CodeSymbol)
                        WHERE target IS NULL OR (
                          target.tenant_id = $tenant_id
                          AND target.workspace_id = $workspace_id
                          AND target.project_id = $project_id
                        )
                        WITH gds.graph.project($graph_name, source, target) AS g
                        RETURN g.graphName AS graphName
                        """,
                        graph_name=graph_name,
                        tenant_id=scope.tenant_id,
                        workspace_id=scope.workspace_id,
                        project_id=scope.project_id,
                    )
                    rows = list(
                        session.run(
                            """
                            CALL gds.degree.stream($graph_name, {concurrency: $concurrency})
                            YIELD nodeId, score
                            WITH gds.util.asNode(nodeId) AS n, score
                            RETURN n.id AS id, n.qualified_name AS qualified_name, n.kind AS kind, score
                            ORDER BY score DESC, qualified_name
                            LIMIT $top_k
                            """,
                            graph_name=graph_name,
                            concurrency=self._gds_concurrency,
                            top_k=top_k,
                        )
                    )
                    session.run(
                        "CALL gds.graph.drop($graph_name, false) YIELD graphName RETURN graphName",
                        graph_name=graph_name,
                    )
                    return [
                        {
                            "symbol_id": row["id"],
                            "qualified_name": row["qualified_name"],
                            "kind": row["kind"],
                            "score": float(row["score"]),
                            "method": "gds.degree",
                        }
                        for row in rows
                    ]
                except Exception:
                    try:
                        session.run(
                            "CALL gds.graph.drop($graph_name, false) YIELD graphName RETURN graphName",
                            graph_name=graph_name,
                        )
                    except Exception:
                        pass

            rows = list(
                session.run(
                    f"""
                    MATCH (n:CodeSymbol)
                    WHERE n.tenant_id = $tenant_id
                      AND n.workspace_id = $workspace_id
                      AND n.project_id = $project_id
                      AND n.kind <> 'documentation'
                      AND n.kind <> 'unresolved'
                    OPTIONAL MATCH (n)-[r:{_REL}]-(m:CodeSymbol)
                    WHERE m.tenant_id = $tenant_id
                      AND m.workspace_id = $workspace_id
                      AND m.project_id = $project_id
                    RETURN n.id AS id,
                           n.qualified_name AS qualified_name,
                           n.kind AS kind,
                           count(r) AS score
                    ORDER BY score DESC, qualified_name
                    LIMIT $top_k
                    """,
                    tenant_id=scope.tenant_id,
                    workspace_id=scope.workspace_id,
                    project_id=scope.project_id,
                    top_k=top_k,
                )
            )
        return [
            {
                "symbol_id": row["id"],
                "qualified_name": row["qualified_name"],
                "kind": row["kind"],
                "score": float(row["score"]),
                "method": "cypher.degree",
            }
            for row in rows
        ]

    @staticmethod
    def _scope_key(scope: Scope) -> str:
        return "|".join((scope.tenant_id, scope.workspace_id, scope.project_id, scope.project_group_id or ""))

    def _symbol_from_node(self, node: Any, scope: Scope) -> GraphSymbol:
        embedding = node.get("embedding") or []
        if isinstance(embedding, str):
            embedding = json.loads(embedding)
        return GraphSymbol(
            id=node["id"],
            scope=scope,
            kind=SymbolKind(node["kind"]),
            file_path=node["file_path"],
            name=node["name"],
            qualified_name=node["qualified_name"],
            signature=node["signature"],
            body=node["body"],
            hash_value=node["hash_value"],
            ai_documentation=node["ai_documentation"],
            doc_status=DocStatus(node["doc_status"]),
            embedding=list(embedding),
            visibility=node["visibility"],
            version=int(node["version"]),
            created_at=str(node["created_at"]),
            updated_at=str(node["updated_at"]),
        )

    def get_symbol(self, symbol_id: str, scope: Scope) -> GraphSymbol:
        with self._driver.session(database=self._database) as session:
            record = session.run(
                """
                MATCH (n:CodeSymbol {id: $id})
                WHERE n.tenant_id = $tenant_id
                  AND n.workspace_id = $workspace_id
                  AND n.project_id = $project_id
                RETURN n
                """,
                id=symbol_id,
                tenant_id=scope.tenant_id,
                workspace_id=scope.workspace_id,
                project_id=scope.project_id,
            ).single()
        if record is None:
            raise NotFoundError("symbol not found in project scope")
        return self._symbol_from_node(record["n"], scope)

    def put_symbol(self, symbol: GraphSymbol) -> None:
        scope = symbol.scope
        with self._driver.session(database=self._database) as session:
            session.run(
                """
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
                    n.updated_at = $updated_at
                """,
                id=symbol.id,
                tenant_id=scope.tenant_id,
                workspace_id=scope.workspace_id,
                project_id=scope.project_id,
                project_group_id=scope.project_group_id,
                kind=symbol.kind.value,
                file_path=symbol.file_path,
                name=symbol.name,
                qualified_name=symbol.qualified_name,
                signature=symbol.signature,
                body=symbol.body,
                hash_value=symbol.hash_value,
                ai_documentation=symbol.ai_documentation,
                doc_status=symbol.doc_status.value,
                embedding=list(symbol.embedding),
                visibility=symbol.visibility,
                version=symbol.version,
                created_at=symbol.created_at,
                updated_at=symbol.updated_at,
            )

    def list_symbols(self, scope: Scope) -> list[GraphSymbol]:
        with self._driver.session(database=self._database) as session:
            rows = list(
                session.run(
                    """
                    MATCH (n:CodeSymbol)
                    WHERE n.tenant_id = $tenant_id
                      AND n.workspace_id = $workspace_id
                      AND n.project_id = $project_id
                    RETURN n
                    ORDER BY n.qualified_name, n.id
                    """,
                    tenant_id=scope.tenant_id,
                    workspace_id=scope.workspace_id,
                    project_id=scope.project_id,
                )
            )
        return [self._symbol_from_node(row["n"], scope) for row in rows]

    def get_symbol_by_qualified_name(self, scope: Scope, qualified_name: str) -> GraphSymbol | None:
        with self._driver.session(database=self._database) as session:
            record = session.run(
                """
                MATCH (n:CodeSymbol)
                WHERE n.tenant_id = $tenant_id
                  AND n.workspace_id = $workspace_id
                  AND n.project_id = $project_id
                  AND n.qualified_name = $qualified_name
                RETURN n
                LIMIT 1
                """,
                tenant_id=scope.tenant_id,
                workspace_id=scope.workspace_id,
                project_id=scope.project_id,
                qualified_name=qualified_name,
            ).single()
        if record is None:
            return None
        return self._symbol_from_node(record["n"], scope)

    def delete_file_edges(self, scope: Scope, file_path: str) -> None:
        with self._driver.session(database=self._database) as session:
            session.run(
                f"""
                MATCH ()-[r:{_REL}]->()
                WHERE r.tenant_id = $tenant_id
                  AND r.workspace_id = $workspace_id
                  AND r.project_id = $project_id
                  AND r.file_path = $file_path
                DELETE r
                """,
                tenant_id=scope.tenant_id,
                workspace_id=scope.workspace_id,
                project_id=scope.project_id,
                file_path=file_path,
            )

    def delete_edge(self, scope: Scope, edge_id: str) -> None:
        with self._driver.session(database=self._database) as session:
            session.run(
                f"""
                MATCH ()-[r:{_REL} {{id: $id}}]->()
                WHERE r.tenant_id = $tenant_id
                  AND r.workspace_id = $workspace_id
                  AND r.project_id = $project_id
                DELETE r
                """,
                id=edge_id,
                tenant_id=scope.tenant_id,
                workspace_id=scope.workspace_id,
                project_id=scope.project_id,
            )

    def put_edge(self, edge: GraphEdge) -> None:
        scope = edge.scope
        metadata = dict(edge.metadata or {})
        file_path = str(metadata.get("file_path") or "")
        with self._driver.session(database=self._database) as session:
            session.run(
                f"""
                MATCH (source:CodeSymbol {{id: $source_id}})
                MATCH (target:CodeSymbol {{id: $target_id}})
                MERGE (source)-[r:{_REL} {{id: $id}}]->(target)
                SET r.tenant_id = $tenant_id,
                    r.workspace_id = $workspace_id,
                    r.project_id = $project_id,
                    r.project_group_id = $project_group_id,
                    r.rel_type = $rel_type,
                    r.confidence = $confidence,
                    r.file_path = $file_path,
                    r.metadata_json = $metadata_json
                """,
                id=edge.id,
                source_id=edge.source_id,
                target_id=edge.target_id,
                tenant_id=scope.tenant_id,
                workspace_id=scope.workspace_id,
                project_id=scope.project_id,
                project_group_id=scope.project_group_id,
                rel_type=edge.rel_type,
                confidence=edge.confidence.value,
                file_path=file_path,
                metadata_json=json.dumps(metadata, sort_keys=True),
            )

    def list_edges(self, scope: Scope) -> list[GraphEdge]:
        with self._driver.session(database=self._database) as session:
            rows = list(
                session.run(
                    f"""
                    MATCH (source:CodeSymbol)-[r:{_REL}]->(target:CodeSymbol)
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
                    """,
                    tenant_id=scope.tenant_id,
                    workspace_id=scope.workspace_id,
                    project_id=scope.project_id,
                )
            )
        return [
            GraphEdge(
                id=row["id"],
                scope=scope,
                rel_type=row["rel_type"],
                source_id=row["source_id"],
                target_id=row["target_id"],
                confidence=CallConfidence(row["confidence"]),
                metadata=json.loads(row["metadata_json"] or "{}"),
            )
            for row in rows
        ]

    def begin_idempotency(self, scope: Scope, key: str, resource: str) -> str | None:
        with self._driver.session(database=self._database) as session:
            record = session.run(
                """
                MATCH (n:CodeIdempotency {
                    scope_key: $scope_key,
                    idempotency_key: $idempotency_key,
                    resource_type: $resource_type
                })
                RETURN n.resource_id AS resource_id
                """,
                scope_key=self._scope_key(scope),
                idempotency_key=key,
                resource_type=resource,
            ).single()
        return None if record is None else record["resource_id"]

    def complete_idempotency(self, scope: Scope, key: str, resource: str, resource_id: str) -> None:
        with self._driver.session(database=self._database) as session:
            record = session.run(
                """
                MERGE (n:CodeIdempotency {
                    scope_key: $scope_key,
                    idempotency_key: $idempotency_key,
                    resource_type: $resource_type
                })
                ON CREATE SET n.resource_id = $resource_id
                RETURN n.resource_id AS resource_id
                """,
                scope_key=self._scope_key(scope),
                idempotency_key=key,
                resource_type=resource,
                resource_id=resource_id,
            ).single()
        if record is None or record["resource_id"] != resource_id:
            raise ConflictError("idempotency key already bound to another resource")

    def append_event(self, event: dict[str, Any]) -> None:
        with self._driver.session(database=self._database) as session:
            session.run(
                """
                CREATE (n:CodeOutboxEvent {
                    event_id: $event_id,
                    event_type: $event_type,
                    payload_json: $payload_json,
                    created_at: datetime()
                })
                """,
                event_id=event["event_id"],
                event_type=event["event_type"],
                payload_json=json.dumps(event, sort_keys=True),
            )

    def outbox(self) -> list[dict[str, Any]]:
        with self._driver.session(database=self._database) as session:
            rows = list(
                session.run(
                    """
                    MATCH (n:CodeOutboxEvent)
                    RETURN n.payload_json AS payload_json
                    ORDER BY n.created_at, n.event_id
                    """
                )
            )
        return [json.loads(row["payload_json"]) for row in rows]


def _lucene_query(raw: str) -> str:
    """Build a Lucene query: OR of sanitized tokens (fuzzy optional on long tokens)."""
    specials = set('+-&|!(){}[]^"~*?:\\/')
    tokens: list[str] = []
    for part in raw.replace(".", " ").replace("/", " ").split():
        cleaned = "".join(ch for ch in part if ch not in specials).strip()
        if len(cleaned) < 2:
            continue
        if len(cleaned) >= 5:
            tokens.append(f"{cleaned}~1")
        else:
            tokens.append(cleaned)
    return " OR ".join(tokens[:24])
