from code_graph_service.api import app
from code_graph_service.core import CodeGraphService, Scope, digest, normalize_source
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
