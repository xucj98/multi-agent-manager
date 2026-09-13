"""Task-local provenance check for the C2 cuRobo smoke validation copy.

This validates the installed extension without resolving its symlinked venv
path, because the C installer intentionally uses uv's symlink link mode.
"""

from __future__ import annotations

import base64
import csv
import hashlib
import importlib.metadata as importlib_metadata
from pathlib import Path
import sys
from typing import Any
import zipfile

DIST_NAME = "nvidia-curobo"
DIST_VERSION = "0.7.8"
DIST_INFO_NAME = "nvidia_curobo-0.7.8.dist-info"
EXTENSION_RELATIVE_PATH = "curobo/curobolib/geom_cu.cpython-310-x86_64-linux-gnu.so"
EXPECTED_EXTENSION_SHA256 = "874b95cb65d84eeb0a84562482de7551638f7c9974d3323b152142476f8abb01"
EXPECTED_EXTENSION_BYTES = 13_367_808
STABLE_WHEEL = Path(
    "/mnt/public/xcj/Projects/state-vla/.cache/curobo/wheel/"
    "nvidia_curobo-0.7.8-cp310-cp310-linux_x86_64.whl"
)
EXPECTED_WHEEL_SHA256 = "780a878713cad48043b4537268c860e52393ddeb46709a6377409f9c65f4f988"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _record_sha256_to_hex(value: str) -> str:
    if not value.startswith("sha256="):
        raise RuntimeError(f"unexpected RECORD digest: {value!r}")
    encoded = value.removeprefix("sha256=")
    padding = "=" * (-len(encoded) % 4)
    return base64.urlsafe_b64decode(encoded + padding).hex()


def _require_lexical_child(path: Path, parent: Path, label: str) -> Path:
    if not path.is_absolute() or not parent.is_absolute():
        raise RuntimeError(f"{label} must be an absolute lexical path")
    try:
        return path.relative_to(parent)
    except ValueError as exc:
        raise RuntimeError(f"{label} is outside runtime venv: {path}") from exc


def verify_curobo_extension_origin(module_file: str) -> dict[str, Any]:
    """Verify the runtime venv, installed distribution, RECORD, and wheel content.

    The lexical venv test deliberately does not call ``Path.resolve()``: its
    target is installed through the approved uv symlink-mode environment.
    """

    runtime_prefix = Path(sys.prefix)
    runtime_executable = Path(sys.executable)
    python_tag = f"python{sys.version_info.major}.{sys.version_info.minor}"
    site_packages = runtime_prefix / "lib" / python_tag / "site-packages"
    extension = Path(module_file)

    _require_lexical_child(runtime_executable, runtime_prefix / "bin", "runtime interpreter")
    relative_extension = _require_lexical_child(extension, site_packages, "cuRobo extension")
    if relative_extension.as_posix() != EXTENSION_RELATIVE_PATH:
        raise RuntimeError(
            "unexpected cuRobo extension location in runtime venv: "
            f"{relative_extension.as_posix()}"
        )
    if not extension.is_file():
        raise RuntimeError(f"cuRobo extension is unavailable: {extension}")

    distribution = importlib_metadata.distribution(DIST_NAME)
    normalized_name = distribution.metadata["Name"].lower().replace("_", "-")
    if normalized_name != DIST_NAME or distribution.version != DIST_VERSION:
        raise RuntimeError(
            "unexpected cuRobo distribution: "
            f"{distribution.metadata['Name']} {distribution.version}"
        )

    record_path = site_packages / DIST_INFO_NAME / "RECORD"
    _require_lexical_child(record_path, site_packages, "distribution RECORD")
    if not record_path.is_file():
        raise RuntimeError(f"runtime distribution RECORD is unavailable: {record_path}")
    distribution_record = distribution.read_text("RECORD")
    lexical_record = record_path.read_text(encoding="utf-8")
    if distribution_record != lexical_record:
        raise RuntimeError("distribution RECORD does not match runtime venv RECORD")

    record_rows = list(csv.reader(lexical_record.splitlines()))
    try:
        record_entry = next(row for row in record_rows if row and row[0] == EXTENSION_RELATIVE_PATH)
    except StopIteration as exc:
        raise RuntimeError("runtime distribution RECORD lacks the cuRobo extension") from exc
    if len(record_entry) != 3 or not record_entry[1] or not record_entry[2]:
        raise RuntimeError(f"invalid cuRobo extension RECORD entry: {record_entry!r}")

    extension_size = extension.stat().st_size
    extension_sha256 = _sha256(extension)
    record_sha256 = _record_sha256_to_hex(record_entry[1])
    if int(record_entry[2]) != extension_size:
        raise RuntimeError("cuRobo extension size differs from runtime RECORD")
    if extension_sha256 != record_sha256:
        raise RuntimeError("cuRobo extension digest differs from runtime RECORD")
    if extension_size != EXPECTED_EXTENSION_BYTES or extension_sha256 != EXPECTED_EXTENSION_SHA256:
        raise RuntimeError("cuRobo extension differs from the Manager-verified expected content")

    if not STABLE_WHEEL.is_file():
        raise RuntimeError(f"Manager-verified stable wheel is unavailable: {STABLE_WHEEL}")
    wheel_sha256 = _sha256(STABLE_WHEEL)
    if wheel_sha256 != EXPECTED_WHEEL_SHA256:
        raise RuntimeError("stable wheel digest differs from the Manager-verified wheel")
    with zipfile.ZipFile(STABLE_WHEEL) as archive:
        try:
            wheel_member = archive.read(EXTENSION_RELATIVE_PATH)
        except KeyError as exc:
            raise RuntimeError("stable wheel lacks the cuRobo extension member") from exc
    wheel_member_sha256 = hashlib.sha256(wheel_member).hexdigest()
    if len(wheel_member) != extension_size or wheel_member_sha256 != extension_sha256:
        raise RuntimeError("runtime cuRobo extension differs from stable wheel content")

    return {
        "runtime_prefix": str(runtime_prefix),
        "runtime_executable": str(runtime_executable),
        "site_packages_lexical": str(site_packages),
        "extension_lexical": str(extension),
        "distribution": {"name": distribution.metadata["Name"], "version": distribution.version},
        "record_path_lexical": str(record_path),
        "record_sha256": record_sha256,
        "record_bytes": int(record_entry[2]),
        "extension_sha256": extension_sha256,
        "extension_bytes": extension_size,
        "stable_wheel": str(STABLE_WHEEL),
        "stable_wheel_sha256": wheel_sha256,
        "stable_wheel_member_sha256": wheel_member_sha256,
    }
