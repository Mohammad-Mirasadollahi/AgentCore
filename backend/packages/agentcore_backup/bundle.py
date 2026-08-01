"""Pack/unpack .acbak archives (gzip tar)."""

from __future__ import annotations

import tarfile
import tempfile
from pathlib import Path


def pack_directory(src_dir: Path, dest_acbak: Path) -> Path:
    dest_acbak.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(dest_acbak, "w:gz") as tar:
        for path in sorted(src_dir.rglob("*")):
            if path.is_file():
                tar.add(path, arcname=path.relative_to(src_dir).as_posix())
    return dest_acbak


def unpack_archive(acbak: Path, dest_dir: Path | None = None) -> Path:
    if not acbak.is_file():
        raise FileNotFoundError(f"bundle not found: {acbak}")
    out = dest_dir or Path(tempfile.mkdtemp(prefix="acbak-"))
    out.mkdir(parents=True, exist_ok=True)
    with tarfile.open(acbak, "r:gz") as tar:
        # Python 3.12+ filter for path traversal safety when available.
        try:
            tar.extractall(out, filter="data")
        except TypeError:
            tar.extractall(out)
    return out
