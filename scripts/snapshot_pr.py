#!/usr/bin/env python3
"""Save a pull request's record to a JSON file (spec REQ-097). Run by hand; never in CI.

  python3 scripts/snapshot_pr.py <owner/repo> <number> [--out docs/data/worked-example.json]

Calls the GitHub command line (`gh api`) with the caller's own login, so it needs the network and
reads only. Saves the title, body, opened and merged times, the commits with their dates, every
comment and review, and the CI runs of the commits, with the fetch date. Email addresses are
replaced by <email>, so that the saved record passes the privacy boundary. The document that quotes the
record is compared with this file offline by a test. Standard library only.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def gh(path: str) -> object:
    done = subprocess.run(["gh", "api", "--paginate", path], capture_output=True, text=True, timeout=120)
    if done.returncode:
        raise SystemExit(f"gh api {path} failed: {done.stderr.strip()[:200]}")
    text = done.stdout.strip()
    # --paginate prints one JSON array per page; join them.
    if text.startswith("[") and "][" in text:
        text = text.replace("][", ",")
        return [x for page in json.loads("[" + text[1:-1] + "]") for x in (page if isinstance(page, list) else [page])]
    return json.loads(text or "null")


EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def redact(value):
    """Replace every email address in the saved record with <email>: the record is published (REQ-035)."""
    if isinstance(value, str):
        return EMAIL.sub("<email>", value)
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, dict):
        return {k: redact(v) for k, v in value.items()}
    return value


def minutes_between(a: str, b: str) -> float:
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    return round((datetime.strptime(b, fmt) - datetime.strptime(a, fmt)).total_seconds() / 60, 1)


def snapshot(repo: str, number: int) -> dict:
    pr = gh(f"repos/{repo}/pulls/{number}")
    commits = gh(f"repos/{repo}/pulls/{number}/commits")
    shas = {c["sha"] for c in commits}
    runs = gh(f"repos/{repo}/actions/runs?per_page=100")
    runs = runs["workflow_runs"] if isinstance(runs, dict) else runs
    return {
        "fetched_on": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "repo": repo,
        "number": number,
        "url": pr["html_url"],
        "title": pr["title"],
        "body": pr["body"],
        "opened_at": pr["created_at"],
        "merged_at": pr["merged_at"],
        "merge_commit": pr["merge_commit_sha"],
        "minutes_open_to_merge": minutes_between(pr["created_at"], pr["merged_at"]) if pr["merged_at"] else None,
        "author": pr["user"]["login"],
        "merged_by": (pr.get("merged_by") or {}).get("login"),
        "commits": [
            {"sha": c["sha"], "headline": c["commit"]["message"].splitlines()[0], "date": c["commit"]["committer"]["date"]}
            for c in commits
        ],
        "issue_comments": [
            {"author": c["user"]["login"], "created_at": c["created_at"], "url": c["html_url"], "body": c["body"]}
            for c in gh(f"repos/{repo}/issues/{number}/comments")
        ],
        "reviews": [
            {"author": r["user"]["login"], "state": r["state"], "submitted_at": r["submitted_at"], "body": r["body"]}
            for r in gh(f"repos/{repo}/pulls/{number}/reviews")
        ],
        "review_comments": [
            {"author": c["user"]["login"], "created_at": c["created_at"], "url": c["html_url"], "body": c["body"]}
            for c in gh(f"repos/{repo}/pulls/{number}/comments")
        ],
        "runs": [
            {"id": r["id"], "url": r["html_url"], "head_sha": r["head_sha"], "conclusion": r["conclusion"], "created_at": r["created_at"]}
            for r in runs
            if r["head_sha"] in shas
        ],
    }


def main(argv: list[str]) -> int:
    args = list(argv)
    out = Path("docs/data/worked-example.json")
    if "--out" in args:
        i = args.index("--out")
        out = Path(args[i + 1])
        del args[i:i + 2]
    if len(args) != 2 or "/" not in args[0] or not args[1].isdigit():
        print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
        return 2
    data = redact(snapshot(args[0], int(args[1])))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"saved {out}: {len(data['commits'])} commits, {len(data['runs'])} runs, "
          f"{len(data['issue_comments']) + len(data['reviews']) + len(data['review_comments'])} comments or reviews")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
