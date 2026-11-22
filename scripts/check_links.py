#!/usr/bin/env python3
"""Check relative links and anchors in documents, offline (spec REQ-099).

  python3 scripts/check_links.py [FILE ...]

With no file, reads README.md, CHANGELOG.md, CONTRIBUTING.md, SECURITY.md and every .md under docs/.
A relative link must name a file or folder that exists; a `#anchor` must match a heading of the
target file (GitHub's slug rule). Links that start with http, https or mailto are counted and not
fetched: external links are checked by hand at release and the output is pasted into the pull
request. Exit 1 if any link fails. Standard library only.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE = re.compile(r"^```.*?^```", re.S | re.M)


def slug(heading: str) -> str:
    s = re.sub(r"[`*_]", "", heading.strip().lower())
    s = re.sub(r"[^\w\- ]", "", s)
    return s.replace(" ", "-")


def anchors(path: Path) -> set[str]:
    text = FENCE.sub("", path.read_text(encoding="utf-8"))
    return {slug(m.group(1)) for m in re.finditer(r"^#{1,6}\s+(.+?)\s*#*$", text, re.M)}


def shown(path: Path) -> str:
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def check(path: Path) -> tuple[int, int, list[str]]:
    text = FENCE.sub("", path.read_text(encoding="utf-8"))
    external = checked = 0
    problems: list[str] = []
    for m in LINK.finditer(text):
        target = m.group(1)
        line = text.count("\n", 0, m.start()) + 1
        if re.match(r"(?:https?:|mailto:)", target):
            external += 1
            continue
        checked += 1
        name, _, frag = target.partition("#")
        dest = path if not name else (path.parent / name)
        if not dest.exists():
            problems.append(f"{shown(path)}:{line}: no such file: {target}")
        elif frag and dest.is_file() and dest.suffix == ".md" and slug(frag) not in anchors(dest):
            problems.append(f"{shown(path)}:{line}: no such heading: {target}")
    return checked, external, problems


def main(argv: list[str]) -> int:
    if argv:
        files = [Path(a).resolve() for a in argv]
    else:
        files = [ROOT / n for n in ("README.md", "CHANGELOG.md", "CONTRIBUTING.md", "SECURITY.md")] + sorted((ROOT / "docs").rglob("*.md"))
        files = [f for f in files if f.exists()]
    checked = external = 0
    problems: list[str] = []
    for f in files:
        c, e, p = check(f)
        checked += c
        external += e
        problems += p
    print("\n".join(problems))
    print(f"check_links: {len(files)} file(s), {checked} relative link(s) checked, {external} external link(s) not fetched, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
