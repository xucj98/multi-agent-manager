"""Program and persisted data version metadata.

The service state has its own schema version.  This module deliberately keeps
the user visible program release and the instance data version separate so a
service schema change cannot be mistaken for a data migration.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any

from .release import RELEASE_COMMIT, RELEASE_TAG, RELEASE_VERSION


PROGRAM_VERSION = RELEASE_VERSION
BASELINE_VERSION = "0.1.0"
DATA_VERSION = PROGRAM_VERSION
# Keep every released data format in the chain so a fresh 0.1.0 instance
# reaches the current format through every intermediate receipt.
MIGRATION_VERSIONS = (BASELINE_VERSION, "0.2.0", "0.2.1", "0.2.2", DATA_VERSION)


def source_commit() -> str | None:
    """Return a reproducible source commit when package metadata provides one."""

    if len(RELEASE_COMMIT) == 40 and all(char in "0123456789abcdef" for char in RELEASE_COMMIT):
        return RELEASE_COMMIT
    package_root = Path(__file__).resolve().parent.parent
    try:
        result = subprocess.run(
            ["git", "-C", str(package_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    commit = result.stdout.strip()
    return commit if result.returncode == 0 and commit else None


def info() -> dict[str, Any]:
    """Return stable JSON-serializable program metadata."""

    return {
        "version": PROGRAM_VERSION,
        "commit": source_commit(),
        "tag": RELEASE_TAG,
        "data_version": DATA_VERSION,
    }


__all__ = [
    "BASELINE_VERSION",
    "DATA_VERSION",
    "MIGRATION_VERSIONS",
    "PROGRAM_VERSION",
    "info",
    "source_commit",
]
