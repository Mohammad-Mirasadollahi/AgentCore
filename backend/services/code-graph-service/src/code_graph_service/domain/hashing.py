"""Hashing and source normalization helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
import re


def digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def normalize_source(source: str, language: str = "python") -> str:
    """Drop comment/whitespace noise so formatting-only edits keep the same hash."""
    normalized_language = (language or "python").strip().lower() or "python"
    if normalized_language in {"javascript", "typescript", "go", "rust"}:
        return _normalize_c_family(source)
    return _normalize_python(source)


def _normalize_python(source: str) -> str:
    lines: list[str] = []
    for raw in source.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if line.strip():
            lines.append(re.sub(r"\s+", " ", line.strip()))
    return "\n".join(lines)


def _normalize_c_family(source: str) -> str:
    without_block = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    lines: list[str] = []
    for raw in without_block.splitlines():
        line = raw.split("//", 1)[0].rstrip()
        if line.strip():
            lines.append(re.sub(r"\s+", " ", line.strip()))
    return "\n".join(lines)


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
