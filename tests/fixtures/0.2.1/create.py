"""Create a 0.2.1 fixture using the unchanged 0.2.x writer contract."""
from __future__ import annotations

from pathlib import Path
import runpy


_writer = runpy.run_path(str(Path(__file__).resolve().parents[1] / "0.2.0" / "create.py"))
main = _writer["main"]


if __name__ == "__main__":
    raise SystemExit(main())
