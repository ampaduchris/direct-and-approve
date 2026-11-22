#!/usr/bin/env python3
"""Run the fenced blocks marked `bash run` in documents (spec REQ-107).

  python3 scripts/run_blocks.py [FILE ...]

With no file, reads README.md and every .md under docs/. Each block whose info string is exactly
`bash run` runs under `bash -e` from the repository root and must exit 0. A block tagged `bash`
only is never run: it needs the network or the owner's login. Prints one line per block. Exit 1 if
any block fails, 0 otherwise. Standard library only.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FENCE = re.compile(r"^```(?P<info>[^\n`]*)\n(?P<body>.*?)^```[ \t]*$", re.S | re.M)


def blocks(path: Path) -> list[tuple[int, str]]:
    text = path.read_text(encoding="utf-8")
    found = []
    for m in FENCE.finditer(text):
        if m.group("info").strip() == "bash run":
            found.append((text.count("\n", 0, m.start()) + 1, m.group("body")))
    return found


def main(argv: list[str]) -> int:
    files = [Path(a) for a in argv] or [ROOT / "README.md", *sorted((ROOT / "docs").rglob("*.md"))]
    failed = total = 0
    for path in files:
        for line, body in blocks(path):
            total += 1
            done = subprocess.run(["bash", "-e", "-o", "pipefail", "-c", body], cwd=ROOT, capture_output=True, text=True, timeout=600)
            ok = done.returncode == 0
            failed += not ok
            tail = (done.stdout.strip().splitlines() or done.stderr.strip().splitlines() or [""])[-1][:100]
            print(f"{'ok  ' if ok else 'FAIL'} {path.name}:{line}: {body.strip().splitlines()[0][:60]} -> exit {done.returncode}: {tail}")
            if not ok:
                sys.stdout.write(done.stdout[-1500:] + done.stderr[-1500:])
    print(f"run_blocks: {total} block(s), {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
