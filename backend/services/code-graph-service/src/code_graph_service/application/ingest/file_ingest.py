"""Single-file ingest and secondary graph emissions."""

from __future__ import annotations

from typing import Any

from ...domain.cross_language import (
    build_symbol_indexes,
    resolve_call_target_polyglot,
    resolve_import_target,
)
from ...domain.dispatch_synth import synthesize_interface_dispatch
from ...domain.enums import CallConfidence, DocStatus, RelType, SymbolKind
from ...domain.errors import ValidationError
from ...domain.framework_routes import extract_routes, route_symbol_id
from ...domain.freshness import extract_rationale_comments
from ...domain.hashing import digest, normalize_source, now_iso
from ...domain.languages import assert_language_supported, detect_language_from_path
from ...domain.models import (
    GraphSymbol,
    IngestResult,
    Scope,
)
from ...domain.parsers import parse_source
from ...domain.test_links import suggest_test_links
from ..support import unresolved_call_name, unresolved_symbol_id


class FileIngestMixin:
    """Parse one source file into symbols/edges."""

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
        raw_language = str(payload.get("language") or "").strip()
        if raw_language:
            language = assert_language_supported(raw_language)
        else:
            language = assert_language_supported(detect_language_from_path(file_path) or "python")
        if not file_path or not source:
            raise ValidationError("file_path and source are required")

        stamp = now_iso()
        file_hash = digest(normalize_source(source, language))
        file_id = f"file:{scope.project_id}:{file_path}"
        previous_file = self._maybe_get(file_id, scope)
        # Skip only when content is unchanged *and* language already persisted
        # (older graphs may lack language and need one re-ingest to backfill).
        if (
            previous_file is not None
            and previous_file.hash_value == file_hash
            and str(previous_file.language or "").strip()
        ):
            # Unchanged content: skip re-parse / re-embed (new idempotency keys each sync).
            clearer = getattr(self, "clear_pending_sync", None)
            if callable(clearer):
                clearer(file_path)
            self.store.complete_idempotency(scope, idempotency_key, "ingest_file", file_id)
            return IngestResult(file_id, 0, 0, 0, 0, [])

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
            language=language,
        )
        if previous_file is not None:
            file_symbol.version = previous_file.version + 1
            file_symbol.created_at = previous_file.created_at
        self.store.put_symbol(file_symbol)
        self._index_embedding(scope, file_id, file_embed.vector, kind=SymbolKind.FILE.value)

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
                    language=language,
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
                        language=language,
                    )
                )
                documented_pairs.append((symbol_id, doc_id))
                self._index_embedding(
                    scope,
                    doc_id,
                    self.embeddings.embed(doc).vector,
                    kind=SymbolKind.DOCUMENTATION.value,
                )
            elif previous and previous.ai_documentation:
                doc_id = f"doc:{scope.project_id}:{item.qualified_name}"
                doc_prev = self._maybe_get(doc_id, scope)
                if doc_prev is not None:
                    documented_pairs.append((symbol_id, doc_id))
                    if not str(doc_prev.language or "").strip():
                        doc_prev.language = language
                        doc_prev.updated_at = stamp
                        self.store.put_symbol(doc_prev)
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
                language=language,
            )
            self.store.put_symbol(symbol)
            self._index_embedding(scope, symbol_id, embed.vector, kind=item.kind.value)

        # Drop ANN rows for symbols that disappeared from this file path (lifecycle).
        active_ids = set(symbol_ids) | {doc_id for _, doc_id in documented_pairs} | {file_id}
        for existing in self.store.list_symbols(scope):
            if existing.file_path != file_path:
                continue
            if existing.id in active_ids:
                continue
            if existing.kind == SymbolKind.FILE:
                continue
            self._delete_embedding(scope, existing.id)

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

        indexes = build_symbol_indexes(self.store.list_symbols(scope))
        source_language = language
        package_aliases = payload.get("package_aliases")
        if not isinstance(package_aliases, dict):
            package_aliases = {}

        for item in parsed.symbols:
            if item.kind != SymbolKind.IMPORT:
                continue
            for imp in item.imports:
                target, confidence, cross_meta = resolve_import_target(
                    imp,
                    indexes,
                    source_language=source_language,
                    package_aliases=package_aliases,
                )
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
                            language=language,
                        )
                    )
                import_meta = {
                    "import_text": imp,
                    "is_external": target is None,
                    **cross_meta,
                }
                edges_written += self._put_edge(
                    scope,
                    "IMPORTS",
                    file_id,
                    target_id,
                    file_path=file_path,
                    confidence=confidence,
                    metadata=import_meta,
                    link_key=f"import:{imp}",
                )
                source_id = f"sym:{scope.project_id}:{item.qualified_name}"
                edges_written += self._put_edge(
                    scope,
                    "IMPORTS",
                    source_id,
                    target_id,
                    file_path=file_path,
                    confidence=confidence,
                    metadata=import_meta,
                    link_key=f"import:{imp}",
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
                        link_key=f"base:{base}",
                    )
                else:
                    edges_written += self._put_edge(
                        scope,
                        "INHERITS_FROM",
                        source_id,
                        unresolved_symbol_id(scope, base),
                        file_path=file_path,
                        confidence=CallConfidence.UNRESOLVED,
                        metadata={"base": base},
                        link_key=f"base:{base}",
                    )
            for call in item.calls:
                targets, confidence, cross_meta = resolve_call_target_polyglot(
                    call,
                    indexes=indexes,
                    import_aliases=parsed.import_aliases,
                    module_prefix=parsed.module_prefix,
                    source_language=source_language,
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
                            metadata={**cross_meta, "call": call},
                            link_key=f"call:{call}:{match}",
                        )
                elif targets:
                    edges_written += self._put_edge(
                        scope,
                        "CALLS",
                        source_id,
                        targets[0],
                        file_path=file_path,
                        confidence=confidence,
                        metadata={**cross_meta, "call": call},
                        link_key=f"call:{call}",
                    )
                else:
                    edges_written += self._put_edge(
                        scope,
                        "CALLS",
                        source_id,
                        unresolved_symbol_id(scope, call),
                        file_path=file_path,
                        confidence=CallConfidence.UNRESOLVED,
                        metadata={"call": call, "cross_language": False},
                        link_key=f"call:{call}",
                    )

        edges_written += self._relink_unresolved_calls(scope, source_language=source_language)
        edges_written += self._relink_unresolved_references(
            scope,
            source_language=source_language,
            package_aliases=package_aliases,
        )
        edges_written += self._emit_framework_routes(
            scope, file_path=file_path, source=source, language=language, stamp=stamp
        )
        edges_written += self._emit_test_links(scope)
        edges_written += self._emit_rationale_nodes(
            scope, file_path=file_path, source=source, stamp=stamp, language=language
        )
        edges_written += self._emit_dynamic_dispatch(scope)
        clearer = getattr(self, "clear_pending_sync", None)
        if callable(clearer):
            clearer(file_path)

        polyglot = self.get_polyglot_profile(scope)  # type: ignore[attr-defined]
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
                    "polyglot": {
                        "is_polyglot": polyglot.is_polyglot,
                        "languages": polyglot.languages,
                        "relatedness": polyglot.relatedness,
                        "cross_language_edge_count": polyglot.cross_language_edge_count,
                        "summary": polyglot.summary,
                    },
                },
            )
        )
        if polyglot.is_polyglot:
            self.store.append_event(
                self._event(
                    "ProjectLanguageProfileUpdated",
                    scope,
                    actor_id,
                    correlation_id,
                    idempotency_key,
                    polyglot.to_dict(),
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

    def _emit_framework_routes(
        self,
        scope: Scope,
        *,
        file_path: str,
        source: str,
        language: str,
        stamp: str,
    ) -> int:
        """Create ROUTE symbols and ROUTES_TO edges for framework handlers."""
        written = 0
        by_name: dict[str, list[str]] = {}
        for sym in self.store.list_symbols(scope):
            if sym.kind in {SymbolKind.FUNCTION, SymbolKind.METHOD}:
                by_name.setdefault(sym.name, []).append(sym.id)

        for route in extract_routes(source, language=language, file_path=file_path):
            rid = route_symbol_id(scope.project_id, route.method, route.path)
            label = f"{route.method} {route.path}"
            self.store.put_symbol(
                GraphSymbol(
                    id=rid,
                    scope=scope,
                    kind=SymbolKind.ROUTE,
                    file_path=file_path,
                    name=label,
                    qualified_name=f"route:{route.method}:{route.path}",
                    signature=label,
                    body="",
                    hash_value=digest(label),
                    ai_documentation=f"{route.framework} route",
                    doc_status=DocStatus.UNCHANGED,
                    embedding=self.embeddings.embed(label).vector,
                    created_at=stamp,
                    updated_at=stamp,
                    language=language,
                )
            )
            handlers = by_name.get(route.handler_name, [])
            confidence = (
                CallConfidence.EXACT
                if len(handlers) == 1
                else CallConfidence.AMBIGUOUS
                if handlers
                else CallConfidence.UNRESOLVED
            )
            if not handlers:
                target = unresolved_symbol_id(scope, route.handler_name)
                written += self._put_edge(
                    scope,
                    RelType.ROUTES_TO.value,
                    rid,
                    target,
                    file_path=file_path,
                    confidence=confidence,
                    metadata={
                        "framework": route.framework,
                        "method": route.method,
                        "path": route.path,
                        "handler": route.handler_name,
                        "line": route.line_hint,
                        "provenance": "framework_route",
                    },
                    link_key=f"route:{route.method}:{route.path}:{route.handler_name}",
                )
            else:
                for hid in handlers[:5]:
                    written += self._put_edge(
                        scope,
                        RelType.ROUTES_TO.value,
                        rid,
                        hid,
                        file_path=file_path,
                        confidence=confidence,
                        metadata={
                            "framework": route.framework,
                            "method": route.method,
                            "path": route.path,
                            "handler": route.handler_name,
                            "line": route.line_hint,
                            "provenance": "framework_route",
                        },
                        link_key=f"route:{route.method}:{route.path}:{hid}",
                    )
        return written

    def _emit_test_links(self, scope: Scope) -> int:
        """Emit convention-based TESTED_BY edges (production → test)."""
        triples: list[tuple[str, str, str]] = []
        id_by_qn: dict[str, str] = {}
        for sym in self.store.list_symbols(scope):
            if sym.kind not in {SymbolKind.FUNCTION, SymbolKind.METHOD, SymbolKind.CLASS}:
                continue
            triples.append((sym.qualified_name, sym.name, sym.file_path))
            id_by_qn[sym.qualified_name] = sym.id

        written = 0
        for link in suggest_test_links(triples):
            src = id_by_qn.get(link.production_name)
            tgt = id_by_qn.get(link.test_name)
            if not src or not tgt:
                continue
            written += self._put_edge(
                scope,
                RelType.TESTED_BY.value,
                src,
                tgt,
                file_path="",
                confidence=CallConfidence.PROBABLE,
                metadata={"reason": link.reason, "provenance": "test_convention"},
                link_key=f"tested_by:{src}:{tgt}",
            )
        return written

    def _emit_rationale_nodes(
        self,
        scope: Scope,
        *,
        file_path: str,
        source: str,
        stamp: str,
        language: str = "",
    ) -> int:
        """Extract WHY/NOTE/HACK comments as RATIONALE symbols linked DOCUMENTED_BY from file."""
        written = 0
        file_id = f"file:{scope.project_id}:{file_path}"
        for hit in extract_rationale_comments(source):
            rid = f"rationale:{scope.project_id}:{file_path}:{hit.line}:{hit.tag}"
            body = f"{hit.tag}: {hit.body}"
            self.store.put_symbol(
                GraphSymbol(
                    id=rid,
                    scope=scope,
                    kind=SymbolKind.RATIONALE,
                    file_path=file_path,
                    name=f"{hit.tag}:{hit.line}",
                    qualified_name=f"{file_path}::{hit.tag}@{hit.line}",
                    signature=hit.tag,
                    body=body,
                    hash_value=digest(body),
                    ai_documentation=body,
                    doc_status=DocStatus.UNCHANGED,
                    embedding=self.embeddings.embed(body).vector,
                    created_at=stamp,
                    updated_at=stamp,
                    language=language,
                )
            )
            written += self._put_edge(
                scope,
                RelType.DOCUMENTED_BY.value,
                file_id,
                rid,
                file_path=file_path,
                confidence=CallConfidence.EXACT,
                metadata={"tag": hit.tag, "line": hit.line, "provenance": "rationale_comment"},
                link_key=f"rationale:{hit.line}:{hit.tag}",
            )
        return written

    def _emit_dynamic_dispatch(self, scope: Scope) -> int:
        symbols = list(self.store.list_symbols(scope))
        edges = list(self.store.list_edges(scope))
        sym_tuples = [(s.id, s.name, s.qualified_name, s.kind.value) for s in symbols]
        inherits = [
            (e.source_id, e.target_id)
            for e in edges
            if e.rel_type in {RelType.INHERITS_FROM.value, "INHERITS_FROM"}
        ]
        calls = [
            (e.source_id, e.target_id, str(e.metadata.get("call") or ""))
            for e in edges
            if e.rel_type in {RelType.CALLS.value, "CALLS"}
        ]
        written = 0
        for synth in synthesize_interface_dispatch(
            symbols=sym_tuples, inherits=inherits, calls=calls
        ):
            written += self._put_edge(
                scope,
                RelType.CALLS.value,
                synth.source_id,
                synth.target_id,
                file_path="",
                confidence=CallConfidence.PROBABLE,
                metadata={
                    "call": synth.method_name,
                    "provenance": synth.provenance,
                    "via_type": synth.via_type,
                    "synthesizedBy": "dynamic_dispatch",
                },
                link_key=f"dispatch:{synth.source_id}:{synth.target_id}:{synth.method_name}",
            )
        return written

    def _relink_unresolved_calls(self, scope: Scope, *, source_language: str) -> int:
        """Re-resolve previously unresolved CALLS after new symbols land (polyglot)."""
        indexes = build_symbol_indexes(self.store.list_symbols(scope))
        written = 0
        for edge in list(self.store.list_edges(scope)):
            if edge.rel_type != "CALLS" or not str(edge.target_id).startswith("unresolved:"):
                continue
            call = str(edge.metadata.get("call") or unresolved_call_name(edge.target_id))
            edge_language = (
                detect_language_from_path(str(edge.metadata.get("file_path") or ""))
                or source_language
            )
            targets, confidence, cross_meta = resolve_call_target_polyglot(
                call,
                indexes=indexes,
                import_aliases={},
                module_prefix="",
                source_language=edge_language,
            )
            if not targets or confidence == CallConfidence.UNRESOLVED:
                continue
            self.store.delete_edge(scope, edge.id)
            if confidence == CallConfidence.AMBIGUOUS:
                for match in targets:
                    written += self._put_edge(
                        scope,
                        "CALLS",
                        edge.source_id,
                        match,
                        file_path=str(edge.metadata.get("file_path") or ""),
                        confidence=CallConfidence.AMBIGUOUS,
                        metadata={**cross_meta, "call": call, "relinked": True},
                        link_key=f"call:{call}:{match}",
                    )
            else:
                written += self._put_edge(
                    scope,
                    "CALLS",
                    edge.source_id,
                    targets[0],
                    file_path=str(edge.metadata.get("file_path") or ""),
                    confidence=confidence,
                    metadata={**cross_meta, "call": call, "relinked": True},
                    link_key=f"call:{call}",
                )
        return written

    def _relink_unresolved_references(
        self,
        scope: Scope,
        *,
        source_language: str,
        package_aliases: dict[str, str],
    ) -> int:
        indexes = build_symbol_indexes(self.store.list_symbols(scope))
        by_qualified = indexes.by_qualified
        written = 0
        for edge in list(self.store.list_edges(scope)):
            file_path = str(edge.metadata.get("file_path") or "")
            edge_language = detect_language_from_path(file_path) or source_language
            if edge.rel_type == "IMPORTS" and str(edge.target_id).startswith("ext:"):
                import_text = str(edge.metadata.get("import_text") or "")
                target, confidence, cross_meta = resolve_import_target(
                    import_text,
                    indexes,
                    source_language=edge_language,
                    package_aliases=package_aliases,
                )
                if target is None:
                    continue
                self.store.delete_edge(scope, edge.id)
                written += self._put_edge(
                    scope,
                    "IMPORTS",
                    edge.source_id,
                    target,
                    file_path=file_path,
                    confidence=confidence,
                    metadata={
                        **edge.metadata,
                        **cross_meta,
                        "is_external": False,
                        "relinked": True,
                    },
                    link_key=f"import:{import_text}",
                )
            elif edge.rel_type == "INHERITS_FROM" and str(edge.target_id).startswith(
                "unresolved:"
            ):
                base = str(edge.metadata.get("base") or "")
                target = by_qualified.get(base) or (indexes.short_names.get(base, [None])[0])
                if target is None:
                    continue
                self.store.delete_edge(scope, edge.id)
                written += self._put_edge(
                    scope,
                    "INHERITS_FROM",
                    edge.source_id,
                    target,
                    file_path=file_path,
                    confidence=CallConfidence.EXACT,
                    metadata={"base": base, "relinked": True},
                    link_key=f"base:{base}",
                )
        return written
