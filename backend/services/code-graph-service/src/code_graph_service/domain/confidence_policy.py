"""Per-language confidence clamping for polyglot resolution (GAP-002)."""

from __future__ import annotations

from .enums import CallConfidence

# Cross-language edges never claim EXACT — parsers disagree on identity.
_CROSS_LANGUAGE_CAP = {
    CallConfidence.EXACT: CallConfidence.PROBABLE,
    CallConfidence.PROBABLE: CallConfidence.PROBABLE,
    CallConfidence.AMBIGUOUS: CallConfidence.AMBIGUOUS,
    CallConfidence.UNRESOLVED: CallConfidence.UNRESOLVED,
    CallConfidence.EXTERNAL: CallConfidence.EXTERNAL,
}

# Package-manifest rewrites are probable unless already weaker.
_VIA_PACKAGE_MANIFEST_CAP = {
    CallConfidence.EXACT: CallConfidence.PROBABLE,
    CallConfidence.PROBABLE: CallConfidence.PROBABLE,
    CallConfidence.AMBIGUOUS: CallConfidence.AMBIGUOUS,
    CallConfidence.UNRESOLVED: CallConfidence.UNRESOLVED,
    CallConfidence.EXTERNAL: CallConfidence.EXTERNAL,
}

# DI / framework heuristics stay at probable max.
_VIA_DI_CAP = {
    CallConfidence.EXACT: CallConfidence.PROBABLE,
    CallConfidence.PROBABLE: CallConfidence.PROBABLE,
    CallConfidence.AMBIGUOUS: CallConfidence.AMBIGUOUS,
    CallConfidence.UNRESOLVED: CallConfidence.UNRESOLVED,
    CallConfidence.EXTERNAL: CallConfidence.EXTERNAL,
}


def clamp_confidence(
    confidence: CallConfidence,
    *,
    source_language: str = "",
    target_language: str = "",
    via: str = "",
) -> CallConfidence:
    """Apply language / resolution-path caps without inventing stronger confidence."""
    result = confidence
    src = (source_language or "").strip().lower()
    tgt = (target_language or "").strip().lower()
    if src and tgt and src != tgt:
        result = _CROSS_LANGUAGE_CAP.get(result, result)
    via_key = (via or "").strip().lower()
    if via_key in {"package_manifest", "package_alias", "tsconfig_paths", "cargo", "go_replace"}:
        result = _VIA_PACKAGE_MANIFEST_CAP.get(result, result)
    if via_key in {"di_injection", "framework_route", "dynamic_dispatch"}:
        result = _VIA_DI_CAP.get(result, result)
    return result
