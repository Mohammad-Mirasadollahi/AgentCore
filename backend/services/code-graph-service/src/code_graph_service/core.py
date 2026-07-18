from __future__ import annotations

import ast
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
import re
from typing import Any, Protocol
from uuid import uuid4


class SymbolKind(StrEnum):
    FILE = "file"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    IMPORT = "import"


class CallConfidence(StrEnum):
    EXACT = "exact"
    PROBABLE = "probable"
    AMBIGUOUS = "ambiguous"
    UNRESOLVED = "unresolved"


class DocStatus(StrEnum):
    MISSING = "missing"
    GENERATED = "generated"
    UNCHANGED = "unchanged"


class CodeGraphError(Exception):
    def __init__(self, code: str, category: str, message: str):
        super().__init__(message)
        self.code, self.category, self.message = code, category, message


class ValidationError(CodeGraphError):
    def __init__(self, message: str):
        super().__init__("validation_error", "validation_error", message)


class NotFoundError(CodeGraphError):
    def __init__(self, message: str):
        super().__init__("not_found", "not_found_error", message)


class ConflictError(CodeGraphError):
    def __init__(self, message: str):
        super().__init__("conflict_error", "conflict_error", message)


@dataclass(frozen=True)
class Scope:
    tenant_id: str
    workspace_id: str
    project_id: str
    project_group_id: str | None = None

    def __post_init__(self) -> None:
        if not all((self.tenant_id.strip(), self.workspace_id.strip(), self.project_id.strip())):
            raise ValidationError("tenant_id, workspace_id, and project_id are required")


def digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def normalize_source(source: str) -> str:
    """Drop comment/whitespace noise so formatting-only edits keep the same hash."""
    lines: list[str] = []
    for raw in source.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if line.strip():
            lines.append(re.sub(r"\s+", " ", line.strip()))
    return "\n".join(lines)


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class GraphSymbol:
    id: str
    scope: Scope
    kind: SymbolKind
    file_path: str
    name: str
    qualified_name: str
    signature: str
    body: str
    hash_value: str
    ai_documentation: str
    doc_status: DocStatus
    embedding: list[float]
    visibility: str = "public"
    version: int = 1
    created_at: str = ""
    updated_at: str = ""


@dataclass
class GraphEdge:
    id: str
    scope: Scope
    rel_type: str
    source_id: str
    target_id: str
    confidence: CallConfidence = CallConfidence.EXACT
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class IngestResult:
    file_id: str
    symbols_indexed: int
    symbols_changed: int
    symbols_documented: int
    edges_written: int
    changed_symbol_ids: list[str]


class Store(Protocol):
    def get_symbol(self, symbol_id: str, scope: Scope) -> GraphSymbol: ...
    def put_symbol(self, symbol: GraphSymbol) -> None: ...
    def list_symbols(self, scope: Scope) -> list[GraphSymbol]: ...
    def get_symbol_by_qualified_name(self, scope: Scope, qualified_name: str) -> GraphSymbol | None: ...
    def delete_file_edges(self, scope: Scope, file_path: str) -> None: ...
    def put_edge(self, edge: GraphEdge) -> None: ...
    def list_edges(self, scope: Scope) -> list[GraphEdge]: ...
    def begin_idempotency(self, scope: Scope, key: str, resource: str) -> str | None: ...
    def complete_idempotency(self, scope: Scope, key: str, resource: str, resource_id: str) -> None: ...
    def append_event(self, event: dict[str, Any]) -> None: ...
    def outbox(self) -> list[dict[str, Any]]: ...


class HeuristicDocGenerator:
    """Local deterministic documentation — no cloud model calls."""

    def generate(self, symbol: GraphSymbol, neighbors: list[str]) -> str:
        neighbor_text = ", ".join(neighbors[:8]) if neighbors else "none"
        return (
            f"{symbol.kind.value.title()} `{symbol.qualified_name}`\n"
            f"Signature: {symbol.signature or symbol.name}\n"
            f"File: {symbol.file_path}\n"
            f"Related symbols: {neighbor_text}\n"
            f"Summary: Owns behavior for `{symbol.name}` in project graph context."
        )


