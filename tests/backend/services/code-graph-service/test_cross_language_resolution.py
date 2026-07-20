"""Cross-language CALLS / IMPORTS resolution and unresolved relink."""

from __future__ import annotations

from code_graph_service.core import CodeGraphService, Scope
from code_graph_service.testing import InMemoryStore

SCOPE = Scope("t", "w", "xlang")

RUST_HELPER = """
pub fn check_password(password: &str) -> bool {
    password.len() > 8
}
"""

PYTHON_CALLER = """
def login(user, password):
    return check_password(password)
"""

HELPERS_PY = """
def helper(value):
    return value
"""

JS_IMPORT_HELPER = """
import { helper as helpFn } from "./helpers";

function run(value) {
  return helpFn(value);
}
"""


def test_python_calls_unique_rust_symbol_cross_language():
    store = InMemoryStore()
    service = CodeGraphService(store)
    service.ingest_file(
        SCOPE,
        "agent",
        "c-rs",
        "idem-rs",
        {"file_path": "src/auth.rs", "source": RUST_HELPER, "language": "rust"},
    )
    service.ingest_file(
        SCOPE,
        "agent",
        "c-py",
        "idem-py",
        {"file_path": "src/login.py", "source": PYTHON_CALLER, "language": "python"},
    )
    login_id = f"sym:{SCOPE.project_id}:src.login.login"
    rust_id = f"sym:{SCOPE.project_id}:src.auth.check_password"
    neighbors = service.structural_query(SCOPE, login_id, "CALLS")
    assert any(
        edge["target_id"] == rust_id
        and edge["confidence"] in {"probable", "exact"}
        and edge["metadata"].get("cross_language") is True
        for edge in neighbors["edges"]
    )


def test_unresolved_call_relinks_after_target_language_ingest():
    store = InMemoryStore()
    service = CodeGraphService(store)
    service.ingest_file(
        SCOPE,
        "agent",
        "c-py",
        "idem-py-first",
        {"file_path": "src/login.py", "source": PYTHON_CALLER, "language": "python"},
    )
    login_id = f"sym:{SCOPE.project_id}:src.login.login"
    before = service.structural_query(SCOPE, login_id, "CALLS")
    assert any(str(edge["target_id"]).startswith("unresolved:") for edge in before["edges"])

    service.ingest_file(
        SCOPE,
        "agent",
        "c-rs",
        "idem-rs-second",
        {"file_path": "src/auth.rs", "source": RUST_HELPER, "language": "rust"},
    )
    rust_id = f"sym:{SCOPE.project_id}:src.auth.check_password"
    after = service.structural_query(SCOPE, login_id, "CALLS")
    assert any(
        edge["target_id"] == rust_id and edge["metadata"].get("relinked") is True
        for edge in after["edges"]
    )
    assert not any(str(edge["target_id"]).startswith("unresolved:") for edge in after["edges"])


def test_js_import_resolves_python_helper_file_stem():
    store = InMemoryStore()
    service = CodeGraphService(store)
    service.ingest_file(
        SCOPE,
        "agent",
        "c-py",
        "idem-helpers",
        {"file_path": "src/helpers.py", "source": HELPERS_PY, "language": "python"},
    )
    service.ingest_file(
        SCOPE,
        "agent",
        "c-js",
        "idem-js",
        {"file_path": "src/consumer.js", "source": JS_IMPORT_HELPER, "language": "javascript"},
    )
    file_id = f"file:{SCOPE.project_id}:src/consumer.js"
    helpers_file = f"file:{SCOPE.project_id}:src/helpers.py"
    imports = service.structural_query(SCOPE, file_id, "IMPORTS")
    assert any(
        edge["target_id"] == helpers_file
        and edge["metadata"].get("cross_language") is True
        and edge["metadata"].get("resolved_via") == "file_stem"
        for edge in imports["edges"]
    )
