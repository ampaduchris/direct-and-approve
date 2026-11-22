#!/usr/bin/env python3
"""Show every requirement row that changed after the spec was adopted.

A requirement that was reworded to fit the code looks fine at HEAD. It only
shows in the history. This tool compares the rows that begin `| REQ-` between
two versions of the spec and says whether each change is recorded as a deviation.

  Git mode, from the repo root (walks every commit that touched the spec):
    spec_diff.py --base <commit where the spec was adopted> [--head HEAD]
                 [--spec docs/spec.md] [--deviations docs/DEVIATIONS.md]
  File mode:
    spec_diff.py --then OLD.md --now NEW.md [--deviations FILE]

To find the base, list the merges that touched the spec and take the spec session's:
    git log --first-parent --date=short --format='%h %ad %s' -- docs/spec.md

Flags:
  LEVEL-DOWN     MUST or MUST NOT became SHOULD or MAY
  LEVEL-CHANGED  any other change of level
  TEXT-CHANGED   the requirement text changed
  PROOF-CHANGED  the test column changed
  REMOVED        the row is gone (ids are never removed; a withdrawn row stays)
  WITHDRAWN      the row now says withdrawn
  WITH-CODE      git mode: the same commit also changed files outside docs/
  NO-DEVIATION   the id does not appear in the deviations file (or in its Deviations section, if it has one)

Exit code 1 if any changed row has NO-DEVIATION. ADDED rows are listed, not flagged.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


def rows(text: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for line in text.splitlines():
        if line.lstrip().startswith("| REQ-"):
            cells = [" ".join(c.split()) for c in line.strip().strip("|").split("|")]
            if len(cells) >= 2:
                out[cells[0]] = cells[1:]
    return out


def deviations_section(text: str) -> str:
    """The text under the first heading that begins "Deviations", or the whole text if there is none."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^(#{1,6})\s*deviations\b", line.strip(), re.I)
        if m:
            level = len(m.group(1))
            out = []
            for nxt in lines[i + 1:]:
                h = re.match(r"^(#{1,6})\s", nxt)
                if h and len(h.group(1)) <= level:
                    break
                out.append(nxt)
            return "\n".join(out)
    return text


def git(*args: str) -> str:
    proc = subprocess.run(["git", *args], capture_output=True, text=True)
    if proc.returncode != 0:
        return ""
    return proc.stdout


def compare(old: dict[str, list[str]], new: dict[str, list[str]]) -> list[tuple[str, list[str], str, str]]:
    changes = []
    for rid in sorted(set(old) | set(new)):
        a, b = old.get(rid), new.get(rid)
        if a == b:
            continue
        if a is None:
            changes.append((rid, ["ADDED"], "", " | ".join(b)))
            continue
        if b is None:
            changes.append((rid, ["REMOVED"], " | ".join(a), ""))
            continue
        flags = []
        strong = lambda lvl: lvl.startswith("MUST")
        if a[0] != b[0]:
            flags.append("LEVEL-DOWN" if strong(a[0]) and not strong(b[0]) else "LEVEL-CHANGED")
        text_a, text_b = (a[1] if len(a) > 1 else ""), (b[1] if len(b) > 1 else "")
        if text_a != text_b:
            flags.append("WITHDRAWN" if "withdrawn" in text_b.lower() and "withdrawn" not in text_a.lower()
                         else "TEXT-CHANGED")
        if a[2:] != b[2:]:
            flags.append("PROOF-CHANGED")
        changes.append((rid, flags, " | ".join(a), " | ".join(b)))
    return changes


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--spec", default="docs/spec.md")
    ap.add_argument("--then")
    ap.add_argument("--now")
    ap.add_argument("--deviations")
    args = ap.parse_args()

    steps: list[tuple[str, list[str], list]] = []
    if args.then and args.now:
        changes = compare(rows(Path(args.then).read_text(encoding="utf-8")),
                          rows(Path(args.now).read_text(encoding="utf-8")))
        steps.append((f"{args.then} -> {args.now}", [], changes))
        dev_path = Path(args.deviations) if args.deviations else None
        dev_text = dev_path.read_text(encoding="utf-8") if dev_path and dev_path.exists() else ""
    elif args.base:
        if not git("rev-parse", "--verify", args.base + "^{commit}"):
            sys.exit(f"not a commit: {args.base}")
        commits = git("rev-list", "--reverse", f"{args.base}..{args.head}", "--", args.spec).split()
        for c in commits:
            old = rows(git("show", f"{c}^:{args.spec}"))
            new = rows(git("show", f"{c}:{args.spec}"))
            changes = compare(old, new)
            if not changes:
                continue
            subject = git("show", "-s", "--format=%h %ad %s", "--date=short", c).strip()
            others = [p for p in git("show", "--name-only", "--format=", c).split("\n")
                      if p and not p.startswith("docs/")]
            steps.append((subject, others, changes))
        dev_file = args.deviations or "docs/DEVIATIONS.md"
        dev_text = git("show", f"{args.head}:{dev_file}")
    else:
        ap.error("give --base (git mode) or --then and --now (file mode)")

    dev_text = deviations_section(dev_text)
    flagged = unlogged = 0
    for title, others, changes in steps:
        print(f"== {title}")
        if others:
            print(f"   same commit also changed {len(others)} file(s) outside docs/: {', '.join(others[:5])}"
                  + (" ..." if len(others) > 5 else ""))
        for rid, flags, old, new in changes:
            if flags == ["ADDED"]:
                print(f"{rid}  ADDED")
                print(f"   + {new}")
                continue
            flagged += 1
            flags = list(flags)
            if others:
                flags.append("WITH-CODE")
            if rid not in dev_text:
                flags.append("NO-DEVIATION")
                unlogged += 1
            print(f"{rid}  {' '.join(flags)}")
            print(f"   - {old}")
            if new:
                print(f"   + {new}")
    print(f"requirement rows changed after adoption: {flagged}; without a deviation entry: {unlogged}")
    return 1 if unlogged else 0


if __name__ == "__main__":
    sys.exit(main())
