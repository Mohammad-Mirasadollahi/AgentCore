"""Single-file ingest orchestration (symbols / edges / emissions / relink)."""

from __future__ import annotations

from typing import Any

from ...domain.errors import ValidationError
from ...domain.hashing import digest, normalize_source, now_iso
from ...domain.languages import assert_language_supported, detect_language_from_path
from ...domain.models import IngestResult, Scope
from ...domain.parsers import parse_source
from .file_edges import FileEdgesMixin
from .file_emissions import FileEmissionsMixin
from .file_relink import FileRelinkMixin
from .file_symbols import FileSymbolsMixin


class FileIngestMixin(
    FileSymbolsMixin,
    FileEdgesMixin,
    FileEmissionsMixin,
    FileRelinkMixin,
):
    """Parse one source file into symbols/edges via focused mixins."""

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
            language = assert_language_supported(
                detect_language_from_path(file_path) or "python"
            )
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
            clearer = getattr(self, "clear_pending_sync", None)
            if callable(clearer):
                clearer(file_path)
            self.store.complete_idempotency(scope, idempotency_key, "ingest_file", file_id)
            return IngestResult(file_id, 0, 0, 0, 0, [])

        self._upsert_file_symbol(
            scope,
            file_id=file_id,
            file_path=file_path,
            source=source,
            file_hash=file_hash,
            language=language,
            stamp=stamp,
            previous_file=previous_file,
        )

        parsed = parse_source(language, file_path, source)
        symbol_ids, changed_ids, documented, documented_pairs = self._upsert_parsed_symbols(
            scope,
            parsed=parsed,
            file_path=file_path,
            language=language,
            stamp=stamp,
        )
        self._prune_stale_file_embeddings(
            scope,
            file_path=file_path,
            file_id=file_id,
            symbol_ids=symbol_ids,
            documented_pairs=documented_pairs,
        )

        self.store.delete_file_edges(scope, file_path)
        edges_written = 0
        edges_written += self._emit_containment_and_doc_edges(
            scope,
            file_id=file_id,
            file_path=file_path,
            symbol_ids=symbol_ids,
            documented_pairs=documented_pairs,
        )

        indexes, by_qualified, short_names = self._resolution_indexes(scope)
        package_aliases = payload.get("package_aliases")
        if not isinstance(package_aliases, dict):
            package_aliases = {}

        edges_written += self._emit_import_edges(
            scope,
            parsed=parsed,
            file_id=file_id,
            file_path=file_path,
            language=language,
            stamp=stamp,
            indexes=indexes,
            package_aliases=package_aliases,
        )
        edges_written += self._emit_inherit_and_call_edges(
            scope,
            parsed=parsed,
            file_path=file_path,
            language=language,
            indexes=indexes,
            by_qualified=by_qualified,
            short_names=short_names,
        )

        edges_written += self._relink_unresolved_calls(scope, source_language=language)
        edges_written += self._relink_unresolved_references(
            scope,
            source_language=language,
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
