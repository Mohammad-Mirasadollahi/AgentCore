from __future__ import annotations

from dataclasses import dataclass
import os

from .core import AdapterService
from .postgres_store import PostgresStore


@dataclass(frozen=True)
class Settings:
    database_url: str

    @classmethod
    def from_environment(cls) -> "Settings":
        database_url = os.environ.get("AGENTCORE_ADAPTER_SERVICE_DATABASE_URL", "").strip()
        if not database_url:
            raise RuntimeError("AGENTCORE_ADAPTER_SERVICE_DATABASE_URL is required")
        if not database_url.startswith(("postgresql://", "postgresql+psycopg://")):
            raise RuntimeError("AGENTCORE_ADAPTER_SERVICE_DATABASE_URL must use PostgreSQL")
        return cls(database_url=database_url)


def build_service(settings: Settings | None = None) -> AdapterService:
    resolved = settings or Settings.from_environment()
    return AdapterService(PostgresStore(resolved.database_url))
