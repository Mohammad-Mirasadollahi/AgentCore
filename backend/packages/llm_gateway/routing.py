"""ModelRoutingProfile resolution for LiteLLM task/risk → model aliases."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any


@dataclass(frozen=True)
class RouteDecision:
    """Resolved LiteLLM route for one task class."""

    profile_id: str
    task_class: str
    risk_level: str
    primary_model: str
    fallback_models: tuple[str, ...]
    max_tokens: int | None
    json_mode: bool
    allow_stub: bool

    def models_in_order(self) -> tuple[str, ...]:
        models: list[str] = []
        if self.primary_model.strip():
            models.append(self.primary_model.strip())
        for item in self.fallback_models:
            alias = item.strip()
            if alias and alias not in models:
                models.append(alias)
        return tuple(models)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "task_class": self.task_class,
            "risk_level": self.risk_level,
            "primary_model": self.primary_model,
            "fallback_models": list(self.fallback_models),
            "max_tokens": self.max_tokens,
            "json_mode": self.json_mode,
            "allow_stub": self.allow_stub,
        }


_TASK_ENV = {
    "docs.generate": "AGENTCORE_LITELLM_MODEL_DOCS",
    "rules.judge": "AGENTCORE_LITELLM_MODEL_JUDGE",
    "codegen.synthesize": "AGENTCORE_LITELLM_MODEL_CODEGEN",
    "embed.symbol": "AGENTCORE_LITELLM_MODEL_EMBED",
}

_TASK_DEFAULTS: dict[tuple[str, str], dict[str, Any]] = {
    ("docs.generate", "low"): {
        "max_tokens": 512,
        "json_mode": False,
        "allow_stub": True,
        "builtin_primary": "",
    },
    ("docs.generate", "medium"): {
        "max_tokens": 768,
        "json_mode": False,
        "allow_stub": True,
        "builtin_primary": "",
    },
    ("docs.generate", "high"): {
        "max_tokens": 1024,
        "json_mode": False,
        "allow_stub": False,
        "builtin_primary": "",
    },
    ("rules.judge", "low"): {
        "max_tokens": 512,
        "json_mode": True,
        "allow_stub": True,
        "builtin_primary": "",
    },
    ("rules.judge", "medium"): {
        "max_tokens": 768,
        "json_mode": True,
        "allow_stub": False,
        "builtin_primary": "",
    },
    ("rules.judge", "high"): {
        "max_tokens": 1024,
        "json_mode": True,
        "allow_stub": False,
        "builtin_primary": "",
    },
    ("codegen.synthesize", "low"): {
        "max_tokens": 1024,
        "json_mode": False,
        "allow_stub": True,
        "builtin_primary": "",
    },
    ("codegen.synthesize", "medium"): {
        "max_tokens": 2048,
        "json_mode": False,
        "allow_stub": False,
        "builtin_primary": "",
    },
    ("codegen.synthesize", "high"): {
        "max_tokens": 4096,
        "json_mode": False,
        "allow_stub": False,
        "builtin_primary": "",
    },
    ("embed.symbol", "low"): {
        "max_tokens": None,
        "json_mode": False,
        "allow_stub": True,
        "builtin_primary": "",
    },
    ("embed.symbol", "medium"): {
        "max_tokens": None,
        "json_mode": False,
        "allow_stub": True,
        "builtin_primary": "",
    },
    ("embed.symbol", "high"): {
        "max_tokens": None,
        "json_mode": False,
        "allow_stub": False,
        "builtin_primary": "",
    },
}


def _parse_fallbacks(raw: str) -> tuple[str, ...]:
    parts = [p.strip() for p in raw.replace(";", ",").split(",")]
    return tuple(p for p in parts if p)


def resolve_route(
    task_class: str,
    *,
    risk_level: str | None = None,
    default_model: str = "",
    profile_id: str | None = None,
) -> RouteDecision:
    """Resolve LiteLLM model aliases for a task class from env + built-in defaults."""
    risk = (risk_level or os.environ.get("AGENTCORE_LITELLM_RISK_LEVEL", "low")).strip().lower() or "low"
    if risk not in {"low", "medium", "high"}:
        risk = "low"

    meta = _TASK_DEFAULTS.get((task_class, risk)) or _TASK_DEFAULTS.get((task_class, "low")) or {
        "max_tokens": 512,
        "json_mode": False,
        "allow_stub": True,
        "builtin_primary": "",
    }

    env_key = _TASK_ENV.get(task_class, "")
    primary = (os.environ.get(env_key, "").strip() if env_key else "") or ""
    if not primary:
        primary = default_model.strip()
    if not primary:
        primary = str(meta.get("builtin_primary") or "").strip()

    fallback_env = os.environ.get("AGENTCORE_LITELLM_FALLBACK_MODELS", "").strip()
    fallbacks = _parse_fallbacks(fallback_env)

    allow_stub = bool(meta["allow_stub"])
    # Force stub-friendly behavior when no model is configured.
    if not primary:
        allow_stub = True

    return RouteDecision(
        profile_id=profile_id or os.environ.get("AGENTCORE_LITELLM_PROFILE_ID", "env-default").strip() or "env-default",
        task_class=task_class,
        risk_level=risk,
        primary_model=primary,
        fallback_models=fallbacks,
        max_tokens=meta.get("max_tokens"),  # type: ignore[arg-type]
        json_mode=bool(meta.get("json_mode")),
        allow_stub=allow_stub,
    )


def docs_generation_enabled() -> bool:
    raw = os.environ.get("AGENTCORE_LITELLM_DOCS_ENABLED", "true").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def embeddings_generation_enabled() -> bool:
    raw = os.environ.get("AGENTCORE_LITELLM_EMBEDDINGS_ENABLED", "false").strip().lower()
    return raw not in {"0", "false", "no", "off"}
