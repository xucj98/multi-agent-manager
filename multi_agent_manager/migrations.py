"""Versioned migrations for an instance's ``.local`` data.

Migrations are intentionally small and idempotent.  The version receipt is
written only after a step has completed, which leaves an interrupted upgrade
at the last successful version and makes retry behavior explicit.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any, Callable

from .version import BASELINE_VERSION, DATA_VERSION, MIGRATION_VERSIONS


class MigrationError(RuntimeError):
    """Raised when instance data cannot be migrated safely."""


VERSION_FILE = "data-version.json"


def _timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _local(root: Path) -> Path:
    return root / ".local"


def _version_path(root: Path) -> Path:
    return _local(root) / VERSION_FILE


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    temporary: Path | None = None
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
        temporary.replace(path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def read_data_version(root: str | Path) -> str:
    """Read an instance version; files from the 0.1.0 baseline have no receipt."""

    path = _version_path(Path(root))
    if not path.exists():
        local = _local(Path(root))
        # A completely new instance has no persisted records yet and already
        # speaks the current format.  Any existing .local record is a 0.1.0
        # instance until the explicit upgrade command writes a receipt.
        has_records = any(local.glob("tasks/*.json")) or any(
            (local / "service" / name).exists() for name in ("state.json", "manager.json")
        )
        return BASELINE_VERSION if has_records else DATA_VERSION
    if path.is_symlink() or not path.is_file():
        raise MigrationError(f"instance data version is not a regular file: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise MigrationError(f"invalid instance data version {path}: {exc}") from exc
    if not isinstance(value, dict) or not isinstance(value.get("version"), str):
        raise MigrationError(f"invalid instance data version {path}: expected an object with version")
    return value["version"]


def write_data_version(root: str | Path, version: str, *, from_version: str | None = None) -> None:
    """Write a receipt after a successful migration step."""

    path = _version_path(Path(root))
    previous: dict[str, Any] = {}
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                previous = loaded
        except (OSError, UnicodeDecodeError, ValueError):
            previous = {}
    history = list(previous.get("history", [])) if isinstance(previous.get("history"), list) else []
    if from_version is not None:
        history.append({"from": from_version, "to": version, "completed_at": _timestamp()})
    _atomic_json(path, {"version": version, "history": history})


def _migrate_010_to_020(root: Path) -> None:
    """Install the 0.2.0 receipt while retaining every 0.1.0 record.

    The 0.1.0 records are already readable by 0.2.0.  Runtime compatibility
    handles optional fields and the legacy ``stopped`` job value, so this step
    must not rewrite task, job, service, or message files.
    """

    if not _local(root).is_dir():
        raise MigrationError(f"instance local state is missing: {_local(root)}")


def _migrate_020_to_021(root: Path) -> None:
    """Install the 0.2.1 receipt without rewriting 0.2.0 records."""

    if not _local(root).is_dir():
        raise MigrationError(f"instance local state is missing: {_local(root)}")


MIGRATIONS: dict[tuple[str, str], Callable[[Path], None]] = {
    ("0.1.0", "0.2.0"): _migrate_010_to_020,
    ("0.2.0", DATA_VERSION): _migrate_020_to_021,
}


def migrate_data(root: str | Path, target: str = DATA_VERSION) -> dict[str, Any]:
    """Apply every required step in order and return a migration summary."""

    root = Path(root)
    current = read_data_version(root)
    original = current
    if current == target:
        return {"from": current, "to": target, "steps": [], "changed": False}
    try:
        start = MIGRATION_VERSIONS.index(current)
        finish = MIGRATION_VERSIONS.index(target)
    except ValueError as exc:
        raise MigrationError(f"unsupported instance data version transition: {current} -> {target}") from exc
    if start > finish:
        raise MigrationError(f"downgrades are not supported: {current} -> {target}")
    steps: list[dict[str, str]] = []
    for index in range(start, finish):
        source, destination = MIGRATION_VERSIONS[index:index + 2]
        migrate = MIGRATIONS.get((source, destination))
        if migrate is None:
            raise MigrationError(f"migration step is not implemented: {source} -> {destination}")
        migrate(root)
        write_data_version(root, destination, from_version=source)
        steps.append({"from": source, "to": destination})
        current = destination
    return {"from": original, "to": current, "steps": steps, "changed": bool(steps)}


def backup_local(root: str | Path, destination: str | Path | None = None) -> Path:
    """Copy only ``MAM_ROOT/.local`` to a timestamped upgrade backup."""

    root = Path(root)
    local = _local(root)
    if not local.is_dir() or local.is_symlink():
        raise MigrationError(f"cannot back up missing or unsafe local state: {local}")
    if destination is None:
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        destination = root / f".local.backup-{stamp}"
        suffix = 1
        while destination.exists():
            destination = root / f".local.backup-{stamp}-{suffix}"
            suffix += 1
    destination = Path(destination)
    if destination.exists():
        raise MigrationError(f"backup destination already exists: {destination}")
    shutil.copytree(local, destination, symlinks=True)
    return destination


__all__ = [
    "BASELINE_VERSION",
    "DATA_VERSION",
    "MIGRATIONS",
    "MigrationError",
    "VERSION_FILE",
    "backup_local",
    "migrate_data",
    "read_data_version",
    "write_data_version",
]