def embed_text(text: str, dims: int = 16) -> list[float]:
    """Cheap local embedding for tests and offline semantic ranking."""
    vec = [0.0] * dims
    tokens = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", text.lower())
    if not tokens:
        return vec
    for token in tokens:
        idx = int(digest(token)[:8], 16) % dims
        vec[idx] += 1.0
    norm = sum(v * v for v in vec) ** 0.5 or 1.0
    return [round(v / norm, 6) for v in vec]


def cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=False))


@dataclass
class ParsedSymbol:
    kind: SymbolKind
    name: str
    qualified_name: str
    signature: str
    body: str
    calls: list[str]
    imports: list[str]
    bases: list[str]
    visibility: str = "public"


def parse_python_source(file_path: str, source: str) -> list[ParsedSymbol]:
    tree = ast.parse(source)
    module = file_path.replace("\\", "/").removesuffix(".py").replace("/", ".")
    results: list[ParsedSymbol] = []

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            else:
                root = node.module or ""
                names = [f"{root}.{alias.name}" if root else alias.name for alias in node.names]
            text = ast.get_source_segment(source, node) or ""
            results.append(
                ParsedSymbol(
                    kind=SymbolKind.IMPORT,
                    name=names[0] if names else "import",
                    qualified_name=f"{module}::__import__::{digest(text)[:8]}",
                    signature=text.strip(),
                    body=text,
                    calls=[],
                    imports=names,
                    bases=[],
                )
            )
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            results.append(_function_symbol(module, source, node, SymbolKind.FUNCTION))
        elif isinstance(node, ast.ClassDef):
            class_q = f"{module}.{node.name}"
            class_body = ast.get_source_segment(source, node) or node.name
            bases = [_expr_name(base) for base in node.bases]
            results.append(
                ParsedSymbol(
                    kind=SymbolKind.CLASS,
                    name=node.name,
                    qualified_name=class_q,
                    signature=f"class {node.name}",
                    body=class_body,
                    calls=[],
                    imports=[],
                    bases=[b for b in bases if b],
                    visibility="private" if node.name.startswith("_") else "public",
                )
            )
            for child in node.body:
                if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                    method = _function_symbol(class_q, source, child, SymbolKind.METHOD)
                    results.append(method)
    return results


def _function_symbol(
    owner: str,
    source: str,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    kind: SymbolKind,
) -> ParsedSymbol:
    body = ast.get_source_segment(source, node) or node.name
    args = [arg.arg for arg in node.args.args]
    signature = f"{node.name}({', '.join(args)})"
    calls = sorted({_call_name(n) for n in ast.walk(node) if isinstance(n, ast.Call)})
    calls = [c for c in calls if c]
    return ParsedSymbol(
        kind=kind,
        name=node.name,
        qualified_name=f"{owner}.{node.name}",
        signature=signature,
        body=body,
        calls=calls,
        imports=[],
        bases=[],
        visibility="private" if node.name.startswith("_") else "public",
    )


def _expr_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _expr_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def _call_name(node: ast.Call) -> str:
    return _expr_name(node.func)


