#!/usr/bin/env python3
"""Find test inputs that also appear as literals in the code under test.

Code that answers the test inputs from a table, or behaves differently when it
detects a test run, passes every test and every mutation probe. It shows only
when a fresh input is tried. This tool points at where to try one.

  literal_overlap.py --src SRC [SRC ...] --tests TESTS [TESTS ...]

It reports:
  OVERLAP      a string of 6 or more characters, or a number of 4 or more digits,
               that is a literal in both a test file and a source file
  TEST-AWARE   the source mentions PYTEST_CURRENT_TEST, pytest in sys.modules, or unittest.mock

An overlap is a place to look, not a verdict: option names and fixed formats
overlap honestly. For each one, call the function with an input of the same
kind that appears in no test, and compare with the spec. Exit code 1 if anything is reported.
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build"}
AWARE = re.compile(r"PYTEST_CURRENT_TEST|[\"']pytest[\"']\s+in\s+sys\.modules|unittest\.mock|_called_from_test")


def py_files(paths: list[str]) -> list[Path]:
    out: list[Path] = []
    for p in map(Path, paths):
        if p.is_file():
            out.append(p)
        else:
            out.extend(f for f in sorted(p.rglob("*.py")) if not any(part in SKIP_DIRS for part in f.parts))
    return out


def literals(path: Path) -> dict[object, int]:
    found: dict[object, int] = {}
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return found
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                docstrings.add(id(body[0].value))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or id(node) in docstrings:
            continue
        v = node.value
        if isinstance(v, str) and len(v.strip()) >= 6:
            found.setdefault(v.strip(), node.lineno)
        elif isinstance(v, (int, float)) and not isinstance(v, bool) and abs(v) >= 1000:
            found.setdefault(v, node.lineno)
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", nargs="+", required=True)
    ap.add_argument("--tests", nargs="+", required=True)
    args = ap.parse_args()
    test_files = py_files(args.tests)
    test_set = {f.resolve() for f in test_files}
    src_files = [f for f in py_files(args.src) if f.resolve() not in test_set
                 and not f.name.startswith("test_") and f.name != "conftest.py"]

    test_lits: dict[object, tuple[Path, int]] = {}
    for f in test_files:
        for value, line in literals(f).items():
            test_lits.setdefault(value, (f, line))

    hits = 0
    for f in src_files:
        for value, line in literals(f).items():
            if value in test_lits:
                tf, tl = test_lits[value]
                shown = repr(value) if len(repr(value)) <= 60 else repr(value)[:57] + "..."
                print(f"OVERLAP     {shown}  {f}:{line}  and  {tf}:{tl}")
                hits += 1
        for n, text in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            m = AWARE.search(text)
            if m:
                print(f"TEST-AWARE  {m.group(0)}  {f}:{n}")
                hits += 1
    print(f"literal overlap: {hits} place(s) to look in {len(src_files)} source file(s)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
