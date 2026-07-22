"""Tests for operator CLI defaults (env / connect.yaml / dogfood)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from agentcore_cli.cli_defaults import load_dotenv_files, resolve_operator_scope
from agentcore_cli.parser import build_parser


def test_resolve_operator_scope_defaults(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AGENTCORE_TENANT_ID", raising=False)
    monkeypatch.delenv("AGENTCORE_WORKSPACE_ID", raising=False)
    monkeypatch.delenv("AGENTCORE_PROJECT_ID", raising=False)
    monkeypatch.setattr("agentcore_cli.cli_defaults.peek_connect_scope", lambda: {})
    monkeypatch.setattr("agentcore_cli.cli_defaults.peek_identity_scope", lambda: {})
    monkeypatch.setattr("agentcore_cli.cli_defaults.load_dotenv_files", lambda **_: [])
    tenant, workspace, project = resolve_operator_scope(cwd=tmp_path)
    assert tenant == "agentcore"
    assert workspace == "dev"
    assert project == tmp_path.name


def test_resolve_operator_scope_env_wins(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("agentcore_cli.cli_defaults.peek_connect_scope", lambda: {})
    monkeypatch.setattr("agentcore_cli.cli_defaults.load_dotenv_files", lambda **_: [])
    monkeypatch.setenv("AGENTCORE_TENANT_ID", "acme")
    monkeypatch.setenv("AGENTCORE_WORKSPACE_ID", "eng")
    monkeypatch.setenv("AGENTCORE_PROJECT_ID", "payments")
    tenant, workspace, project = resolve_operator_scope(cwd=tmp_path)
    assert (tenant, workspace, project) == ("acme", "eng", "payments")


def test_resolve_operator_scope_cli_wins(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("agentcore_cli.cli_defaults.peek_connect_scope", lambda: {"tenant": "from-yaml"})
    monkeypatch.setattr("agentcore_cli.cli_defaults.load_dotenv_files", lambda **_: [])
    monkeypatch.setenv("AGENTCORE_TENANT_ID", "from-env")
    tenant, workspace, project = resolve_operator_scope(
        tenant="from-cli",
        workspace="w",
        project="p",
        cwd=tmp_path,
    )
    assert tenant == "from-cli"
    assert workspace == "w"
    assert project == "p"


def test_load_dotenv_files_fills_missing(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("AGENTCORE_TENANT_ID", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("AGENTCORE_TENANT_ID=from-dotenv\n", encoding="utf-8")
    monkeypatch.setattr("agentcore_cli.util.repo_root", lambda: tmp_path)
    loaded = load_dotenv_files(root=tmp_path)
    assert env_file in loaded
    assert os_environ_tenant() == "from-dotenv"


def test_load_dotenv_files_includes_code_graph_runtime_config(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("AGENTCORE_LITELLM_DEFAULT_MODEL", raising=False)
    env_file = tmp_path / "backend" / "services" / "code-graph-service" / "config" / ".env"
    env_file.parent.mkdir(parents=True)
    env_file.write_text("AGENTCORE_LITELLM_DEFAULT_MODEL=local/test-model\n", encoding="utf-8")
    env_file.chmod(0o600)

    loaded = load_dotenv_files(root=tmp_path, include_code_graph=True)

    assert env_file in loaded
    assert os.environ["AGENTCORE_LITELLM_DEFAULT_MODEL"] == "local/test-model"


def test_graph_cli_builds_gateway_from_code_graph_runtime_config(monkeypatch, tmp_path: Path):
    import code_graph_service.bootstrap as bootstrap
    from agentcore_cli.commands.graph import _graph_service
    from code_graph_service.testing import InMemoryStore

    keys = (
        "AGENTCORE_GRAPH_CLI_BACKEND",
        "AGENTCORE_CODE_GRAPH_STORE",
        "AGENTCORE_CODE_GRAPH_DATABASE_URL",
        "AGENTCORE_NEO4J_PASSWORD",
        "AGENTCORE_LITELLM_DEFAULT_MODEL",
        "AGENTCORE_LITELLM_MODEL_DOCS",
        "AGENTCORE_LITELLM_RPM",
        "AGENTCORE_EMBEDDING_PROVIDER",
    )
    for key in keys:
        monkeypatch.delenv(key, raising=False)
    env_file = tmp_path / "backend" / "services" / "code-graph-service" / "config" / ".env"
    env_file.parent.mkdir(parents=True)
    env_file.write_text(
        "AGENTCORE_GRAPH_CLI_BACKEND=neo4j\n"
        "AGENTCORE_CODE_GRAPH_STORE=neo4j\n"
        "AGENTCORE_NEO4J_PASSWORD=local-test-secret\n"
        "AGENTCORE_LITELLM_DEFAULT_MODEL=local/live-model\n"
        "AGENTCORE_LITELLM_MODEL_DOCS=local/live-model\n"
        "AGENTCORE_LITELLM_RPM=7\n"
        "AGENTCORE_EMBEDDING_PROVIDER=stub\n",
        encoding="utf-8",
    )
    env_file.chmod(0o600)
    monkeypatch.setattr("agentcore_cli.util.repo_root", lambda: tmp_path)
    monkeypatch.setattr(bootstrap, "build_store", lambda _settings: InMemoryStore())
    monkeypatch.setattr(bootstrap, "build_embedding_index", lambda _settings: None)

    service = _graph_service()

    assert service.llm.settings.default_model == "local/live-model"
    assert service.llm.settings.rpm == 7
    assert service.llm_config()["route_docs"]["primary_model"] == "local/live-model"


def test_code_graph_runtime_config_requires_private_permissions(tmp_path: Path):
    env_file = tmp_path / "backend" / "services" / "code-graph-service" / "config" / ".env"
    env_file.parent.mkdir(parents=True)
    env_file.write_text("AGENTCORE_LITELLM_RPM=7\n", encoding="utf-8")
    env_file.chmod(0o644)

    with pytest.raises(PermissionError, match="mode 0600"):
        load_dotenv_files(root=tmp_path, include_code_graph=True)


def test_sync_cloud_llm_requires_explicit_per_run_consent():
    from agentcore_cli.commands.graph import _require_cloud_llm_consent

    class Service:
        def __init__(self, model: str) -> None:
            self.model = model

        def llm_config(self):
            return {
                "enabled": True,
                "api_base": "http://127.0.0.1:32400",
                "docs_enabled": True,
                "embeddings_enabled": False,
                "route_docs": {"primary_model": self.model, "fallback_models": []},
                "route_embed": {"primary_model": "", "fallback_models": []},
            }

    # Non-TTY without flag → fail closed
    with pytest.raises(SystemExit, match="--allow-cloud-llm|interactive"):
        _require_cloud_llm_consent(
            Service("openai/gpt-oss"),
            allowed=False,
            tenant="acme",
            workspace="eng",
            project="agentcore",
            paths=["/opt/MyApp"],
            stdin_isatty=False,
        )
    # Flag skips prompt
    _require_cloud_llm_consent(Service("openai/gpt-oss"), allowed=True, stdin_isatty=False)
    # Local private route needs no consent
    _require_cloud_llm_consent(Service("ollama/local-model"), allowed=False, stdin_isatty=False)

    class EmbedService:
        def llm_config(self):
            return {
                "enabled": True,
                "api_base": "http://127.0.0.1:32400",
                "docs_enabled": False,
                "embeddings_enabled": True,
                "route_docs": {"primary_model": "", "fallback_models": []},
                "route_embed": {
                    "primary_model": "ollama/local-model",
                    "fallback_models": ["openai/cloud-fallback"],
                },
            }

    with pytest.raises(SystemExit, match="--allow-cloud-llm|interactive"):
        _require_cloud_llm_consent(EmbedService(), allowed=False, stdin_isatty=False)

    # Interactive: both yes steps required
    answers = iter(["yes", "yes"])
    _require_cloud_llm_consent(
        Service("openai/gpt-oss"),
        allowed=False,
        tenant="acme",
        workspace="eng",
        project="agentcore",
        paths=["/opt/MyApp"],
        input_fn=lambda _p: next(answers),
        stdin_isatty=True,
    )
    # Decline on first yes
    with pytest.raises(SystemExit, match="cloud LLM consent declined"):
        _require_cloud_llm_consent(
            Service("openai/gpt-oss"),
            allowed=False,
            tenant="acme",
            workspace="eng",
            project="agentcore",
            paths=["/opt/MyApp"],
            input_fn=lambda _p: "n",
            stdin_isatty=True,
        )
    # Decline on second yes (ID confirm)
    answers2 = iter(["y", "n"])
    with pytest.raises(SystemExit, match="scope ID confirmation declined"):
        _require_cloud_llm_consent(
            Service("openai/gpt-oss"),
            allowed=False,
            tenant="acme",
            workspace="eng",
            project="agentcore",
            paths=["/opt/MyApp"],
            input_fn=lambda _p: next(answers2),
            stdin_isatty=True,
        )


def test_cloud_llm_consent_prompt_shows_scope_and_path(capsys):
    from agentcore_cli.commands.graph import _require_cloud_llm_consent

    class Service:
        def llm_config(self):
            return {
                "enabled": True,
                "api_base": "https://openrouter.ai/api/v1",
                "docs_enabled": True,
                "embeddings_enabled": False,
                "route_docs": {
                    "primary_model": "openai/gpt-oss-20b:free",
                    "fallback_models": [],
                },
                "route_embed": {"primary_model": "", "fallback_models": []},
            }

    answers = iter(["y", "y"])
    _require_cloud_llm_consent(
        Service(),
        allowed=False,
        tenant="acme",
        workspace="eng",
        project="agentcore",
        paths=["/opt/AgentCore"],
        input_fn=lambda _p: next(answers),
        stdin_isatty=True,
    )
    out = capsys.readouterr().out
    assert "acme" in out
    assert "eng" in out
    assert "/opt/AgentCore" in out
    assert "openrouter.ai" in out
    assert "acme/eng/agentcore" in out
    assert "Confirm scope IDs" in out
    assert out.count("/opt/AgentCore") >= 2  # shown in step 1 and step 2


def test_graph_query_commands_apply_cloud_consent_guard(monkeypatch):
    import agentcore_cli.commands.graph as graph

    class Scope:
        tenant_id = "t"
        workspace_id = "w"
        project_id = "p"

    class Service:
        def explore(self, *_args, **_kwargs):
            return {"sections": []}

        def hybrid_search(self, *_args, **_kwargs):
            return {"hits": []}

    service = Service()
    guarded: list[dict] = []
    monkeypatch.setattr(graph, "_graph_service", lambda: service)
    monkeypatch.setattr(graph, "_graph_scope", lambda _args: Scope())

    def capture(_svc, *, allowed, **kwargs):
        guarded.append({"allowed": allowed, **kwargs})

    monkeypatch.setattr(graph, "_require_cloud_llm_consent", capture)
    args = SimpleNamespace(query="private query", top_k=5, allow_cloud_llm=False)

    assert graph.cmd_graph_explore(args) == 0
    assert graph.cmd_graph_hybrid(args) == 0
    assert [g["allowed"] for g in guarded] == [False, False]
    assert all(g.get("tenant") == "t" and g.get("workspace") == "w" for g in guarded)


def os_environ_tenant() -> str:
    import os

    return os.environ.get("AGENTCORE_TENANT_ID", "")


def test_parser_sync_defaults_path_and_optional_scope():
    parser = build_parser()
    args = parser.parse_args(["sync"])
    assert args.command == "sync"
    assert args.path is None  # uses pinned software paths from init
    assert args.tenant == ""
    assert args.max_files == 2000
    assert args.allow_cloud_llm is False
    assert parser.parse_args(["sync", "--allow-cloud-llm"]).allow_cloud_llm is True
    assert parser.parse_args(
        ["graph", "explore", "--tenant", "t", "--workspace", "w", "--project", "p", "--query", "q", "--allow-cloud-llm"]
    ).allow_cloud_llm is True
    purge = parser.parse_args(["purge", "--yes"])
    assert purge.yes is True


def test_parser_sync_max_file_bare_word_only():
    parser = build_parser()
    args = parser.parse_args(["sync", "max-file", "50"])
    assert args.max_files == 50
    for bad in ("-max-file", "--max-file", "--max-files"):
        try:
            parser.parse_args(["sync", bad, "50"])
        except SystemExit as exc:
            assert exc.code == 2
        else:
            raise AssertionError(f"{bad} must be rejected for sync")
