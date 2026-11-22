#!/usr/bin/env python3
"""Print one part of a long Markdown file, so a session reads that part only.

  section.py FILE "6.8"            the section whose heading starts with 6.8 (any level), up to the next heading of the same or higher level
  section.py FILE "Limits"         the first section whose heading contains the text (case-insensitive)
  section.py FILE REQ-030..REQ-046 the requirement table rows in that range, with each row's table header
  section.py FILE --toc            the headings with line numbers

Exit 1 if nothing matched.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HEAD = re.compile(r"^(#{1,6})\s+(.*)$")


def headings(lines: list[str]) -> list[tuple[int, int, str]]:
    out, fence = [], False
    for i, l in enumerate(lines):
        if l.startswith("```"):
            fence = not fence
        m = None if fence else HEAD.match(l)
        if m:
            out.append((i, len(m.group(1)), m.group(2).strip()))
    return out


def section(lines: list[str], key: str) -> list[str]:
    hs = headings(lines)
    k = key.lower()
    hit = next((h for h in hs if re.match(rf"{re.escape(k)}(\b|\.|\s|$)", h[2].lower())), None)
    hit = hit or next((h for h in hs if k in h[2].lower()), None)
    if not hit:
        return []
    start, level, _ = hit
    end = next((i for i, lv, _ in hs if i > start and lv <= level), len(lines))
    return lines[start:end]


def req_rows(lines: list[str], lo: int, hi: int) -> list[str]:
    out, header = [], None
    for i, l in enumerate(lines):
        if l.startswith("|") and i + 1 < len(lines) and set(lines[i + 1].replace("|", "").strip()) <= set("-: ") and lines[i + 1].startswith("|"):
            header = [l, lines[i + 1]]
        m = re.match(r"^\|\s*REQ-(\d+)", l)
        if m and lo <= int(m.group(1)) <= hi:
            if header:
                out.extend(header)
                header = None
            out.append(l)
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 1
    lines = Path(argv[0]).read_text().splitlines()
    key = argv[1]
    if key == "--toc":
        for i, lv, t in headings(lines):
            print(f"{i + 1:5d} {'  ' * (lv - 1)}{t}")
        return 0
    m = re.fullmatch(r"REQ-(\d+)\.\.REQ-(\d+)", key)
    out = req_rows(lines, int(m.group(1)), int(m.group(2))) if m else section(lines, key)
    print("\n".join(out) if out else f"NO MATCH for {key!r} in {argv[0]}")
    return 0 if out else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