def extract_identifier_refs(source: str) -> set[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", source))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    return names


def _defined_names(source: str) -> set[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
    return names


def _builtin_names() -> set[str]:
    return {
        "True",
        "False",
        "None",
        "self",
        "cls",
        "print",
        "len",
        "str",
        "int",
        "list",
        "dict",
        "set",
        "tuple",
        "range",
        "isinstance",
        "getattr",
        "setattr",
    }


class CodeGraphService:
    def __init__(self, store: Store, docs: HeuristicDocGenerator | None = None) -> None:
        self.store = store
        self.docs = docs or HeuristicDocGenerator()

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
        language = str(payload.get("language") or "python").strip().lower()
        if not file_path or not source:
            raise ValidationError("file_path and source are required")
        if language != "python":
            raise ValidationError("Phase 7 slice supports python language only")

        stamp = now_iso()
        file_hash = digest(normalize_source(source))
        file_id = f"file:{scope.project_id}:{file_path}"
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
            embedding=embed_text(file_path),
            created_at=stamp,
            updated_at=stamp,
        )
        previous_file = self._maybe_get(file_id, scope)
        if previous_file is not None:
            file_symbol.version = previous_file.version + 1
            file_symbol.created_at = previous_file.created_at
        self.store.put_symbol(file_symbol)

        parsed = parse_python_source(file_path, source)
        changed_ids: list[str] = []
        documented = 0
        symbol_ids: list[str] = []

        for item in parsed:
            symbol_id = f"sym:{scope.project_id}:{item.qualified_name}"
            symbol_ids.append(symbol_id)
            hash_value = digest(normalize_source(item.body))
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
                embedding=embed_text(f"{item.qualified_name}\n{doc}"),
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

        by_name = {s.qualified_name: s.id for s in self.store.list_symbols(scope) if s.kind != SymbolKind.FILE}
        short_names = {}
        for s in self.store.list_symbols(scope):
            short_names.setdefault(s.name, []).append(s.id)

        for item in parsed:
            source_id = f"sym:{scope.project_id}:{item.qualified_name}"
            for base in item.bases:
                target = by_name.get(base) or (short_names.get(base, [None])[0])
                if target:
                    edges_written += self._put_edge(
                        scope, "INHERITS_FROM", source_id, target, file_path=file_path, confidence=CallConfidence.EXACT
                    )
            for imp in item.imports:
                target = by_name.get(imp)
                confidence = CallConfidence.EXACT if target else CallConfidence.UNRESOLVED
                target_id = target or f"ext:{imp}"
                if target is None:
                    # External import placeholder node.
                    if self._maybe_get(target_id, scope) is None:
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
                                embedding=embed_text(imp),
                                created_at=stamp,
                                updated_at=stamp,
                            )
                        )
                edges_written += self._put_edge(
                    scope, "IMPORTS", source_id, target_id, file_path=file_path, confidence=confidence
                )
            for call in item.calls:
                matches = short_names.get(call, [])
                if len(matches) == 1:
                    edges_written += self._put_edge(
                        scope,
                        "CALLS",
                        source_id,
                        matches[0],
                        file_path=file_path,
                        confidence=CallConfidence.EXACT,
                    )
                elif len(matches) > 1:
                    for match in matches:
                        edges_written += self._put_edge(
                            scope,
                            "CALLS",
                            source_id,
                            match,
                            file_path=file_path,
                            confidence=CallConfidence.AMBIGUOUS,
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
            if symbol.kind == SymbolKind.FILE:
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
                }
                for edge in edges
            ],
        }

    def semantic_search(self, scope: Scope, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if not query.strip():
            raise ValidationError("query is required")
        vector = embed_text(query)
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
        known = {symbol.name for symbol in self.store.list_symbols(scope)}
        known.update(_builtin_names())
        known.update(_defined_names(source))
        refs = extract_identifier_refs(source)
        unknown = sorted(ref for ref in refs if ref not in known and not ref.startswith("__"))
        return {
            "accepted": len(unknown) == 0,
            "unknown_symbols": unknown,
            "known_symbol_count": len(known),
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
    ) -> int:
        edge = GraphEdge(
            id=f"edge:{digest(f'{rel_type}|{source_id}|{target_id}')[:16]}",
            scope=scope,
            rel_type=rel_type,
            source_id=source_id,
            target_id=target_id,
            confidence=confidence,
            metadata={"file_path": file_path},
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
