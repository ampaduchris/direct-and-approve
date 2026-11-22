#!/usr/bin/env python3
"""Prove that every planted defect is exposed by its command, and that the control is clean.

Runs the five kit scripts on all eleven examples and compares exit codes and
key output with EXPECT below. Prints one line per run and writes the full
output to PROOF.txt in the system temporary folder.

  uv run --with pytest python calibration/_answers/prove.py

Exit code 0 only if every run matches. Reviewers: do not open this file before
your calibration findings are written. It names every planted defect.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXAMPLES = HERE.parent
KIT = HERE.parents[1] / ".claude" / "skills" / "independent-review" / "scripts"
PY = sys.executable

# example -> (module, function, requirement ids for the probe or None)
TARGET = {
    "ex01": ("redact", "redact", "REQ-001,REQ-002"),
    "ex02": ("days", "parse_day", "REQ-002"),
    "ex03": ("vat", "gross_cents", "REQ-001"),
    "ex04": ("cards", "mask_card", None),
    "ex05": ("cents", "to_cents", "REQ-001"),
    "ex06": ("notes", "shorten", "REQ-001"),
    "ex07": ("digits", "hide_digits", "REQ-001"),
    "ex08": ("luhn", "luhn_ok", "REQ-001"),
    "ex09": ("settings", "load_settings", "REQ-001"),
    "ex10": ("stats", "median", "REQ-002"),
    "ex11": ("quantity", "parse_quantity", "REQ-002"),
}

# A fresh input, one that appears in no test, for the examples where the misleading test hides a fault.
FRESH = {
    "ex02": ('from days import parse_day; print(parse_day("2026-02-30"))', "(2026, 2, 30)"),
    "ex05": ('from cents import to_cents; print(to_cents("12.5"))', "1205"),
    "ex07": ('from digits import hide_digits; print(hide_digits("Card 4111 1111 1111 111"))', "Card #### #### #### 111"),
    "ex08": ('from luhn import luhn_ok; print(luhn_ok("4111111111111111"))', "False"),
    "ex11": ('from quantity import parse_quantity; print(parse_quantity("-3"))', "-3"),
}

# (example, tool) -> (exit code, [text that must appear in the output])
# Anything not listed must exit 0: the tool has nothing to say about that example.
EXPECT = {
    # ex01 weak assertions: only the flip probe shows it.
    ("ex01", "mutate"): (1, ["gut     killed", "raise   killed", "flip    SURVIVED"]),
    # ex02 expected-to-fail test on a MUST.
    ("ex02", "req_run"): (1, ["REQ-002", "XFAIL", "NO-PASSING-TEST"]),
    ("ex02", "mutate"): (1, ["gut     SURVIVED", "raise   SURVIVED", "flip    SURVIVED"]),
    # ex03 the test patches the function under test.
    ("ex03", "mutate"): (1, ["gut     SURVIVED", "raise   SURVIVED", "flip    SURVIVED"]),
    # ex04 control: every tool exits 0 (checked by the default rule).
    # ex05 a second function of the same name replaces the tagged test.
    ("ex05", "req_run"): (1, ["REQ-001", "NOT-COLLECTED", "never ran: test_cents.py::test_to_cents (line 6)"]),
    ("ex05", "mutate"): (2, ["NO TESTS SELECTED"]),
    # ex06 the requirement was reworded after adoption; nothing else shows it.
    ("ex06", "spec_diff"): (1, ["REQ-001  TEXT-CHANGED NO-DEVIATION", "never inside a word"]),
    # ex07 the fixture yields nothing, so the loop body never runs.
    ("ex07", "req_run"): (1, ["REQ-001", "ZERO-ASSERT", "passed with 0 asserts executed (1 written)"]),
    ("ex07", "mutate"): (1, ["gut     SURVIVED", "raise   SURVIVED"]),
    # ex08 the code answers the test inputs from a table; mutation probes are all killed.
    ("ex08", "overlap"): (1, ["OVERLAP", "79927398713", "4539578763621486"]),
    # ex09 a comparison with no assert.
    ("ex09", "req_run"): (1, ["REQ-001", "ZERO-ASSERT", "passed with 0 asserts executed (0 written)"]),
    ("ex09", "mutate"): (1, ["gut     SURVIVED", "raise   killed"]),
    # ex10 the body says 3 passed; the suite has a failure.
    ("ex10", "tier"): (1, ["RERUN-FAILED", "EVIDENCE-MISMATCH(claimed 3 passed, now 2)"]),
    ("ex10", "req_run"): (1, ["REQ-002", "FAILED"]),
    ("ex10", "mutate"): (2, ["baseline is not green"]),
    # ex11 any exception satisfies the test.
    ("ex11", "req_run"): (1, ["REQ-002", "BROAD-RAISES"]),
    ("ex11", "mutate"): (1, ["gut     killed", "raise   SURVIVED"]),
}


def commands(ex: str) -> dict[str, list[str]]:
    module, func, req = TARGET[ex]
    mutate = [PY, str(KIT / "mutate_check.py"), f"{module}.py:{func}"] + (["--req", req] if req else [])
    return {
        "req_run": [PY, str(KIT / "req_run.py"), "--spec", "spec.md", "--tests", "."],
        "mutate": mutate,
        "spec_diff": [PY, str(KIT / "spec_diff.py"), "--then", "spec.adopted.md", "--now", "spec.md",
                      "--deviations", "PR-BODY.md"],
        "tier": [PY, str(KIT / "tier_check.py"), "PR-BODY.md", "--rerun", "--offline"],
        "overlap": [PY, str(KIT / "literal_overlap.py"), "--src", ".", "--tests", f"test_{module}.py"],
    }


def main() -> int:
    log: list[str] = []
    bad = 0
    for ex in sorted(TARGET):
        cwd = EXAMPLES / ex
        before = {p.name: p.read_bytes() for p in cwd.iterdir() if p.is_file()}
        for tool, cmd in commands(ex).items():
            proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env={**__import__("os").environ, "PYTEST_ADDOPTS": "-p no:cacheprovider", "PYTHONDONTWRITEBYTECODE": "1"})
            out = proc.stdout + proc.stderr
            want_code, want_text = EXPECT.get((ex, tool), (0, []))
            missing = [t for t in want_text if t not in out]
            ok = proc.returncode == want_code and not missing
            bad += not ok
            print(f"{'ok  ' if ok else 'FAIL'} {ex} {tool:<9} exit {proc.returncode} (expected {want_code})"
                  + (f" missing: {missing}" if missing else ""))
            shown = " ".join(c.replace(str(KIT) + "/", "").replace(PY, "python") for c in cmd)
            log.append(f"$ cd {ex} && {shown}\n{out.rstrip()}\n[exit {proc.returncode}]\n")
        if ex in FRESH:
            code, want = FRESH[ex]
            proc = subprocess.run([PY, "-c", code], cwd=cwd, capture_output=True, text=True, env={**__import__("os").environ, "PYTHONDONTWRITEBYTECODE": "1"})
            got = proc.stdout.strip()
            ok = got == want
            bad += not ok
            print(f"{'ok  ' if ok else 'FAIL'} {ex} fresh     prints {got!r} (expected {want!r})")
            log.append(f"$ cd {ex} && python -c '{code}'\n{got}\n")
        after = {p.name: p.read_bytes() for p in cwd.iterdir() if p.is_file()}
        if before != after:
            bad += 1
            print(f"FAIL {ex} files changed by the run")
    (Path(__import__("tempfile").gettempdir()) / "PROOF.txt").write_text("\n".join(log))
    print(f"{'ALL RUNS MATCH' if not bad else str(bad) + ' MISMATCH(ES)'}: "
          f"{len(TARGET)} examples, 5 tools each, plus {len(FRESH)} fresh-input probes")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
