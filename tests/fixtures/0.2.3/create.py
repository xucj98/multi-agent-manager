"""Create a 0.2.3 fixture with its program writer and current data receipt."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import runpy
import sys


_writer = runpy.run_path(str(Path(__file__).resolve().parents[1] / "0.2.0" / "create.py"))


def create(*, project_root: Path, mam_root: Path, package_parent: Path, version: str = "0.2.3") -> dict:
    result = _writer["create"](
        project_root=project_root, mam_root=mam_root, package_parent=package_parent, version=version
    )
    sys.path.insert(0, str(package_parent))
    from multi_agent_manager import migrations
    from multi_agent_manager.version import DATA_VERSION

    if version != DATA_VERSION:
        raise RuntimeError(f"fixture version {version} does not match its writer {DATA_VERSION}")
    migrations.write_data_version(mam_root, DATA_VERSION)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--mam-root", type=Path)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--version", default="0.2.3")
    args = parser.parse_args(argv)
    project = (args.project_root or args.root).resolve()
    mam_root = (args.mam_root or project / "multi-agent-manager").resolve()
    print(json.dumps(create(project_root=project, mam_root=mam_root, package_parent=args.package.resolve(), version=args.version), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
