from __future__ import annotations

from dataclasses import dataclass
import os

from .core import CodeGraphService
from .postgres_store import PostgresStore


@dataclass(frozen=True)
class Settings:
    database_url: str

    @classmethod
    def from_environment(cls) -> "Settings":
        database_url = os.environ.get("AGENTCORE_CODE_GRAPH_DATABASE_URL", "").strip()
        if not database_url:
            raise RuntimeError("AGENTCORE_CODE_GRAPH_DATABASE_URL is required")
        if not database_url.startswith(("postgresql://", "postgresql+psycopg://")):
            raise RuntimeError("AGENTCORE_CODE_GRAPH_DATABASE_URL must use PostgreSQL")
        return cls(database_url=database_url)


def build_service(settings: Settings | None = None) -> CodeGraphService:
    resolved = settings or Settings.from_environment()
    return CodeGraphService(PostgresStore(resolved.database_url))
