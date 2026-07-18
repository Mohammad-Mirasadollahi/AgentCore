"""Shared public API contract helpers (pagination, errors, examples)."""

from .api import (
    ERROR_CATEGORIES,
    ContractError,
    make_error_envelope,
    make_page,
    validate_error_envelope,
    validate_page,
)

__all__ = [
    "ERROR_CATEGORIES",
    "ContractError",
    "make_error_envelope",
    "make_page",
    "validate_error_envelope",
    "validate_page",
]
