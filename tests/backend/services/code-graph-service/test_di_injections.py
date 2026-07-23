"""GAP-002: DI injection extraction and CALLS provenance."""

from __future__ import annotations

from code_graph_service.domain.confidence_policy import clamp_confidence
from code_graph_service.domain.di_injections import extract_injections
from code_graph_service.domain.enums import CallConfidence


def test_extract_fastapi_depends():
    source = '''
from fastapi import Depends

def get_db():
    return None

async def list_items(db=Depends(get_db)):
    return db
'''
    hits = extract_injections(source, language="python")
    assert any(h.provider_name == "get_db" and h.consumer_name == "list_items" for h in hits)
    assert hits[0].framework == "fastapi"


def test_extract_nestjs_constructor_types():
    source = """
@Injectable()
export class OrdersService {
  constructor(private readonly users: UsersService) {}
}
"""
    hits = extract_injections(source, language="typescript")
    assert any(
        h.consumer_name == "OrdersService" and h.provider_name == "UsersService" for h in hits
    )


def test_clamp_cross_language_caps_exact():
    assert (
        clamp_confidence(
            CallConfidence.EXACT,
            source_language="python",
            target_language="rust",
        )
        == CallConfidence.PROBABLE
    )


def test_clamp_same_language_keeps_exact():
    assert (
        clamp_confidence(
            CallConfidence.EXACT,
            source_language="python",
            target_language="python",
        )
        == CallConfidence.EXACT
    )


def test_clamp_di_via_caps_exact():
    assert (
        clamp_confidence(CallConfidence.EXACT, via="di_injection") == CallConfidence.PROBABLE
    )
