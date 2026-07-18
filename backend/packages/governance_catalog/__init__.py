"""AgentCore governance catalogs for Phase 9/10 (risks, KPIs, gap register)."""

from .loader import (
    GovernanceCatalogError,
    load_gap_register,
    load_impact_kpis,
    load_risk_catalog,
    validate_gap_register,
    validate_impact_kpis,
    validate_risk_catalog,
)

__all__ = [
    "GovernanceCatalogError",
    "load_gap_register",
    "load_impact_kpis",
    "load_risk_catalog",
    "validate_gap_register",
    "validate_impact_kpis",
    "validate_risk_catalog",
]
