"""Application service: ingest, query, generation context, and validation use cases."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from ..domain.documentation import HeuristicDocGenerator
from ..domain.embeddings import LocalEmbeddingStub, cosine
from ..domain.enums import CallConfidence, DocStatus, SymbolKind
from ..domain.errors import NotFoundError, ValidationError
from ..domain.hashing import digest, normalize_source, now_iso
from ..domain.languages import assert_language_supported, assert_required_languages_supported
from ..domain.models import GraphEdge, GraphSymbol, IngestResult, Scope
from ..domain.parsers import parse_source
from ..domain.parsing import (
    builtin_names,
    defined_names,
    extract_call_refs,
    resolve_call_target,
)
from ..domain.ports import Store


class CodeGraphService:
    def __init__(
        self,
        store: Store,
        docs: HeuristicDocGenerator | None = None,
        embeddings: LocalEmbeddingStub | None = None,
    ) -> None:
        assert_required_languages_supported()
        self.store = store
        self.docs = docs or HeuristicDocGenerator()
        self.embeddings = embeddings or LocalEmbeddingStub()

    def ingest_file(
        self,
        scope: Scope,
        actor_id: str,
        correlation_id: str,
        idempotency_key: str,
        payload: dict[str, Any],
    ) -> IngestResult:
        existing = self.store.begin_idempotency(scope, idempotency_key, "ingest_file")
        if existing is not None:
            file_symbol = self.store.get_symbol(existing, scope)
            return IngestResult(file_symbol.id, 0, 0, 0, 0, [])

        file_path = str(payload.get("file_path") or "").strip()
        source = str(payload.get("source") or "")
        language = assert_language_supported(str(payload.get("language") or "python"))
        if not file_path or not source:
            raise ValidationError("file_path and source are required")

        stamp = now_iso()
        file_hash = digest(normalize_source(source, language))
        file_id = f"file:{scope.project_id}:{file_path}"
        file_embed = self.embeddings.embed(file_path)
        file_symbol = GraphSymbol(
            id=file_id,
            scope=scope,
            kind=SymbolKind.FILE,
            file_path=file_path,
            name=file_path.rsplit("/", 1)[-1],
            qualified_name=file_path,
            signature=file_path,
            body=source,
            hash_value=file_hash,
            ai_documentation="",
            doc_status=DocStatus.UNCHANGED,
            embedding=file_embed.vector,
            created_at=stamp,
            updated_at=stamp,
        )
        previous_file = self._maybe_get(file_id, scope)
        if previous_file is not None:
            file_symbol.version = previous_file.version + 1
            file_symbol.created_at = previous_file.created_at
        self.store.put_symbol(file_symbol)

        parsed = parse_source(language, file_path, source)
        changed_ids: list[str] = []
        documented = 0
        symbol_ids: list[str] = []
        documented_pairs: list[tuple[str, str]] = []

        for item in parsed.symbols:
            symbol_id = f"sym:{scope.project_id}:{item.qualified_name}"
            symbol_ids.append(symbol_id)
            hash_value = digest(normalize_source(item.body, language))
            previous = self._maybe_get(symbol_id, scope)
            changed = previous is None or previous.hash_value != hash_value
            neighbors = item.calls + item.bases + item.imports
            doc = previous.ai_documentation if previous and not changed else ""
            status = DocStatus.UNCHANGED
            if changed:
                changed_ids.append(symbol_id)
                draft = GraphSymbol(
                    id=symbol_id,
                    scope=scope,
                    kind=item.kind,
                    file_path=file_path,
                    name=item.name,
                    qualified_name=item.qualified_name,
                    signature=item.signature,
                    body=item.body,
                    hash_value=hash_value,
                    ai_documentation="",
                    doc_status=DocStatus.MISSING,
                    embedding=[],
                    visibility=item.visibility,
                    version=(previous.version + 1) if previous else 1,
                    created_at=previous.created_at if previous else stamp,
                    updated_at=stamp,
                )
                doc = self.docs.generate(draft, neighbors)
                status = DocStatus.GENERATED
                documented += 1
                doc_id = f"doc:{scope.project_id}:{item.qualified_name}"
                self.store.put_symbol(
                    GraphSymbol(
                        id=doc_id,
                        scope=scope,
                        kind=SymbolKind.DOCUMENTATION,
                        file_path=file_path,
                        name=f"{item.name}.md",
                        qualified_name=f"{item.qualified_name}::__doc__",
                        signature=item.signature,
                        body=doc,
                        hash_value=digest(doc),
                        ai_documentation=doc,
                        doc_status=DocStatus.GENERATED,
                        embedding=self.embeddings.embed(doc).vector,
                        created_at=stamp,
                        updated_at=stamp,
                    )
                )
                documented_pairs.append((symbol_id, doc_id))
            elif previous and previous.ai_documentation:
                doc_id = f"doc:{scope.project_id}:{item.qualified_name}"
                if self._maybe_get(doc_id, scope) is not None:
                    documented_pairs.append((symbol_id, doc_id))
            embed = self.embeddings.embed(f"{item.qualified_name}\n{doc}")
            symbol = GraphSymbol(
                id=symbol_id,
                scope=scope,
                kind=item.kind,
                file_path=file_path,
                name=item.name,
                qualified_name=item.qualified_name,
                signature=item.signature,
                body=item.body,
                hash_value=hash_value,
                ai_documentation=doc,
                doc_status=status if changed else DocStatus.UNCHANGED,
                embedding=embed.vector,
                visibility=item.visibility,
                version=(previous.version + 1) if previous and changed else (previous.version if previous else 1),
                created_at=previous.created_at if previous else stamp,
                updated_at=stamp,
            )
            self.store.put_symbol(symbol)

        self.store.delete_file_edges(scope, file_path)
        edges_written = 0
        for symbol_id in symbol_ids:
            edges_written += self._put_edge(scope, "CONTAINS", file_id, symbol_id, file_path=file_path)
        for symbol_id, doc_id in documented_pairs:
            edges_written += self._put_edge(scope, "DOCUMENTED_BY", symbol_id, doc_id, file_path=file_path)

        by_qualified = {
            s.qualified_name: s.id
            for s in self.store.list_symbols(scope)
            if s.kind not in {SymbolKind.FILE, SymbolKind.DOCUMENTATION}
        }
        short_names: dict[str, list[str]] = {}
        for s in self.store.list_symbols(scope):
            if s.kind in {SymbolKind.FILE, SymbolKind.DOCUMENTATION, SymbolKind.IMPORT}:
                continue
            short_names.setdefault(s.name, []).append(s.id)

        for item in parsed.symbols:
            if item.kind != SymbolKind.IMPORT:
                continue
            for imp in item.imports:
                target = by_qualified.get(imp)
                confidence = CallConfidence.EXACT if target else CallConfidence.UNRESOLVED
                target_id = target or f"ext:{imp}"
                if target is None and self._maybe_get(target_id, scope) is None:
                    self.store.put_symbol(
                        GraphSymbol(
                            id=target_id,
                            scope=scope,
                            kind=SymbolKind.IMPORT,
                            file_path=file_path,
                            name=imp,
                            qualified_name=imp,
                            signature=imp,
                            body=imp,
                            hash_value=digest(imp),
                            ai_documentation="external import",
                            doc_status=DocStatus.UNCHANGED,
                            embedding=self.embeddings.embed(imp).vector,
                            created_at=stamp,
                            updated_at=stamp,
                        )
                    )
                edges_written += self._put_edge(
                    scope,
                    "IMPORTS",
                    file_id,
                    target_id,
                    file_path=file_path,
                    confidence=confidence,
                    metadata={"import_text": imp, "is_external": target is None},
                )
                source_id = f"sym:{scope.project_id}:{item.qualified_name}"
                edges_written += self._put_edge(
                    scope,
                    "IMPORTS",
                    source_id,
                    target_id,
                    file_path=file_path,
                    confidence=confidence,
                    metadata={"import_text": imp, "is_external": target is None},
                )

        for item in parsed.symbols:
            source_id = f"sym:{scope.project_id}:{item.qualified_name}"
            for base in item.bases:
                target = by_qualified.get(base) or (short_names.get(base, [None])[0])
                if target:
                    edges_written += self._put_edge(
                        scope,
                        "INHERITS_FROM",
                        source_id,
                        target,
                        file_path=file_path,
                        confidence=CallConfidence.EXACT,
                    )
            for call in item.calls:
                targets, confidence = resolve_call_target(
                    call,
                    by_qualified=by_qualified,
                    short_names=short_names,
                    import_aliases=parsed.import_aliases,
                    module_prefix=parsed.module_prefix,
                )
                if confidence == CallConfidence.AMBIGUOUS and targets:
                    for match in targets:
                        edges_written += self._put_edge(
                            scope,
                            "CALLS",
                            source_id,
                            match,
                            file_path=file_path,
                            confidence=CallConfidence.AMBIGUOUS,
                        )
                elif targets:
                    edges_written += self._put_edge(
                        scope,
                        "CALLS",
                        source_id,
                        targets[0],
                        file_path=file_path,
                        confidence=confidence,
                    )
                else:
                    edges_written += self._put_edge(
                        scope,
                        "CALLS",
                        source_id,
                        f"unresolved:{call}",
                        file_path=file_path,
                        confidence=CallConfidence.UNRESOLVED,
                    )

        self.store.append_event(
            self._event(
                "FileIngested",
                scope,
                actor_id,
                correlation_id,
                idempotency_key,
                {
                    "file_id": file_id,
                    "file_path": file_path,
                    "language": language,
                    "symbols_indexed": len(symbol_ids) + 1,
                    "symbols_changed": len(changed_ids),
                    "symbols_documented": documented,
                },
            )
        )
        if changed_ids:
            self.store.append_event(
                self._event(
                    "SymbolsDocumented",
                    scope,
                    actor_id,
                    correlation_id,
                    idempotency_key,
                    {"symbol_ids": changed_ids, "count": documented},
                )
            )
        self.store.complete_idempotency(scope, idempotency_key, "ingest_file", file_id)
        return IngestResult(
            file_id=file_id,
            symbols_indexed=len(symbol_ids) + 1,
            symbols_changed=len(changed_ids),
            symbols_documented=documented,
            edges_written=edges_written,
            changed_symbol_ids=changed_ids,
        )

    def get_symbol(self, scope: Scope, symbol_id: str) -> GraphSymbol:
        return self.store.get_symbol(symbol_id, scope)

    def list_changed_since(self, scope: Scope, previous_hashes: dict[str, str]) -> list[GraphSymbol]:
        changed: list[GraphSymbol] = []
        for symbol in self.store.list_symbols(scope):
            if symbol.kind in {SymbolKind.FILE, SymbolKind.DOCUMENTATION}:
                continue
            prior = previous_hashes.get(symbol.qualified_name)
            if prior is None or prior != symbol.hash_value:
                changed.append(symbol)
        return changed

    def structural_query(self, scope: Scope, symbol_id: str, rel_type: str | None = None) -> dict[str, Any]:
        symbol = self.store.get_symbol(symbol_id, scope)
        edges = [
            edge
            for edge in self.store.list_edges(scope)
            if edge.source_id == symbol_id or edge.target_id == symbol_id
        ]
        if rel_type:
            edges = [edge for edge in edges if edge.rel_type == rel_type.upper()]
        return {
            "symbol": self._symbol_view(symbol),
            "edges": [
                {
                    "id": edge.id,
                    "rel_type": edge.rel_type,
                    "source_id": edge.source_id,
                    "target_id": edge.target_id,
                    "confidence": edge.confidence.value,
                    "metadata": edge.metadata,
                }
                for edge in edges
            ],
        }

    def semantic_search(self, scope: Scope, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if not query.strip():
            raise ValidationError("query is required")
        vector = self.embeddings.embed(query).vector
        scored: list[tuple[float, GraphSymbol]] = []
        for symbol in self.store.list_symbols(scope):
            if symbol.kind in {SymbolKind.FILE, SymbolKind.IMPORT}:
                continue
            scored.append((cosine(vector, symbol.embedding), symbol))
        scored.sort(key=lambda item: (-item[0], item[1].qualified_name))
        return [
            {"score": round(score, 6), "symbol": self._symbol_view(symbol)}
            for score, symbol in scored[: max(1, top_k)]
            if score > 0
        ]

    def build_generation_context(self, scope: Scope, seed_symbol_id: str, max_symbols: int = 12) -> dict[str, Any]:
        seed = self.store.get_symbol(seed_symbol_id, scope)
        related_ids = {seed.id}
        for edge in self.store.list_edges(scope):
            if edge.source_id == seed.id:
                related_ids.add(edge.target_id)
            if edge.target_id == seed.id:
                related_ids.add(edge.source_id)
        symbols = []
        for symbol_id in sorted(related_ids):
            try:
                symbol = self.store.get_symbol(symbol_id, scope)
            except NotFoundError:
                continue
            if symbol.kind == SymbolKind.FILE:
                continue
            symbols.append(symbol)
            if len(symbols) >= max_symbols:
                break
        prompt_parts = [
            "Use only the following graph context. Do not assume repository-wide source.",
            f"Seed: {seed.qualified_name}",
        ]
        for symbol in symbols:
            prompt_parts.append(
                f"- {symbol.kind.value} {symbol.qualified_name}: {symbol.signature}\n"
                f"  doc: {symbol.ai_documentation.splitlines()[0] if symbol.ai_documentation else 'n/a'}"
            )
        return {
            "seed_symbol_id": seed.id,
            "symbol_count": len(symbols),
            "uses_full_repository": False,
            "prompt_context": "\n".join(prompt_parts),
            "symbols": [self._symbol_view(symbol) for symbol in symbols],
        }

    def validate_generated_code(self, scope: Scope, source: str) -> dict[str, Any]:
        if not source.strip():
            raise ValidationError("source is required")
        symbols = self.store.list_symbols(scope)
        known = {symbol.name for symbol in symbols}
        known.update(symbol.qualified_name for symbol in symbols)
        known.update(builtin_names())
        known.update(defined_names(source))
        call_refs = extract_call_refs(source)
        unknown = sorted(
            {
                ref
                for ref in call_refs
                if ref not in known and ref.split(".")[-1] not in known and not ref.startswith("__")
            }
        )
        return {
            "accepted": len(unknown) == 0,
            "unknown_symbols": unknown,
            "known_symbol_count": len(known),
            "checked_call_refs": sorted(call_refs),
        }

    def _put_edge(
        self,
        scope: Scope,
        rel_type: str,
        source_id: str,
        target_id: str,
        *,
        file_path: str,
        confidence: CallConfidence = CallConfidence.EXACT,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        meta = {"file_path": file_path}
        if metadata:
            meta.update(metadata)
        edge = GraphEdge(
            id=f"edge:{digest(f'{rel_type}|{source_id}|{target_id}')[:16]}",
            scope=scope,
            rel_type=rel_type,
            source_id=source_id,
            target_id=target_id,
            confidence=confidence,
            metadata=meta,
        )
        self.store.put_edge(edge)
        return 1

    def _maybe_get(self, symbol_id: str, scope: Scope) -> GraphSymbol | None:
        try:
            return self.store.get_symbol(symbol_id, scope)
        except NotFoundError:
            return None

    @staticmethod
    def _symbol_view(symbol: GraphSymbol) -> dict[str, Any]:
        return {
            "id": symbol.id,
            "kind": symbol.kind.value,
            "file_path": symbol.file_path,
            "name": symbol.name,
            "qualified_name": symbol.qualified_name,
            "signature": symbol.signature,
            "hash_value": symbol.hash_value,
            "ai_documentation": symbol.ai_documentation,
            "doc_status": symbol.doc_status.value,
            "visibility": symbol.visibility,
            "version": symbol.version,
        }

    @staticmethod
    def _event(
        event_type: str,
        scope: Scope,
        actor_id: str,
        correlation_id: str,
        idempotency_key: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "event_id": str(uuid4()),
            "event_type": event_type,
            "event_version": "1",
            "occurred_at": now_iso(),
            "producer": "code-graph-service",
            "tenant_id": scope.tenant_id,
            "workspace_id": scope.workspace_id,
            "project_id": scope.project_id,
            "project_group_id": scope.project_group_id,
            "actor_ref": actor_id,
            "correlation_id": correlation_id,
            "causation_id": correlation_id,
            "idempotency_key": idempotency_key,
            "payload": payload,
            "evidence_refs": [],
        }
