"""Typed errors for the Code-Knowledge Graph domain."""

from __future__ import annotations


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
