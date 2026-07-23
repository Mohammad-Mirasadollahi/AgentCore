"""Framework DI / injection binding extraction (GAP-002 Phase F3).

Detects common Depends / constructor-injection patterns and returns
consumer→provider bindings for ingest to emit CALLS edges with
``provenance=di_injection``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


# FastAPI / Starlette: Depends(provider) or Annotated[..., Depends(provider)]
_PY_DEPENDS = re.compile(
    r"Depends\(\s*(?P<provider>[A-Za-z_][\w.]*)\s*\)",
    re.MULTILINE,
)

# NestJS / TS: constructor(private readonly foo: FooService)
_TS_CTOR_PARAM = re.compile(
    r"constructor\s*\((?P<body>[^)]*)\)",
    re.MULTILINE | re.DOTALL,
)
_TS_PARAM_TYPE = re.compile(
    r"(?:private|public|protected|readonly|\s)+(?P<name>[A-Za-z_]\w*)\s*:\s*(?P<type>[A-Za-z_][\w.]*)",
)

# Nest @Inject(TOKEN) on a parameter — capture token identifier
_TS_INJECT = re.compile(
    r"@Inject\(\s*[\"']?(?P<token>[A-Za-z_][\w.]*)[\"']?\s*\)",
    re.MULTILINE,
)

# Nearest preceding def/class for Python Depends sites
_PY_DEF_OR_CLASS = re.compile(
    r"^(?:async\s+)?(?:def|class)\s+(?P<name>[A-Za-z_]\w*)\s*[\(:]",
    re.MULTILINE,
)


@dataclass(frozen=True)
class ExtractedInjection:
    consumer_name: str
    provider_name: str
    framework: str
    pattern: str
    line_hint: int = 0


def extract_injections(
    source: str, *, language: str, file_path: str = ""
) -> list[ExtractedInjection]:
    """Extract DI bindings from a source file (deterministic, no LLM)."""
    lang = (language or "").lower().strip()
    if lang in {"python", "py"}:
        return _extract_python(source)
    if lang in {"javascript", "js", "typescript", "ts", "tsx", "jsx"}:
        return _extract_typescript(source)
    return []


def _extract_python(source: str) -> list[ExtractedInjection]:
    out: list[ExtractedInjection] = []
    for match in _PY_DEPENDS.finditer(source):
        provider = match.group("provider").split(".")[-1]
        consumer = _nearest_def_or_class(source, match.start()) or "__module__"
        line_hint = source[: match.start()].count("\n") + 1
        out.append(
            ExtractedInjection(
                consumer_name=consumer,
                provider_name=provider,
                framework="fastapi",
                pattern="Depends",
                line_hint=line_hint,
            )
        )
    return out


def _extract_typescript(source: str) -> list[ExtractedInjection]:
    out: list[ExtractedInjection] = []
    class_names = [
        m.group("name")
        for m in re.finditer(r"class\s+(?P<name>[A-Za-z_]\w*)", source)
    ]
    default_consumer = class_names[-1] if class_names else "__module__"

    for match in _TS_CTOR_PARAM.finditer(source):
        body = match.group("body")
        consumer = _nearest_class_before(source, match.start()) or default_consumer
        line_hint = source[: match.start()].count("\n") + 1
        for param in _TS_PARAM_TYPE.finditer(body):
            provider = param.group("type").split(".")[-1]
            out.append(
                ExtractedInjection(
                    consumer_name=consumer,
                    provider_name=provider,
                    framework="nestjs_or_ts",
                    pattern="constructor_type",
                    line_hint=line_hint,
                )
            )

    for match in _TS_INJECT.finditer(source):
        token = match.group("token").split(".")[-1]
        consumer = _nearest_class_before(source, match.start()) or default_consumer
        line_hint = source[: match.start()].count("\n") + 1
        out.append(
            ExtractedInjection(
                consumer_name=consumer,
                provider_name=token,
                framework="nestjs",
                pattern="Inject",
                line_hint=line_hint,
            )
        )
    return out


def _nearest_def_or_class(source: str, pos: int) -> str | None:
    best: str | None = None
    best_start = -1
    for match in _PY_DEF_OR_CLASS.finditer(source):
        if match.start() <= pos and match.start() >= best_start:
            best = match.group("name")
            best_start = match.start()
    return best


def _nearest_class_before(source: str, pos: int) -> str | None:
    best: str | None = None
    best_start = -1
    for match in re.finditer(r"class\s+(?P<name>[A-Za-z_]\w*)", source):
        if match.start() <= pos and match.start() >= best_start:
            best = match.group("name")
            best_start = match.start()
    return best
