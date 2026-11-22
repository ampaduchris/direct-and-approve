#!/usr/bin/env python3
"""Import every script of the repository with the standard library only (spec REQ-003).

  python3 -I scripts/check_imports.py

Imports each file under `scripts/` and `method/tools/` by path, in isolated mode, and prints one
line per file. A script that needs a third-party module fails here. Importing runs no command,
because every script guards its entry point. Exit 1 if any import fails. Standard library only.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True  # importing must not leave bytecode under method/, which the manifest check counts


def main() -> int:
    files = sorted([*(ROOT / "scripts").glob("*.py"), *(ROOT / "method/tools").glob("*.py")])
    failed = 0
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        try:
            spec = importlib.util.spec_from_file_location(f"checked_{path.stem}", path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            print(f"ok   {rel}")
        except BaseException as exc:  # noqa: BLE001 - report any failure, including SystemExit
            failed += 1
            print(f"FAIL {rel}: {type(exc).__name__}: {exc}")
    print(f"check_imports: {len(files)} script(s), {failed} failed, python {sys.version.split()[0]}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
