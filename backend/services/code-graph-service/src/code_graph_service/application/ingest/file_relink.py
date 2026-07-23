"""Relink unresolved CALLS / IMPORTS / INHERITS_FROM after peer symbols land."""

from __future__ import annotations

from ...domain.cross_language import build_symbol_indexes, resolve_call_target_polyglot, resolve_import_target
from ...domain.enums import CallConfidence
from ...domain.external_calls import classify_external_call, external_call_symbol_id
from ...domain.languages import detect_language_from_path
from ...domain.models import Scope
from ..support import unresolved_call_name


class FileRelinkMixin:
    """Late-binding for placeholders once more of the project graph exists."""

    def _relink_unresolved_calls(self, scope: Scope, *, source_language: str) -> int:
        """Re-resolve previously unresolved CALLS after new symbols land (polyglot).

        Also retags clearly-external unresolved placeholders to ``ext:call:``.
        """
        indexes = build_symbol_indexes(self.store.list_symbols(scope))
        written = 0
        for edge in list(self.store.list_edges(scope)):
            if edge.rel_type != "CALLS":
                continue
            target = str(edge.target_id)
            if not target.startswith("unresolved:"):
                continue
            call = str(edge.metadata.get("call") or unresolved_call_name(edge.target_id))
            external_kind = classify_external_call(call)
            if external_kind:
                self.store.delete_edge(scope, edge.id)
                written += self._put_edge(
                    scope,
                    "CALLS",
                    edge.source_id,
                    external_call_symbol_id(scope.project_id, call),
                    file_path=str(edge.metadata.get("file_path") or ""),
                    confidence=CallConfidence.EXTERNAL,
                    metadata={
                        "call": call,
                        "is_external": True,
                        "external_kind": external_kind,
                        "relinked": True,
                        "cross_language": False,
                    },
                    link_key=f"call:{call}",
                )
                continue
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
