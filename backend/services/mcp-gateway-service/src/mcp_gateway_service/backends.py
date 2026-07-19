from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[5]
SERVICES = ROOT / "backend" / "services"
PACKAGES = ROOT / "backend" / "packages"


def _ensure_path(path: Path) -> None:
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)


for _path in (
    PACKAGES,
    SERVICES / "core-data-service" / "src",
    SERVICES / "memory-service" / "src",
    SERVICES / "code-graph-service" / "src",
    SERVICES / "docs-sync-service" / "src",
):
    _ensure_path(_path)


from code_graph_service.core import CodeGraphService, Scope as GraphScope  # noqa: E402
from core_data_service.core import CoreData, Kind, Scope as CoreScope  # noqa: E402
from docs_sync_service.core import DocsSyncService, Scope as DocsScope  # noqa: E402
from memory_service.core import MemoryService, Scope as MemoryScope  # noqa: E402

from .store_factory import StoreBundle, build_stores  # noqa: E402


class PlatformBackends:
    """In-process AgentCore service facades used by the MCP gateway."""

    def __init__(self, stores: StoreBundle | None = None) -> None:
        self._stores = stores or build_stores()
        self.core = CoreData(self._stores.core)
        self.memory = MemoryService(self._stores.memory)
        self.graph = CodeGraphService(self._stores.graph)
        self.docs = DocsSyncService(self._stores.docs)
        self.actor_id = "mcp-gateway"
        self.store_mode = self._stores.mode

    @classmethod
    def from_env(cls, environ: dict[str, str] | None = None) -> PlatformBackends:
        return cls(build_stores(environ))

    def close(self) -> None:
        self._stores.close()

    def core_scope(self, scope: dict[str, str]) -> CoreScope:
        return CoreScope(scope["tenant_id"], scope["workspace_id"], scope["project_id"])

    def memory_scope(self, scope: dict[str, str]) -> MemoryScope:
        return MemoryScope(scope["tenant_id"], scope["workspace_id"], scope["project_id"])

    def graph_scope(self, scope: dict[str, str]) -> GraphScope:
        return GraphScope(scope["tenant_id"], scope["workspace_id"], scope["project_id"])

    def docs_scope(self, scope: dict[str, str]) -> DocsScope:
        return DocsScope(scope["tenant_id"], scope["workspace_id"], scope["project_id"])

    def ensure_memory_seed(self, scope: dict[str, str], query: str) -> None:
        mem_scope = self.memory_scope(scope)
        if self.memory.store.list_memory(mem_scope):
            return
        self.memory.create_memory(
            mem_scope,
            self.actor_id,
            str(uuid4()),
            f"seed-memory:{scope['project_id']}",
            {
                "kind": "semantic",
                "state": "active",
                "title": "Project coding conventions",
                "body": f"Prefer AgentCore scoped APIs and idempotency keys. Context query seed: {query}",
                "tags": ["programming", "conventions"],
                "evidence_refs": ["usage-profile:programming-cursor-mcp"],
                "source_refs": ["mcp-gateway"],
                "confidence": 0.95,
            },
        )

    def ensure_graph_seed(self, scope: dict[str, str]) -> None:
        graph_scope = self.graph_scope(scope)
        if self.graph.store.list_symbols(graph_scope):
            return
        self.graph.ingest_file(
            graph_scope,
            self.actor_id,
            str(uuid4()),
            f"seed-graph:{scope['project_id']}",
            {
                "file_path": "src/auth/hash.py",
                "language": "python",
                "source": (
                    "def hash_password(value: str) -> str:\n"
                    "    return value\n\n"
                    "def verify_password(value: str, hashed: str) -> bool:\n"
                    "    return hash_password(value) == hashed\n"
                ),
            },
        )

    def ensure_docs_symbol(self, scope: dict[str, str], symbol: str, file_path: str | None) -> str:
        docs_scope = self.docs_scope(scope)
        indexed = self.docs.index_symbol(
            docs_scope,
            self.actor_id,
            str(uuid4()),
            f"docs-symbol:{scope['project_id']}:{symbol}",
            {
                "repo": scope["project_id"],
                "file_path": file_path or "src/module.py",
                "symbol_path": symbol,
                "kind": "function",
                "body": f"def {symbol.split('.')[-1]}():\n    pass\n",
                "doc_required": True,
            },
        )
        return indexed.id


def dispatch_capability(
    backends: PlatformBackends,
    maps_to: str,
    arguments: dict[str, Any],
    *,
    scope: dict[str, str],
    usage_profile: str,
    correlation_id: str,
) -> dict[str, Any]:
    base = {
        "maps_to": maps_to,
        "usage_profile": usage_profile,
        "scope": scope,
        "correlation_id": correlation_id,
        "backend": "in_process",
        "store_mode": backends.store_mode,
    }
    if maps_to == "platform.ping":
        return {**base, "ok": True}
    if maps_to == "profile.effective":
        return {**base, "ok": True}

    if maps_to == "memory.retrieve":
        query = str(arguments.get("query") or "").strip()
        if not query:
            raise ValueError("query is required")
        backends.ensure_memory_seed(scope, query)
        bundle = backends.memory.retrieve_context(
            backends.memory_scope(scope),
            backends.actor_id,
            correlation_id,
            query,
        )
        public = bundle.public()
        return {
            **base,
            "query": query,
            "include_history": bool(arguments.get("include_history", False)),
            "bundle_id": public.get("bundle_id"),
            "items": public.get("items") or [],
            "excluded": public.get("excluded") or [],
        }

    if maps_to == "code_graph.search":
        query = str(arguments.get("query") or "").strip()
        if not query:
            raise ValueError("query is required")
        top_k = int(arguments.get("top_k") or 5)
        backends.ensure_graph_seed(scope)
        hits = backends.graph.semantic_search(backends.graph_scope(scope), query, top_k=top_k)
        return {**base, "query": query, "top_k": top_k, "symbols": hits}

    if maps_to == "core_data.create_task":
        title = str(arguments.get("title") or "").strip()
        if not title:
            raise ValueError("title is required")
        instructions = str(arguments.get("instructions") or "Implement via AgentCore MCP task").strip()
        record = backends.core.create(
            Kind.TASK,
            backends.core_scope(scope),
            backends.actor_id,
            correlation_id,
            f"mcp-task:{correlation_id}",
            {
                "title": title,
                "assignee_type": "backend",
                "instructions": instructions,
                "acceptance_criteria": ["Implemented", "Tests pass"],
            },
        )
        return {**base, "task": record.public()}

    if maps_to == "docs_sync.drift_check":
        symbol = str(arguments.get("symbol") or "").strip()
        if not symbol:
            raise ValueError("symbol is required")
        file_path = arguments.get("file_path")
        symbol_id = backends.ensure_docs_symbol(scope, symbol, str(file_path) if file_path else None)
        findings = backends.docs.detect_drift(
            backends.docs_scope(scope),
            backends.actor_id,
            correlation_id,
            f"mcp-drift:{correlation_id}",
            symbol_ids=[symbol_id],
        )
        return {
            **base,
            "symbol": symbol,
            "file_path": file_path,
            "symbol_id": symbol_id,
            "drift": bool(findings),
            "findings": [item.public() for item in findings],
        }

    raise ValueError(f"unmapped capability: {maps_to}")
