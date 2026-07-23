"""Check helpers for DI composition Phase A+B gate."""

from __future__ import annotations

from pathlib import Path

from .catalog import (
    BANNED_APPLICATION_PATTERNS,
    CODE_GRAPH_API,
    CODE_GRAPH_APPLICATION,
    CODE_GRAPH_BOOTSTRAP,
    CODE_GRAPH_DOMAIN,
    MCP_STORE_FACTORY,
    REQUIRED_DOCS,
    ROOT,
    SERVICES,
    THIN_SERVICES,
)
from .gate import CheckResult


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def verify_docs_exist() -> list[CheckResult]:
    results: list[CheckResult] = []
    for index, path in enumerate(REQUIRED_DOCS, start=1):
        ok = path.is_file()
        results.append(
            CheckResult(
                f"di-doc-{index}",
                "documentation",
                path.name,
                "passed" if ok else "failed",
                "present" if ok else "missing",
                [str(path.relative_to(ROOT))],
                str(path.relative_to(ROOT)),
            )
        )
    return results


def verify_code_graph_container() -> list[CheckResult]:
    text = _read(CODE_GRAPH_BOOTSTRAP)
    has_container = "class ServiceContainer" in text and "def build_container" in text
    has_wrapper = "def build_service" in text and "build_container" in text
    return [
        CheckResult(
            "di-cg-build-container",
            "composition",
            "code-graph-bootstrap",
            "passed" if has_container else "failed",
            "ServiceContainer+build_container" if has_container else "missing",
            ["build_container"],
            "docs/08-software-engineering-architecture/47-backend-di-composition-low-level-design.md",
        ),
        CheckResult(
            "di-cg-build-service-wrapper",
            "composition",
            "code-graph-bootstrap",
            "passed" if has_wrapper else "failed",
            "build_service wraps build_container" if has_wrapper else "missing wrapper",
            ["build_service"],
            "docs/08-software-engineering-architecture/47-backend-di-composition-low-level-design.md",
        ),
    ]


def verify_code_graph_app_state() -> list[CheckResult]:
    text = _read(CODE_GRAPH_API)
    has_build_app = "def build_app" in text
    has_state = "api.state.container" in text or "app.state.container" in text
    has_build_service_call = "build_service(" in text
    return [
        CheckResult(
            "di-cg-build-app",
            "composition",
            "code-graph-api",
            "passed" if has_build_app and has_state else "failed",
            "build_app+app.state.container" if has_build_app and has_state else "missing",
            ["build_app", "state.container"],
            "docs/08-software-engineering-architecture/47-backend-di-composition-low-level-design.md",
        ),
        CheckResult(
            "di-cg-no-handler-build-service",
            "composition",
            "code-graph-api",
            "passed" if not has_build_service_call else "failed",
            "no build_service in api" if not has_build_service_call else "build_service still referenced",
            [],
            "docs/08-software-engineering-architecture/47-backend-di-composition-low-level-design.md",
        ),
    ]


def verify_application_banned_imports() -> list[CheckResult]:
    offenders: list[str] = []
    for root in (CODE_GRAPH_APPLICATION, CODE_GRAPH_DOMAIN):
        if not root.is_dir():
            continue
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for pattern in BANNED_APPLICATION_PATTERNS:
                if pattern in text:
                    offenders.append(f"{path.relative_to(ROOT)}:{pattern}")
    return [
        CheckResult(
            "di-cg-banned-imports",
            "import_boundary",
            "code-graph-application-domain",
            "passed" if not offenders else "failed",
            "clean" if not offenders else f"offenders={len(offenders)}",
            offenders[:20],
            "docs/08-software-engineering-architecture/47-backend-di-composition-low-level-design.md",
        )
    ]


def verify_mcp_composition_root() -> list[CheckResult]:
    text = _read(MCP_STORE_FACTORY)
    has_mcp_container = "class McpServiceContainer" in text and "def build_container" in text
    uses_cg_container = "build_container" in text and "code_graph_service.bootstrap" in text
    return [
        CheckResult(
            "di-mcp-build-container",
            "composition",
            "mcp-store-factory",
            "passed" if has_mcp_container else "failed",
            "McpServiceContainer+build_container" if has_mcp_container else "missing",
            ["build_container"],
            "docs/08-software-engineering-architecture/47-backend-di-composition-low-level-design.md",
        ),
        CheckResult(
            "di-mcp-uses-code-graph-container",
            "composition",
            "mcp-store-factory",
            "passed" if uses_cg_container else "failed",
            "neo4j path uses code-graph build_container" if uses_cg_container else "missing",
            [],
            "docs/08-software-engineering-architecture/47-backend-di-composition-low-level-design.md",
        ),
    ]


def verify_thin_services() -> list[CheckResult]:
    missing: list[str] = []
    for service_dir, pkg in THIN_SERVICES:
        boot = SERVICES / service_dir / "src" / pkg / "bootstrap.py"
        api = SERVICES / service_dir / "src" / pkg / "api.py"
        if not boot.is_file() or not api.is_file():
            missing.append(f"{service_dir}:missing-files")
            continue
        boot_text = _read(boot)
        api_text = _read(api)
        if "class ServiceContainer" not in boot_text or "def build_container" not in boot_text:
            missing.append(f"{service_dir}:bootstrap")
        if "def build_app" not in api_text or "api.state.container" not in api_text:
            missing.append(f"{service_dir}:api")
        if "build_service(" in api_text:
            missing.append(f"{service_dir}:api-build_service")
        if "app = build_app" not in api_text:
            missing.append(f"{service_dir}:app-alias")
    return [
        CheckResult(
            "di-thin-services-phase-b",
            "composition",
            "thin-services",
            "passed" if not missing else "failed",
            f"ok={len(THIN_SERVICES)}" if not missing else f"missing={missing[:12]}",
            missing[:20],
            "docs/08-software-engineering-architecture/47-backend-di-composition-low-level-design.md",
        )
    ]


def run_all_checks() -> list[CheckResult]:
    results: list[CheckResult] = []
    results.extend(verify_docs_exist())
    results.extend(verify_code_graph_container())
    results.extend(verify_code_graph_app_state())
    results.extend(verify_application_banned_imports())
    results.extend(verify_mcp_composition_root())
    results.extend(verify_thin_services())
    return results
