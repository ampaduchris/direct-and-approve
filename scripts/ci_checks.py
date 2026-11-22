#!/usr/bin/env python3
"""The three CI checks that copy files about (spec REQ-074, 081, 082, 106).

  python3 scripts/ci_checks.py kit             calibration proof in place; no example changed
  python3 scripts/ci_checks.py scrub           scrubber self-test and example-list scan of the tree
  python3 scripts/ci_checks.py start-your-own  copy method/ outside the repository and run its checks

Each prints one line per step and exits 0 only if every step passed. Standard library only. The
kit step needs pytest on the path, because the calibration examples are pytest suites.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
METHOD = ROOT / "method"
SKIP = {".git", ".venv", ".pytest_cache", ".hypothesis", "__pycache__", "mutants", "dist"}
# The tests and the two example lists plant invented names on purpose (spec section 16.2, FX-6).
# They are the only paths the example-list scan leaves out, so that the scan can print CLEAN on
# everything else. DEV-012.
SCAN_SKIP = ("tests", "method/private/denylist.example.txt", "static/private/denylist.example.txt")
# prove.py writes its transcript here, with timings, so the file differs on every run. DEV-011.
PROOF_TRANSCRIPT = "method/calibration/_answers/PROOF.txt"


def step(label: str, cmd: list[str], *, cwd: Path, env: dict | None = None) -> bool:
    done = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=600)
    tail = (done.stdout.strip().splitlines() or done.stderr.strip().splitlines() or [""])[-1]
    print(f"{'ok  ' if done.returncode == 0 else 'FAIL'} {label}: {tail}")
    if done.returncode:
        sys.stdout.write(done.stdout[-3000:] + done.stderr[-3000:])
    return done.returncode == 0


def kit() -> int:
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTEST_ADDOPTS": "-p no:cacheprovider"}
    ok = step("calibration proof", [sys.executable, str(METHOD / "calibration/_answers/prove.py")], cwd=ROOT, env=env)
    spec = ["--", "method/calibration", f":(exclude){PROOF_TRANSCRIPT}"]
    changed = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all", *spec],
                             cwd=ROOT, capture_output=True, text=True).stdout.strip()
    print(f"{'ok  ' if not changed else 'FAIL'} no example file changed by the run: {changed or 'git status is empty'}")
    return 0 if ok and not changed else 1


def tree_copy(src: Path, dest: Path, skip: tuple[str, ...]) -> None:
    for path in sorted(src.rglob("*")):
        rel = path.relative_to(src)
        if any(part in SKIP for part in rel.parts) or any(rel.as_posix() == s or rel.as_posix().startswith(s + "/") for s in skip):
            continue
        if path.is_symlink() or not path.is_file():
            continue
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest / rel)


def with_example_list(base: Path) -> Path:
    method = base / "method"
    shutil.copytree(METHOD, method, symlinks=False)
    shutil.copy(method / "private/denylist.example.txt", method / "private/denylist.txt")
    return method


def scrub() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        method = with_example_list(base)
        tree = base / "tree"
        tree.mkdir()
        tree_copy(ROOT, tree, SCAN_SKIP)
        scrubber = method / "tools/scrub.py"
        a = step("scrubber self-test", [sys.executable, str(scrubber), "--self-test"], cwd=method)
        b = step("example-list scan of the tree", [sys.executable, str(scrubber), str(tree)], cwd=method)
    return 0 if a and b else 1


def start_your_own() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        method = with_example_list(Path(tmp))
        results = [
            step("check_sessions on the copy", [sys.executable, str(ROOT / "scripts/check_sessions.py"), str(method)], cwd=method),
            step("scrubber self-test on the copy", [sys.executable, str(method / "tools/scrub.py"), "--self-test"], cwd=method),
            step("calibration proof on the copy", [sys.executable, str(method / "calibration/_answers/prove.py")], cwd=method,
                 env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}),
        ]
    return 0 if all(results) else 1


def main(argv: list[str]) -> int:
    commands = {"kit": kit, "scrub": scrub, "start-your-own": start_your_own}
    if len(argv) != 1 or argv[0] not in commands:
        print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
        return 2
    return commands[argv[0]]()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
