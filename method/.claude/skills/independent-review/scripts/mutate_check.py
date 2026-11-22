#!/usr/bin/env python3
"""Break the code behind a requirement, watch its tests, put the code back.

A test proves a requirement only if it fails when the code is wrong. This tool
breaks one function three ways and runs the tests each time:

  gut    the body becomes `return None`
  raise  the body becomes `raise RuntimeError("mutation probe")`
  flip   every comparison, and/or, True/False, +/- is inverted and every
         integer constant is raised by one

  mutate_check.py FILE:FUNCTION [--req REQ-012[,REQ-013]] [--probes gut,raise,flip]
                  [--timeout 120] [--show] [-- extra pytest arguments]
  mutate_check.py FILE:L40-L52 ...        deletes those lines instead (one probe, "delete")

FUNCTION may be `name` or `Class.method`. With --req only tests tagged with one
of those requirement ids run. Run it with the project's interpreter from the
project root, for example:
  uv run python ../../.claude/skills/independent-review/scripts/mutate_check.py \
      src/inkproof/match.py:find_terms --req REQ-016

Result per probe: killed (tests failed, which is what a real test does) or
SURVIVED (tests still passed with broken code). Exit code 1 if any probe survived.
The file is restored byte for byte after every probe and its hash is checked.

How to read survivors:
  gut and raise both survive      the tests never execute this code (mock, empty fixture, wrong target)
  gut survives, raise is killed   the code runs but nothing about its result is asserted
  raise survives, gut is killed   the test accepts any exception
  only flip survives              the assertions are too weak to tell right from wrong

All probes killed does not prove the code right. Code that answers the test
inputs from a table is killed by every probe: see literal_overlap.py.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import os
import re
import signal
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent

CMP = {ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.Lt: ast.GtE, ast.GtE: ast.Lt, ast.Gt: ast.LtE,
       ast.LtE: ast.Gt, ast.Is: ast.IsNot, ast.IsNot: ast.Is, ast.In: ast.NotIn, ast.NotIn: ast.In}
ARITH = {ast.Add: ast.Sub, ast.Sub: ast.Add}


class Flip(ast.NodeTransformer):
    def visit_Compare(self, node):
        self.generic_visit(node)
        node.ops = [CMP.get(type(op), type(op))() for op in node.ops]
        return node

    def visit_BoolOp(self, node):
        self.generic_visit(node)
        node.op = ast.Or() if isinstance(node.op, ast.And) else ast.And()
        return node

    def visit_UnaryOp(self, node):
        if isinstance(node.op, ast.Not):
            return node.operand  # drop the `not`; leave the operand alone so the two do not cancel
        self.generic_visit(node)
        return node

    def visit_BinOp(self, node):
        self.generic_visit(node)
        if type(node.op) in ARITH:
            node.op = ARITH[type(node.op)]()
        return node

    def visit_AugAssign(self, node):
        self.generic_visit(node)
        if type(node.op) in ARITH:
            node.op = ARITH[type(node.op)]()
        return node

    def visit_Constant(self, node):
        if isinstance(node.value, bool):
            return ast.copy_location(ast.Constant(value=not node.value), node)
        if isinstance(node.value, int):
            return ast.copy_location(ast.Constant(value=node.value + 1), node)
        return node

    def _negate_bare(self, test):
        if isinstance(test, (ast.Compare, ast.BoolOp, ast.UnaryOp, ast.Constant)):
            return self.visit(test)
        return ast.UnaryOp(op=ast.Not(), operand=test)

    def visit_If(self, node):
        node.test = self._negate_bare(node.test)
        node.body = [self.visit(s) for s in node.body]
        node.orelse = [self.visit(s) for s in node.orelse]
        return node

    def visit_IfExp(self, node):
        node.test = self._negate_bare(node.test)
        node.body = self.visit(node.body)
        node.orelse = self.visit(node.orelse)
        return node


def find_function(tree: ast.Module, qual: str):
    parts = qual.split(".")
    body = tree.body
    node = None
    for i, part in enumerate(parts):
        matches = [n for n in body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                   and n.name == part]
        if not matches:
            return None
        node = matches[-1]  # the last definition is the one Python keeps
        body = node.body
    return node if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else None


def mutated_source(src: str, qual: str, probe: str) -> str | None:
    tree = ast.parse(src)
    fn = find_function(tree, qual)
    if fn is None:
        sys.exit(f"function not found: {qual}")
    start = min([d.lineno for d in fn.decorator_list] + [fn.lineno])
    end = fn.end_lineno
    doc = fn.body[:1] if (fn.body and isinstance(fn.body[0], ast.Expr)
                          and isinstance(getattr(fn.body[0], "value", None), ast.Constant)
                          and isinstance(fn.body[0].value.value, str)) else []
    before = ast.unparse(fn)
    if probe == "gut":
        fn.body = doc + [ast.Return(value=ast.Constant(value=None))]
    elif probe == "raise":
        fn.body = doc + [ast.parse('raise RuntimeError("mutation probe")').body[0]]
    elif probe == "flip":
        fn.body = doc + [Flip().visit(s) for s in fn.body[len(doc):]]
    else:
        sys.exit(f"unknown probe: {probe}")
    ast.fix_missing_locations(fn)
    after = ast.unparse(fn)
    if after == before:
        return None
    lines = src.splitlines(keepends=True)
    indent = " " * fn.col_offset
    block = textwrap.indent(after, indent) + "\n"
    return "".join(lines[:start - 1]) + block + "".join(lines[end:])


def deleted_lines(src: str, first: int, last: int) -> str:
    lines = src.splitlines(keepends=True)
    if not (1 <= first <= last <= len(lines)):
        sys.exit(f"line range outside file: L{first}-L{last}")
    indent = re.match(r"\s*", lines[first - 1]).group(0)
    return "".join(lines[:first - 1]) + indent + "pass\n" + "".join(lines[last:])


def run_tests(extra: list[str], req: str | None, timeout: int, pyc: str) -> tuple[int, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(HERE) + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPYCACHEPREFIX"] = pyc
    cmd = [sys.executable, "-m", "pytest", "-q", "--no-header", "-x", "-p", "no:cacheprovider"]
    if req:
        env["REQPROBE_ONLY"] = req
        cmd += ["-p", "reqprobe"]
    cmd += extra
    try:
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return 124, f"timed out after {timeout}s"
    tail = [ln for ln in proc.stdout.strip().splitlines() if ln.strip()][-1:] or ["(no output)"]
    return proc.returncode, tail[0].strip("= ")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", help="FILE:FUNCTION, FILE:Class.method or FILE:L10-L20")
    ap.add_argument("--req", help="run only tests tagged with these requirement ids (comma-separated)")
    ap.add_argument("--probes", default="gut,raise,flip")
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--show", action="store_true", help="print each mutated version")
    argv = sys.argv[1:]
    extra = []
    if "--" in argv:
        cut = argv.index("--")
        argv, extra = argv[:cut], argv[cut + 1:]
    args = ap.parse_args(argv)

    file_part, _, what = args.target.rpartition(":")
    path = Path(file_part)
    if not file_part or not path.is_file():
        sys.exit(f"no such file: {file_part or args.target}")
    original = path.read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    stat = path.stat()
    src = original.decode("utf-8")

    line_range = re.fullmatch(r"L(\d+)-L(\d+)", what)
    probes = ["delete"] if line_range else [p.strip() for p in args.probes.split(",") if p.strip()]

    def restore(*_):
        path.write_bytes(original)
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))

    def on_signal(signum, frame):
        restore()
        sys.exit(130)

    signal.signal(signal.SIGTERM, on_signal)
    survived = 0
    with tempfile.TemporaryDirectory() as pyc:
        code, summary = run_tests(extra, args.req, args.timeout, pyc)
        scope = f"tests tagged {args.req}" if args.req else "tests"
        print(f"target:   {path}:{what}")
        print(f"baseline: {summary} (exit {code}, {scope})")
        if code == 5:
            print("NO TESTS SELECTED: nothing runs against this code, so nothing can prove it")
            return 2
        if code != 0:
            print("baseline is not green; fix that first")
            return 2
        try:
            for probe in probes:
                if probe == "delete":
                    new = deleted_lines(src, int(line_range.group(1)), int(line_range.group(2)))
                else:
                    new = mutated_source(src, what, probe)
                if new is None:
                    print(f"{probe:<7} n/a       nothing in this function for the probe to change")
                    continue
                try:
                    ast.parse(new)
                except SyntaxError as exc:
                    print(f"{probe:<7} n/a       mutated file would not parse ({exc.msg})")
                    continue
                if args.show:
                    print(f"--- {probe} ---")
                    print(new if probe == "delete" else ast.unparse(find_function(ast.parse(new), what)))
                path.write_bytes(new.encode("utf-8"))
                try:
                    code, summary = run_tests(extra, args.req, args.timeout, pyc)
                finally:
                    restore()
                if code == 0:
                    survived += 1
                    print(f"{probe:<7} SURVIVED  {summary}")
                else:
                    how = "timeout" if code == 124 else f"exit {code}"
                    print(f"{probe:<7} killed    {summary} ({how})")
        finally:
            restore()
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        print("RESTORE FAILED: the file differs from the original. Run `git diff` now.")
        return 3
    print("restored: file hash matches the original")
    print(f"result:   {survived} survived" if survived else "result:   all probes killed")
    return 1 if survived else 0


if __name__ == "__main__":
    sys.exit(main())
