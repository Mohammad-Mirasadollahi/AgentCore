"""Stage-1 hybrid RAG constants for code-graph retrieval (pgvector + Neo4j expand).

turbovec / VectorIndexPort are explicitly out of scope for Stage-1.
"""

from __future__ import annotations

from .enums import SymbolKind

# Indexed and returned by semantic_search (SQL filter before ANN when using pgvector).
SEARCHABLE_SYMBOL_KINDS: frozenset[str] = frozenset(
    {
        SymbolKind.CLASS.value,
        SymbolKind.FUNCTION.value,
        SymbolKind.METHOD.value,
        SymbolKind.DOCUMENTATION.value,
    }
)

# Default hybrid expand: top-N vector seeds get neighborhood attached.
DEFAULT_EXPAND_SEEDS = 3
DEFAULT_EXPAND_DEPTH = 1
DEFAULT_EXPAND_EDGE_LIMIT = 8
