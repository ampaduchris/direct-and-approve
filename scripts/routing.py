#!/usr/bin/env python3
"""Count sessions by model and effort from a BUILD-LOG (spec section 12).

  python3 scripts/routing.py <BUILD-LOG.md> [--json]

Reads the table of the standard: date, session id, model, effort and its source, minutes, tiers
passed, NOT VERIFIED count, pull request link. Prints sessions by model and effort, total minutes,
total NOT VERIFIED and the number of rows whose effort was not machine-verified. Every figure
carries the number of sessions it was computed from. A malformed row exits 1 naming the line, and
no total is printed. Standard library only.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

COLUMNS = 8
MODEL = re.compile(r"^(?:Sonnet|Opus|Haiku|Fable)\s+\d+(?:\.\d+)?")
EFFORT = re.compile(r"^(low|medium|high|xhigh|max)\b")
NUMBER = re.compile(r"^~?\s*(\d+)\b")


def cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse(path: Path) -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    errors: list[str] = []
    seen: set[str] = set()
    in_table = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.startswith("|"):
            in_table = False
            continue
        parts = cells(line)
        if parts and parts[0] == "Date":
            in_table = True
            continue
        if not in_table or set(line.replace("|", "").strip()) <= {"-", " ", ":"}:
            continue
        where = f"{path.name}:{number}"
        if len(parts) != COLUMNS:
            errors.append(f"{where}: {len(parts)} columns, expected {COLUMNS}")
            continue
        date, session, model, effort, minutes, _tiers, not_verified, _pr = parts
        if session in seen:
            errors.append(f"{where}: duplicate session id {session}")
            continue
        seen.add(session)
        m = MODEL.match(model)
        e = EFFORT.match(effort)
        mins = NUMBER.match(minutes)
        count = re.fullmatch(r"\d+", not_verified)
        if not m:
            errors.append(f"{where}: model not recognised: {model!r}")
        if not e:
            errors.append(f"{where}: effort not recognised: {effort!r}")
        if not mins:
            errors.append(f"{where}: minutes is not a number: {minutes!r}")
        if not count:
            errors.append(f"{where}: NOT VERIFIED count is not a number: {not_verified!r}")
        if m and e and mins and count:
            rows.append({
                "session": session, "date": date, "model": m.group(0), "effort": e.group(1),
                "minutes": int(mins.group(1)), "not_verified": int(count.group(0)),
                "machine_verified": "not machine-verified" not in effort,
            })
    if not rows and not errors:
        errors.append(f"{path.name}: no BUILD-LOG table found")
    return rows, errors


def summarise(rows: list[dict]) -> dict:
    n = len(rows)
    by = Counter((r["model"], r["effort"]) for r in rows)
    return {
        "sessions": n,
        "by_model_effort": [
            {"model": m, "effort": e, "sessions": c} for (m, e), c in sorted(by.items())
        ],
        "total_minutes": sum(r["minutes"] for r in rows),
        "total_not_verified": sum(r["not_verified"] for r in rows),
        "effort_not_machine_verified": sum(1 for r in rows if not r["machine_verified"]),
    }


def render(s: dict) -> str:
    n = s["sessions"]
    lines = [f"Sessions by model and effort ({n} sessions)"]
    lines += [f"  {r['model']} / {r['effort']}: {r['sessions']}" for r in s["by_model_effort"]]
    lines += [
        f"total minutes: {s['total_minutes']} ({n} sessions)",
        f"total NOT VERIFIED: {s['total_not_verified']} ({n} sessions)",
        f"effort not machine-verified: {s['effort_not_machine_verified']} ({n} sessions)",
    ]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    args = [a for a in argv if a != "--json"]
    if len(args) != 1 or not Path(args[0]).is_file():
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 2
    rows, errors = parse(Path(args[0]))
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    summary = summarise(rows)
    print(json.dumps(summary, indent=2) if "--json" in argv else render(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
