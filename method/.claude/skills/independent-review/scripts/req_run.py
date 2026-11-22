#!/usr/bin/env python3
"""Requirement trace by running, not by reading tags.

For each requirement id it prints: the tests that carry the tag in the source,
the tests pytest actually ran, their outcomes, and how many plain `assert`
statements passed. A requirement tag proves nothing until a test that carries
it runs, passes and asserts.

  req_run.py [--spec docs/spec.md] [--tests tests] [-- extra pytest arguments]

Run it with the project's interpreter, from the project root, for example:
  uv run python ../../.claude/skills/independent-review/scripts/req_run.py --spec docs/spec.md

Flags (any flag on a MUST or MUST NOT makes the exit code 1):
  NO-TEST          no test carries the tag
  NOT-COLLECTED    a tagged function exists in the source but pytest never ran it
  NO-PASSING-TEST  tests exist but none passed
  SKIPPED XFAIL XPASS FAILED ERROR   outcome of at least one tagged test
  ZERO-ASSERT      a tagged test passed with no assert executed and no raises/warns/mock check
  BROAD-RAISES     pytest.raises(Exception) or (BaseException): any error satisfies the test
  SWALLOWS         a try/except in the test that hides a failure
  UNKNOWN-ID       a tag names an id that is not in the spec
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build", ".tox"}
REQ_ROW = re.compile(r"^\|\s*(REQ-\d+)\s*\|\s*([A-Z ]+?)\s*\|")


def spec_rows(path: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = REQ_ROW.match(line)
        if m:
            rows[m.group(1)] = " ".join(m.group(2).split())
    return rows


def _dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Attribute):
        return _dotted(node.value) + "." + node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def _req_args(dec: ast.AST) -> list[str]:
    if isinstance(dec, ast.Call) and _dotted(dec.func).endswith("mark.req"):
        return [a.value for a in dec.args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
    return []


def _marks(decs: list[ast.AST]) -> tuple[list[str], list[str]]:
    reqs: list[str] = []
    other: list[str] = []
    for dec in decs:
        reqs.extend(_req_args(dec))
        name = _dotted(dec.func if isinstance(dec, ast.Call) else dec)
        for word in ("skipif", "skip", "xfail"):
            if name.endswith("mark." + word):
                other.append(word)
                break
    return reqs, other


def _features(fn: ast.AST) -> dict:
    asserts = raises = mock_checks = 0
    broad = swallow = False
    for node in ast.walk(fn):
        if isinstance(node, ast.Assert):
            asserts += 1
        elif isinstance(node, ast.Call):
            name = _dotted(node.func)
            last = name.rsplit(".", 1)[-1]
            if name.endswith(("pytest.raises", "pytest.warns", "pytest.fail", "pytest.deprecated_call")):
                raises += 1
                if node.args and _dotted(node.args[0]) in ("Exception", "BaseException"):
                    broad = True
            elif last.startswith("assert_") or last.startswith("assert") and last != "assert":
                mock_checks += 1
        elif isinstance(node, ast.ExceptHandler):
            only_pass = all(isinstance(s, (ast.Pass, ast.Continue)) or
                            (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))
                            for s in node.body)
            if only_pass:
                swallow = True
    return {"asserts": asserts, "raises": raises, "mock_checks": mock_checks,
            "broad": broad, "swallow": swallow}


def static_scan(root: Path) -> list[dict]:
    found: list[dict] = []
    files = [root] if root.is_file() else sorted(root.rglob("*.py"))
    for path in files:
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        module_reqs: list[str] = []
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(_dotted(t) == "pytestmark" for t in node.targets):
                vals = node.value.elts if isinstance(node.value, (ast.List, ast.Tuple)) else [node.value]
                for v in vals:
                    module_reqs.extend(_req_args(v))

        def visit(body, prefix, inherited):
            for node in body:
                if isinstance(node, ast.ClassDef):
                    creqs, _ = _marks(node.decorator_list)
                    visit(node.body, prefix + node.name + "::", inherited + creqs)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    reqs, other = _marks(node.decorator_list)
                    reqs = sorted(set(reqs + inherited))
                    if not reqs:
                        continue
                    start = min([d.lineno for d in node.decorator_list] + [node.lineno])
                    rec = {"file": os.path.realpath(str(path)), "name": node.name,
                           "qual": prefix + node.name, "start": start, "end": node.end_lineno,
                           "reqs": reqs, "marks": other}
                    rec.update(_features(node))
                    found.append(rec)

        visit(tree.body, "", module_reqs)
    return found


def run_pytest(extra: list[str], only: str | None = None) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "reqprobe.json"
        env = dict(os.environ)
        env["PYTHONPATH"] = str(HERE) + os.pathsep + env.get("PYTHONPATH", "")
        env["REQPROBE_OUT"] = str(out)
        env["PYTHONPYCACHEPREFIX"] = str(Path(tmp) / "pyc")
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        if only:
            env["REQPROBE_ONLY"] = only
        cmd = [sys.executable, "-m", "pytest", "-p", "reqprobe", "-p", "no:cacheprovider",
               "-o", "enable_assertion_pass_hook=true", "-q", "--no-header", *extra]
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
        tail = [ln for ln in proc.stdout.strip().splitlines() if ln.strip()][-1:] or ["(no output)"]
        if not out.exists():
            print(proc.stdout[-2000:])
            print(proc.stderr[-2000:], file=sys.stderr)
            sys.exit(f"pytest did not finish (exit {proc.returncode}); no result file")
        data = json.loads(out.read_text(encoding="utf-8"))
        data["summary"] = tail[0]
        return data


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spec", help="spec file with rows that begin '| REQ-'")
    ap.add_argument("--tests", default=None, help="folder or file to scan for tags (default: tests, else .)")
    argv = sys.argv[1:]
    extra = []
    if "--" in argv:
        cut = argv.index("--")
        argv, extra = argv[:cut], argv[cut + 1:]
    args = ap.parse_args(argv)
    root = Path(args.tests) if args.tests else (Path("tests") if Path("tests").is_dir() else Path("."))
    spec = spec_rows(Path(args.spec)) if args.spec else {}

    static = static_scan(root)
    data = run_pytest(extra or [str(root)])
    items = data["items"]

    for fn in static:
        fn["items"] = [it for it in items if it["file"] == fn["file"] and it["name"] == fn["name"]
                       and fn["start"] <= it["line"] <= fn["end"]]

    ids = sorted(set(spec) | {r for fn in static for r in fn["reqs"]} | {r for it in items for r in it["reqs"]})
    print(f"pytest: {data['summary']}")
    print(f"{'requirement':<10} {'level':<9} {'tagged':>6} {'ran':>4} {'pass':>4} {'skip':>4} {'xfail':>5} {'fail':>4} {'asserts':>7}  flags")
    bad_must = 0
    must_total = must_proven = 0
    for rid in ids:
        level = spec.get(rid, "?" if spec else "-")
        fns = [fn for fn in static if rid in fn["reqs"]]
        ran = [it for it in items if rid in it["reqs"]]
        count = lambda o: sum(1 for it in ran if it["outcome"] in o)
        flags: list[str] = []
        notes: list[str] = []
        if spec and rid not in spec:
            flags.append("UNKNOWN-ID")
        if not fns and not ran:
            flags.append("NO-TEST")
        for fn in fns:
            where = f"{os.path.relpath(fn['file'])}::{fn['qual']} (line {fn['start']})"
            if not fn["items"]:
                flags.append("NOT-COLLECTED")
                notes.append(f"never ran: {where}")
                continue
            passed = [it for it in fn["items"] if it["outcome"] == "passed"]
            if passed and sum(it["asserts_passed"] for it in passed) == 0 \
                    and not fn["raises"] and not fn["mock_checks"]:
                flags.append("ZERO-ASSERT")
                notes.append(f"passed with 0 asserts executed ({fn['asserts']} written): {where}")
            if fn["broad"]:
                flags.append("BROAD-RAISES")
                notes.append(f"accepts any exception: {where}")
            if fn["swallow"]:
                flags.append("SWALLOWS")
                notes.append(f"except block hides failures: {where}")
        for outcome, flag in (("skipped", "SKIPPED"), ("xfailed", "XFAIL"), ("xpassed", "XPASS"),
                              ("failed", "FAILED"), ("error", "ERROR")):
            hit = [it for it in ran if it["outcome"] == outcome]
            if hit:
                flags.append(flag)
                for it in hit:
                    notes.append(f"{outcome}: {it['nodeid']}" + (f" ({it['reason']})" if it["reason"] else ""))
        if (fns or ran) and count({"passed"}) == 0:
            flags.append("NO-PASSING-TEST")
        flags = list(dict.fromkeys(flags))
        is_must = level.startswith("MUST") or not spec
        if is_must:
            must_total += 1
            if flags:
                bad_must += 1
            else:
                must_proven += 1
        asserts = sum(it["asserts_passed"] for it in ran)
        print(f"{rid:<10} {level:<9} {len(fns):>6} {len(ran):>4} {count({'passed'}):>4} {count({'skipped'}):>4} "
              f"{count({'xfailed', 'xpassed'}):>5} {count({'failed', 'error'}):>4} {asserts:>7}  {' '.join(flags) or '-'}")
        for note in notes:
            print(f"    {note}")
    untagged_skips = [it for it in items if not it["reqs"] and it["outcome"] in ("skipped", "xfailed", "xpassed")]
    for it in untagged_skips:
        print(f"untagged {it['outcome']}: {it['nodeid']}" + (f" ({it['reason']})" if it["reason"] else ""))
    label = "MUST and MUST NOT" if spec else "requirement ids (no spec given, all treated as MUST)"
    print(f"{label}: {must_total}; clean: {must_proven}; flagged: {bad_must}")
    return 1 if bad_must else 0


if __name__ == "__main__":
    sys.exit(main())
