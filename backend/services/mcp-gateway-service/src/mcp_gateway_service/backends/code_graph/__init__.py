"""MCP capability handlers for the code-knowledge graph (modular)."""

from __future__ import annotations

from ._resolve import resolve_symbol_id
from .query import (
    architecture_overview,
    detect_changes,
    explore,
    freshness,
    generation_context,
    get_symbol,
    hybrid_search,
    impact,
    language_profile,
    neighbors,
    search,
    symbol_path,
)
from .write import ingest_file, ingest_repo, purge_scope, sync_repo

# Private alias kept for any internal callers.
_resolve_symbol_id = resolve_symbol_id

__all__ = [
    "_resolve_symbol_id",
    "architecture_overview",
    "detect_changes",
    "explore",
    "freshness",
    "generation_context",
    "get_symbol",
    "hybrid_search",
    "impact",
    "ingest_file",
    "ingest_repo",
    "language_profile",
    "neighbors",
    "purge_scope",
    "resolve_symbol_id",
    "search",
    "symbol_path",
    "sync_repo",
]
