"""Domain models and value objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .enums import CallConfidence, DocStatus, SymbolKind
from .errors import ValidationError


@dataclass(frozen=True)
class Scope:
    tenant_id: str
    workspace_id: str
    project_id: str
    project_group_id: str | None = None

    def __post_init__(self) -> None:
        if not all((self.tenant_id.strip(), self.workspace_id.strip(), self.project_id.strip())):
            raise ValidationError("tenant_id, workspace_id, and project_id are required")


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
    import_aliases: dict[str, str] = field(default_factory=dict)


@dataclass
class ParseResult:
    symbols: list[ParsedSymbol]
    import_aliases: dict[str, str]
    module_prefix: str


@dataclass(frozen=True)
class EmbeddingResult:
    vector: list[float]
    status: str
    model: str
    dims: int
