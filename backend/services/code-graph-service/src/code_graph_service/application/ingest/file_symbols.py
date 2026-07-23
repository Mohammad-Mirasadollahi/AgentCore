"""Upsert parsed symbols and living-documentation nodes for one file."""

from __future__ import annotations

from ...domain.enums import DocStatus, SymbolKind
from ...domain.hashing import digest, normalize_source
from ...domain.models import GraphSymbol, ParseResult, Scope


class FileSymbolsMixin:
    """Write FILE / code / DOCUMENTATION symbols and prune stale embeddings."""

    def _upsert_file_symbol(
        self,
        scope: Scope,
        *,
        file_id: str,
        file_path: str,
        source: str,
        file_hash: str,
        language: str,
        stamp: str,
        previous_file: GraphSymbol | None,
    ) -> GraphSymbol:
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
        return file_symbol

    def _upsert_parsed_symbols(
        self,
        scope: Scope,
        *,
        parsed: ParseResult,
        file_path: str,
        language: str,
        stamp: str,
    ) -> tuple[list[str], list[str], int, list[tuple[str, str]]]:
        """Return ``(symbol_ids, changed_ids, documented_count, documented_pairs)``."""
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
                version=(previous.version + 1)
                if previous and changed
                else (previous.version if previous else 1),
                created_at=previous.created_at if previous else stamp,
                updated_at=stamp,
                language=language,
            )
            self.store.put_symbol(symbol)
            self._index_embedding(scope, symbol_id, embed.vector, kind=item.kind.value)

        return symbol_ids, changed_ids, documented, documented_pairs

    def _prune_stale_file_embeddings(
        self,
        scope: Scope,
        *,
        file_path: str,
        file_id: str,
        symbol_ids: list[str],
        documented_pairs: list[tuple[str, str]],
    ) -> None:
        active_ids = set(symbol_ids) | {doc_id for _, doc_id in documented_pairs} | {file_id}
        for existing in self.store.list_symbols(scope):
            if existing.file_path != file_path:
                continue
            if existing.id in active_ids:
                continue
            if existing.kind == SymbolKind.FILE:
                continue
            self._delete_embedding(scope, existing.id)
