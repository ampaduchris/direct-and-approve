#!/usr/bin/env python3
"""Check the session format of a control folder (spec section 8).

  python3 scripts/check_sessions.py <control-folder>

A session line is `- [<mark>] **<id> <title>** · [switch to ]<model> / <effort>`. The mark is a
space, p, x or ~. Every problem is printed as `path:line: message`. Exit 0 if there is none, 1 if
there is at least one, 2 on a usage error. Standard library only.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

EFFORTS = ("low", "medium", "high", "xhigh", "max")
MARKS = (" ", "p", "x", "~")
MODEL = re.compile(r"\b(?:Sonnet|Opus|Haiku|Fable)\s+\d+(?:\.\d+)?\b")
SESSION = re.compile(r"^- \[(?P<mark>[^\]]*)\] \*\*(?P<id>\S+) (?P<title>.+?)\*\*(?P<rest>.*)$")
PR_LINK = re.compile(r"https://github\.com/[^\s)]+/pull/\d+")
EXIT_TEST = re.compile(r"^\s+[-*]\s+Exit test\b")
NOTE = re.compile(r"^\s+[-*]\s+Note\b")


def cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def check_sessions_file(path: Path, shown: str, problems: list[str]) -> int:
    """Check one SESSIONS.md; return the number of session lines read."""
    lines = path.read_text(encoding="utf-8").split("\n")
    starts = [i for i, l in enumerate(lines) if l.startswith("- [")]
    seen: dict[str, int] = {}
    first_unstarted: tuple[str, int] | None = None

    def bad(n: int, msg: str) -> None:
        problems.append(f"{shown}:{n}: {msg}")

    for k, i in enumerate(starts):
        end = starts[k + 1] if k + 1 < len(starts) else len(lines)
        block = []
        for j in range(i + 1, end):
            if lines[j] and not lines[j][0].isspace():
                break
            block.append(lines[j])
        m = SESSION.match(lines[i])
        if not m:
            bad(i + 1, "malformed session line: expected `- [ ] **<id> <title>** · <model> / <effort>`")
            continue
        sid, mark, rest = m["id"], m["mark"], m["rest"]
        if mark not in MARKS:
            bad(i + 1, f"session {sid}: mark [{mark}] is not one of [ ], [p], [x], [~]")
        if sid in seen:
            bad(i + 1, f"duplicate session id {sid} (first at line {seen[sid]})")
        seen.setdefault(sid, i + 1)
        models = MODEL.findall(rest)
        if not models:
            bad(i + 1, f"session {sid}: no model")
        elif len(models) > 1:
            bad(i + 1, f"session {sid}: more than one model")
        else:
            e = re.search(MODEL.pattern + r"\s*/\s*(\S+)", rest)
            if not e:
                bad(i + 1, f"session {sid}: no effort after the model")
            else:
                word = re.sub(r"[^A-Za-z]+$", "", e.group(1))
                if word not in EFFORTS:
                    bad(i + 1, f"session {sid}: effort '{word}' is not one of {', '.join(EFFORTS)}")
        if not any(EXIT_TEST.match(b) for b in block):
            bad(i + 1, f"session {sid}: no bullet that begins 'Exit test'")
        if mark == "p" and not PR_LINK.search(lines[i] + "\n" + "\n".join(block)):
            bad(i + 1, f"session {sid}: marked [p] with no pull request link")
        if mark == "~" and not any(NOTE.match(b) for b in block):
            bad(i + 1, f"session {sid}: marked [~] with no note (a bullet that begins 'Note')")
        if mark == " " and first_unstarted is None:
            first_unstarted = (sid, i + 1)
        elif mark in ("p", "x") and first_unstarted is not None:
            bad(i + 1, f"session {sid} is [{mark}] but an earlier session ({first_unstarted[0]}, line {first_unstarted[1]}) is [ ]")
    return len(starts)


def check_plan(plan: Path, root: Path, problems: list[str]) -> list[Path]:
    """Check PLAN.md; return the SESSIONS.md files its rows name."""
    lines = plan.read_text(encoding="utf-8").split("\n")
    head = next((i for i, l in enumerate(lines) if re.match(r"^#+\s.*phases", l, re.I)), -1)
    start = next((i for i in range(head + 1, len(lines)) if lines[i].startswith("|")), None)
    if start is None:
        problems.append("PLAN.md:1: no phases table")
        return []
    header = cells(lines[start])
    missing = [c for c in ("Status", "Folder") if c not in header]
    for c in missing:
        problems.append(f"PLAN.md:{start + 1}: the phases table has no '{c}' column")
    if missing:
        return []
    si, fi = header.index("Status"), header.index("Folder")
    current, named = [], []
    for n in range(start + 2, len(lines)):
        if not lines[n].startswith("|"):
            break
        row = cells(lines[n])
        if set(lines[n]) <= set("|-: "):
            continue
        if len(row) <= max(si, fi):
            problems.append(f"PLAN.md:{n + 1}: row has fewer cells than the header")
            continue
        if row[si].strip("`* ").startswith("CURRENT"):
            current.append(n + 1)
        folder = re.sub(r"^builds/", "", row[fi].strip("`* ")).rstrip("/")
        target = root / "builds" / folder / "SESSIONS.md"
        if not folder or not target.is_file():
            problems.append(f"PLAN.md:{n + 1}: folder builds/{folder} has no SESSIONS.md")
        else:
            named.append(target)
    if len(current) > 1:
        problems.append(f"PLAN.md:{current[1]}: more than one phase is CURRENT (lines {', '.join(map(str, current))})")
    return named


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: check_sessions.py <control-folder>", file=sys.stderr)
        return 2
    root = Path(argv[0])
    plan = root / "PLAN.md"
    if not root.is_dir() or not plan.is_file():
        print(f"check_sessions: {argv[0]} is not a control folder (no PLAN.md)", file=sys.stderr)
        return 2
    problems: list[str] = []
    named = check_plan(plan, root, problems)
    files = sorted({*named, *root.glob("builds/*/SESSIONS.md")})
    sessions = 0
    for f in files:
        sessions += check_sessions_file(f, f.relative_to(root).as_posix(), problems)
    for p in problems:
        print(p)
    if problems:
        print(f"check_sessions: {len(problems)} problem(s)")
        return 1
    print(f"check_sessions: OK. files read: {len(files) + 1}, sessions read: {sessions}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
