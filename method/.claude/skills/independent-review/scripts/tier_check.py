#!/usr/bin/env python3
"""Check the tier table of a pull request body against what can be run or resolved.

A row marked PASS is a claim. This tool checks that the claim has evidence, that
the evidence is green, that it belongs to the commit under review, and, with
--rerun, that the command gives the same result again.

  tier_check.py BODY.md [--rerun] [--cwd DIR] [--head SHA] [--offline]
                        [--build-log docs/BUILD-LOG.md --session 1.4]
  tier_check.py --pr 12 [--repo owner/name] [--build-log ... --session ...]

Expected body layout (STANDARD.md, plus the "Not verified" list the pre-pr-check skill adds):
  a table with the columns Tier, Check run, Command, Result, Evidence and rows V1 to V6
  a heading "Not verified" followed by one list item per thing that was not verified
  V6 is PASS when that list exists and its count is right; its evidence cell gives the count

Errors (exit code 1):
  NO-TABLE MISSING-ROW DUPLICATE-ROW BLANK-CELL BAD-RESULT
  NO-EVIDENCE        PASS with an empty or placeholder evidence cell
  RED-EVIDENCE       the linked run did not succeed, or the pasted output shows a failure
  STALE-EVIDENCE     the linked run is for a different commit than the head
  PENDING-EVIDENCE   the linked run has not finished
  UNRESOLVED-LINK    the linked run could not be read
  RERUN-FAILED       --rerun: the command exits non-zero now
  EVIDENCE-MISMATCH  --rerun: the pasted pass count differs from the count now
  NV-LIST-MISSING    no "Not verified" list
  NV-COUNT-MISMATCH  the list is shorter than the NOT VERIFIED rows, or differs from the BUILD-LOG row
Warnings (exit code stays 0): PASS-WITH-SKIPS, LINK-NOT-CHECKED, NV-ZERO

--rerun runs the commands in the Command column. It is allowed only with a local
body file that this session wrote or read first, never with --pr.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

RUN_URL = re.compile(r"https://github\.com/([\w.-]+/[\w.-]+)/actions/runs/(\d+)")
ANY_URL = re.compile(r"https?://\S+")
RED = re.compile(r"\b[1-9]\d* (failed|errors?)\b|Traceback|\bFAILED\b|\bexit(?: code)? [1-9]|no tests ran", re.I)
SOFT = re.compile(r"\b[1-9]\d* (skipped|xfailed|xpassed)\b", re.I)
PASSED = re.compile(r"\b(\d+) passed\b")
PLACEHOLDER = {"", "-", "n/a", "na", "tbd", "todo", "pending", "see ci", "link"}


def sh(cmd: list[str]) -> tuple[int, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)
    return proc.returncode, proc.stdout.strip() or proc.stderr.strip()


def parse_table(body: str) -> list[dict]:
    lines = body.splitlines()
    for i, line in enumerate(lines):
        cells = [c.strip().lower() for c in line.strip().strip("|").split("|")]
        if line.strip().startswith("|") and "tier" in cells and "result" in cells:
            header = cells
            out = []
            for row in lines[i + 2:]:
                if not row.strip().startswith("|"):
                    break
                vals = [c.strip() for c in re.split(r"(?<!\\)\|", row.strip().strip("|"))]
                vals += [""] * (len(header) - len(vals))
                out.append(dict(zip(header, vals)))
            return out
    return []


def not_verified_items(body: str) -> list[str] | None:
    lines = body.splitlines()
    for i, line in enumerate(lines):
        if re.match(r"^#{1,6}\s*not verified\b", line.strip(), re.I):
            items = []
            for nxt in lines[i + 1:]:
                if re.match(r"^#{1,6}\s", nxt):
                    break
                if re.match(r"^\s*(?:[-*]|\d+\.)\s+\S", nxt):
                    items.append(nxt.strip())
            return items
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("body", nargs="?")
    ap.add_argument("--pr")
    ap.add_argument("--repo")
    ap.add_argument("--head")
    ap.add_argument("--rerun", action="store_true")
    ap.add_argument("--cwd", default=".")
    ap.add_argument("--offline", action="store_true", help="do not call gh")
    ap.add_argument("--build-log")
    ap.add_argument("--session")
    args = ap.parse_args()

    head = args.head
    if args.pr:
        if args.rerun:
            ap.error("--rerun needs a local body file; text fetched from the network is not executed")
        cmd = ["gh", "pr", "view", args.pr, "--json", "body,headRefOid"] + (["--repo", args.repo] if args.repo else [])
        code, out = sh(cmd)
        if code != 0:
            sys.exit(f"gh pr view failed: {out}")
        data = json.loads(out)
        body, head = data["body"], head or data["headRefOid"]
    elif args.body:
        body = Path(args.body).read_text(encoding="utf-8")
    else:
        ap.error("give a body file or --pr")
    if not head and not args.offline:
        code, out = sh(["git", "-C", args.cwd, "rev-parse", "HEAD"])
        head = out if code == 0 else None

    errors: list[str] = []
    warnings: list[str] = []
    table = parse_table(body)
    if not table:
        print("NO-TABLE: no table with Tier and Result columns")
        return 1

    seen: dict[str, int] = {}
    nv_rows = 0
    for row in table:
        tier = row.get("tier", "").upper()
        seen[tier] = seen.get(tier, 0) + 1
        result = row.get("result", "").upper().strip("* ")
        evidence = row.get("evidence", "")
        command = row.get("command", "")
        blanks = [k for k in ("check run", "command", "result", "evidence") if not row.get(k, "").strip()]
        notes: list[str] = []
        if blanks:
            notes.append("BLANK-CELL(" + ",".join(blanks) + ")")
        if result not in ("PASS", "FAIL", "NOT VERIFIED"):
            notes.append("BAD-RESULT")
        if result == "NOT VERIFIED" and tier != "V6":
            nv_rows += 1
        if result == "PASS":
            if evidence.strip("`* ").lower() in PLACEHOLDER:
                notes.append("NO-EVIDENCE")
            runs = RUN_URL.findall(evidence)
            for repo, run_id in runs:
                if args.offline:
                    warnings.append(f"{tier}: LINK-NOT-CHECKED run {run_id} (offline)")
                    continue
                code, out = sh(["gh", "run", "view", run_id, "--repo", repo, "--json", "conclusion,status,headSha"])
                if code != 0:
                    notes.append(f"UNRESOLVED-LINK(run {run_id})")
                    continue
                info = json.loads(out)
                if info.get("status") != "completed":
                    notes.append(f"PENDING-EVIDENCE(run {run_id} is {info.get('status')})")
                elif info.get("conclusion") != "success":
                    notes.append(f"RED-EVIDENCE(run {run_id} concluded {info.get('conclusion')})")
                if head and info.get("headSha") and info["headSha"] != head:
                    notes.append(f"STALE-EVIDENCE(run {run_id} is for {info['headSha'][:8]}, head is {head[:8]})")
            other_links = [u for u in ANY_URL.findall(evidence) if not RUN_URL.search(u)]
            for url in other_links:
                warnings.append(f"{tier}: LINK-NOT-CHECKED {url.rstrip(').,')}")
            if RED.search(evidence):
                notes.append("RED-EVIDENCE(pasted output shows a failure)")
            if SOFT.search(evidence):
                warnings.append(f"{tier}: PASS-WITH-SKIPS ({SOFT.search(evidence).group(0)}); name each one under Not verified")
            if args.rerun:
                whole = re.fullmatch(r"`([^`]+)`", command.strip())
                cmds = [whole.group(1)] if whole else []
                if not cmds:
                    print(f"   rerun {tier}: no single command in backticks, nothing rerun")
                for c in cmds:
                    proc = subprocess.run(c, shell=True, cwd=args.cwd, capture_output=True, text=True, timeout=900)
                    out_lines = [ln for ln in (proc.stdout + proc.stderr).strip().splitlines() if ln.strip()]
                    last = out_lines[-1].strip("= ") if out_lines else "(no output)"
                    print(f"   rerun {tier}: `{c}` -> exit {proc.returncode}: {last}")
                    if proc.returncode != 0:
                        notes.append("RERUN-FAILED")
                    claimed, now = PASSED.search(evidence), PASSED.search(last)
                    if claimed and now and claimed.group(1) != now.group(1):
                        notes.append(f"EVIDENCE-MISMATCH(claimed {claimed.group(1)} passed, now {now.group(1)})")
                    elif claimed and not now and proc.returncode == 0:
                        warnings.append(f"{tier}: pass count claimed but not found in rerun output")
        print(f"{tier:<3} {result:<12} {' '.join(dict.fromkeys(notes)) or 'ok'}")
        errors.extend(f"{tier}: {n}" for n in dict.fromkeys(notes))

    for tier in ("V1", "V2", "V3", "V4", "V5", "V6"):
        if seen.get(tier, 0) == 0:
            errors.append(f"{tier}: MISSING-ROW")
        elif seen[tier] > 1:
            errors.append(f"{tier}: DUPLICATE-ROW")

    items = not_verified_items(body)
    if items is None:
        errors.append('NV-LIST-MISSING: add a "Not verified" heading with one list item per gap, or "- None" with the reason')
        listed = None
    else:
        real = [it for it in items if not re.match(r"^\s*(?:[-*]|\d+\.)\s+none\b", it, re.I)]
        listed = len(real)
        print(f"Not verified: {listed} item(s) listed; {nv_rows} row(s) marked NOT VERIFIED")
        if listed < nv_rows:
            errors.append(f"NV-COUNT-MISMATCH: {nv_rows} rows are NOT VERIFIED but only {listed} item(s) are listed")
        if listed == 0:
            warnings.append("NV-ZERO: nothing listed as not verified; say what was out of reach, or why nothing was")

    if args.build_log and args.session:
        logged = None
        for line in Path(args.build_log).read_text(encoding="utf-8").splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if line.strip().startswith("|") and len(cells) >= 8 and cells[1] == args.session:
                m = re.search(r"\d+", cells[6])
                logged = int(m.group(0)) if m else None
        if logged is None:
            errors.append(f"NV-COUNT-MISMATCH: no BUILD-LOG row with a count for session {args.session}")
        elif listed is not None and logged != listed:
            errors.append(f"NV-COUNT-MISMATCH: BUILD-LOG says {logged}, the body lists {listed}")

    for w in warnings:
        print(f"warning  {w}")
    for e in errors:
        print(f"ERROR    {e}")
    print(f"tier table: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
