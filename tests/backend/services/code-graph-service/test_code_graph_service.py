from code_graph_service.api import app
from code_graph_service.core import (
    CallConfidence,
    CodeGraphService,
    LocalEmbeddingStub,
    Scope,
    ValidationError,
    assert_language_supported,
    digest,
    language_matrix,
    normalize_source,
    resolve_call_target,
    supported_languages,
)
from code_graph_service.testing import InMemoryStore


SCOPE = Scope("t", "w", "p")

AUTH_SOURCE_V1 = '''\
def check_password(password):
    return len(password) > 8

def login(user, password):
    return check_password(password)
'''

AUTH_SOURCE_V2 = '''\
def check_password(password):
    return len(password) > 8

def login(user, password):
    return check_password(password) and user is not None
'''

HELPER_SOURCE = '''\
def helper(value):
    return value
'''

CONSUMER_SOURCE = '''\
from src.helpers import helper as help_fn

def run(value):
    return help_fn(value)
'''


def test_hash_change_documents_only_changed_symbols():
    store = InMemoryStore()
    service = CodeGraphService(store)

    first = service.ingest_file(
        SCOPE,
        "agent",
        "corr-1",
        "ingest-1",
        {"file_path": "src/auth.py", "source": AUTH_SOURCE_V1, "language": "python"},
    )
    assert first.symbols_indexed >= 3
    assert first.symbols_changed >= 2
    assert first.symbols_documented == first.symbols_changed
    assert store.outbox()[0]["event_type"] == "FileIngested"

    login_id = f"sym:{SCOPE.project_id}:src.auth.login"
    login_before = service.get_symbol(SCOPE, login_id)
    check_id = f"sym:{SCOPE.project_id}:src.auth.check_password"
    check_before = service.get_symbol(SCOPE, check_id)

    second = service.ingest_file(
        SCOPE,
        "agent",
        "corr-2",
        "ingest-2",
        {"file_path": "src/auth.py", "source": AUTH_SOURCE_V2, "language": "python"},
    )
    assert login_id in second.changed_symbol_ids
    assert check_id not in second.changed_symbol_ids
    assert second.symbols_documented == len(second.changed_symbol_ids)

    login_after = service.get_symbol(SCOPE, login_id)
    check_after = service.get_symbol(SCOPE, check_id)
    assert login_after.hash_value != login_before.hash_value
    assert check_after.hash_value == check_before.hash_value
    assert login_after.doc_status.value == "generated"
    assert "login" in login_after.ai_documentation

    documented = service.structural_query(SCOPE, check_id, "DOCUMENTED_BY")
    assert any(edge["rel_type"] == "DOCUMENTED_BY" for edge in documented["edges"])


def test_structural_and_semantic_queries():
    store = InMemoryStore()
    service = CodeGraphService(store)
    service.ingest_file(
        SCOPE,
        "agent",
        "corr",
        "ingest-struct",
        {"file_path": "src/auth.py", "source": AUTH_SOURCE_V1, "language": "python"},
    )
    login_id = f"sym:{SCOPE.project_id}:src.auth.login"
    neighbors = service.structural_query(SCOPE, login_id, "CALLS")
    assert neighbors["symbol"]["qualified_name"] == "src.auth.login"
    assert any(edge["rel_type"] == "CALLS" for edge in neighbors["edges"])
    assert any(edge["confidence"] == "exact" for edge in neighbors["edges"])

    hits = service.semantic_search(SCOPE, "login password authentication", top_k=3)
    assert hits
    assert any("login" in hit["symbol"]["qualified_name"] for hit in hits)


