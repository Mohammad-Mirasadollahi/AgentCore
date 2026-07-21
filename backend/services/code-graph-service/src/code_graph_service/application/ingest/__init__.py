"""Ingest use cases (modular)."""

from __future__ import annotations

from ..support import GraphServiceSupport
from .file_ingest import FileIngestMixin
from .human_docs import HumanDocIngestMixin
from .repo_ingest import RepoIngestMixin
from .sync import SyncMixin


class IngestUseCases(
    FileIngestMixin,
    HumanDocIngestMixin,
    RepoIngestMixin,
    SyncMixin,
    GraphServiceSupport,
):
    """Application ingest surface composed from focused mixins."""

    pass

__all__ = [
    "IngestUseCases",
    "FileIngestMixin",
    "HumanDocIngestMixin",
    "RepoIngestMixin",
    "SyncMixin",
]
