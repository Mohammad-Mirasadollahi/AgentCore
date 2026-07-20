"""Domain enums for the Code-Knowledge Graph."""

from __future__ import annotations

from enum import StrEnum


class SymbolKind(StrEnum):
    FILE = "file"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    IMPORT = "import"
    DOCUMENTATION = "documentation"


class CallConfidence(StrEnum):
    EXACT = "exact"
    PROBABLE = "probable"
    AMBIGUOUS = "ambiguous"
    UNRESOLVED = "unresolved"


class DocStatus(StrEnum):
    MISSING = "missing"
    GENERATED = "generated"
    UNCHANGED = "unchanged"