def test_generation_context_avoids_full_repo_and_validates_refs():
    store = InMemoryStore()
    service = CodeGraphService(store)
    service.ingest_file(
        SCOPE,
        "agent",
        "corr",
        "ingest-ctx",
        {"file_path": "src/auth.py", "source": AUTH_SOURCE_V1, "language": "python"},
    )
    login_id = f"sym:{SCOPE.project_id}:src.auth.login"
    context = service.build_generation_context(SCOPE, login_id)
    assert context["uses_full_repository"] is False
    assert "graph context" in context["prompt_context"].lower()
    assert context["symbol_count"] >= 1

    ok = service.validate_generated_code(
        SCOPE,
        "def wrap(user, password):\n    return login(user, password)\n",
    )
    assert ok["accepted"] is True
    assert "login" in ok["checked_call_refs"]

    bad = service.validate_generated_code(
        SCOPE,
        "def wrap(user):\n    return totally_unknown_helper(user)\n",
    )
    assert bad["accepted"] is False
    assert "totally_unknown_helper" in bad["unknown_symbols"]


def test_normalization_and_api_routes():
    left = normalize_source("def login():\n    return True  # note\n")
    right = normalize_source("def login():\n\n    return    True\n")
    assert left == right
    assert digest(left) == digest(right)

    routes = {route.path for route in app(CodeGraphService(InMemoryStore())).routes}
    assert "/api/v1/projects/{project_id}/graph/ingest-file" in routes
    assert "/api/v1/projects/{project_id}/graph/search:semantic" in routes
    assert "/api/v1/projects/{project_id}/graph/generation-context" in routes
    assert "/api/v1/projects/{project_id}/graph/generated-code:validate" in routes
    assert "/api/v1/projects/{project_id}/graph/symbols/{symbol_id}/neighbors" in routes


def test_language_matrix_hook_and_reject_planned():
    matrix = language_matrix()
    assert matrix["python"]["status"] == "supported"
    assert matrix["python"]["parser"] == "stdlib_ast"
    assert "python" in supported_languages()
    assert assert_language_supported("Python") == "python"
    try:
        assert_language_supported("typescript")
        raise AssertionError("planned language should raise")
    except ValidationError as exc:
        assert "planned" in exc.message


def test_import_alias_probable_calls_and_file_imports():
    store = InMemoryStore()
    service = CodeGraphService(store)
    service.ingest_file(
        SCOPE,
        "agent",
        "corr-h",
        "ingest-helper",
        {"file_path": "src/helpers.py", "source": HELPER_SOURCE, "language": "python"},
    )
    service.ingest_file(
        SCOPE,
        "agent",
        "corr-c",
        "ingest-consumer",
        {"file_path": "src/consumer.py", "source": CONSUMER_SOURCE, "language": "python"},
    )
    run_id = f"sym:{SCOPE.project_id}:src.consumer.run"
    neighbors = service.structural_query(SCOPE, run_id, "CALLS")
    helper_id = f"sym:{SCOPE.project_id}:src.helpers.helper"
    assert any(
        edge["target_id"] == helper_id and edge["confidence"] in {"probable", "exact"}
        for edge in neighbors["edges"]
    )

    file_id = f"file:{SCOPE.project_id}:src/consumer.py"
    imports = service.structural_query(SCOPE, file_id, "IMPORTS")
    assert any(edge["rel_type"] == "IMPORTS" for edge in imports["edges"])


def test_embedding_stub_ready_and_resolve_ambiguous():
    stub = LocalEmbeddingStub(dims=8)
    ready = stub.embed("login password")
    assert ready.status == "ready"
    assert ready.dims == 8
    assert len(ready.vector) == 8
    assert stub.embed("").status == "empty"

    by_qualified = {"mod.a": "id-a", "mod.b": "id-b", "other.a": "id-other"}
    short_names = {"a": ["id-a", "id-other"], "b": ["id-b"]}
    targets, confidence = resolve_call_target(
        "a",
        by_qualified=by_qualified,
        short_names=short_names,
        import_aliases={},
        module_prefix="mod",
    )
    assert confidence == CallConfidence.EXACT
    assert targets == ["id-a"]

    targets, confidence = resolve_call_target(
        "a",
        by_qualified=by_qualified,
        short_names=short_names,
        import_aliases={},
        module_prefix="unrelated",
    )
    assert confidence == CallConfidence.AMBIGUOUS
    assert set(targets) == {"id-a", "id-other"}
