#!/usr/bin/env python3
"""Privacy boundary check (spec REQ-111 and REQ-112).

  python3 scripts/boundary.py [--root DIR]

Reads [boundary] and [forbidden] of extract.toml in the root. Fails (exit 1) if a path of the tree
matches a forbidden path and no allowed path, or if a forbidden pattern matches a line of any text
file not on the allowlist. Prints the path and line number, never the matched text. Exit 3 if the
mapping cannot be read. Standard library only.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract import any_match  # noqa: E402

SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", ".hypothesis", ".mypy_cache",
             ".ruff_cache", "mutants"}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="boundary.py")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    root = Path(ap.parse_args(argv).root)
    try:
        cfg = tomllib.loads((root / "extract.toml").read_text(encoding="utf-8"))
        patterns = [re.compile(p) for p in cfg.get("forbidden", {}).get("patterns", [])]
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError, re.error):
        print("boundary: extract.toml is missing or cannot be read", file=sys.stderr)
        return 3
    b = cfg.get("boundary", {})
    forbidden, allowed, skip_patterns = b.get("forbidden_paths", []), b.get("allow_paths", []), b.get("pattern_allowlist", [])
    problems, scanned = [], 0
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        here = Path(dirpath)
        keep = []
        for d in sorted(dirnames):
            rel = (here / d).relative_to(root).as_posix()
            if d in SKIP_DIRS or (here / d).is_symlink():
                continue
            if any_match(forbidden, rel) and not any_match(allowed, rel):
                problems.append(f"forbidden path: {rel}/")
                continue  # not descended: one line for the folder
            keep.append(d)
        dirnames[:] = keep
        for name in sorted(filenames):
            p = here / name
            rel = p.relative_to(root).as_posix()
            if p.is_symlink():
                continue
            if any_match(forbidden, rel) and not any_match(allowed, rel):
                problems.append(f"forbidden path: {rel}")
                continue
            if any_match(skip_patterns, rel):
                continue
            try:
                text = p.read_bytes().decode("utf-8")
            except (OSError, UnicodeDecodeError):
                continue  # not a text file
            scanned += 1
            for n, line in enumerate(text.split("\n"), 1):
                if any(pat.search(line) for pat in patterns):
                    problems.append(f"{rel}:{n}: forbidden pattern")
    for p in problems:
        print(p)
    if problems:
        print(f"boundary: {len(problems)} problem(s)")
        return 1
    print(f"boundary: OK, {scanned} text files scanned")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
