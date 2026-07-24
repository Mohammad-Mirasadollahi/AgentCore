"""Neo4j CRUD Cypher strings live in a dedicated module."""

from __future__ import annotations

from code_graph_service.neo4j import cypher
from code_graph_service.neo4j.constants import REL


def test_cypher_module_exports_crud_queries():
    names = (
        "GET_SYMBOL",
        "PUT_SYMBOL",
        "DELETE_SYMBOL",
        "LIST_SYMBOLS",
        "LIST_SYMBOLS_FOR_FILE",
        "GET_SYMBOL_BY_QUALIFIED_NAME",
        "DELETE_FILE_EDGES",
        "DELETE_EDGE",
        "PUT_EDGE",
        "LIST_EDGES",
        "BEGIN_IDEMPOTENCY",
        "COMPLETE_IDEMPOTENCY",
        "APPEND_EVENT",
        "OUTBOX",
        "WIPE_SYMBOLS",
        "WIPE_EDGES",
        "WIPE_IDEMPOTENCY",
    )
    for name in names:
        value = getattr(cypher, name)
        assert isinstance(value, str)
        assert value.strip()


def test_edge_queries_use_shared_rel_constant():
    assert REL in cypher.PUT_EDGE
    assert REL in cypher.LIST_EDGES
    assert REL in cypher.DELETE_EDGE
    assert REL in cypher.DELETE_FILE_EDGES
    assert REL in cypher.WIPE_EDGES
