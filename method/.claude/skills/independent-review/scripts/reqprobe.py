"""pytest plugin used by req_run.py and mutate_check.py. Not run directly.

Records, for every collected test: its requirement tags as pytest sees them at
run time, its outcome, and how many plain `assert` statements passed in it.
Writes one JSON file to the path in the environment variable REQPROBE_OUT.

If REQPROBE_ONLY holds a comma-separated list of requirement ids, every test
that carries none of them is deselected.
"""
from __future__ import annotations

import json
import os

_items: dict[str, dict] = {}


def pytest_configure(config):
    config.addinivalue_line("markers", "req(*ids): requirement ids this test proves")


def _req_ids(item) -> list[str]:
    ids: list[str] = []
    for mark in item.iter_markers("req"):
        ids.extend(str(a) for a in mark.args)
    return sorted(set(ids))


def pytest_collection_modifyitems(config, items):
    only = os.environ.get("REQPROBE_ONLY", "").strip()
    if only:
        wanted = {x.strip() for x in only.split(",") if x.strip()}
        keep = [it for it in items if wanted & set(_req_ids(it))]
        drop = [it for it in items if not (wanted & set(_req_ids(it)))]
        if drop:
            config.hook.pytest_deselected(items=drop)
            items[:] = keep
    for it in items:
        path, lineno, _ = it.reportinfo()
        _items[it.nodeid] = {
            "nodeid": it.nodeid,
            "file": os.path.realpath(str(path)),
            "line": (lineno or 0) + 1,
            "name": getattr(it, "originalname", None) or it.name,
            "reqs": _req_ids(it),
            "outcome": "not-run",
            "asserts_passed": 0,
            "reason": "",
        }


def pytest_assertion_pass(item, lineno, orig, expl):
    rec = _items.get(item.nodeid)
    if rec is not None:
        rec["asserts_passed"] += 1


def pytest_runtest_logreport(report):
    rec = _items.get(report.nodeid)
    if rec is None:
        return
    xfail = hasattr(report, "wasxfail")
    if report.when == "setup":
        if report.skipped:
            rec["outcome"] = "xfailed" if xfail else "skipped"
            if isinstance(report.longrepr, tuple) and len(report.longrepr) == 3:
                rec["reason"] = str(report.longrepr[2])
            elif xfail:
                rec["reason"] = str(report.wasxfail)
        elif report.failed:
            rec["outcome"] = "error"
    elif report.when == "call":
        if xfail:
            rec["outcome"] = "xpassed" if report.passed else "xfailed"
            rec["reason"] = str(report.wasxfail)
        elif report.passed:
            rec["outcome"] = "passed"
        elif report.failed:
            rec["outcome"] = "failed"
        elif report.skipped:
            rec["outcome"] = "skipped"
            if isinstance(report.longrepr, tuple) and len(report.longrepr) == 3:
                rec["reason"] = str(report.longrepr[2])
    elif report.when == "teardown" and report.failed and rec["outcome"] == "passed":
        rec["outcome"] = "error"


def pytest_sessionfinish(session, exitstatus):
    out = os.environ.get("REQPROBE_OUT")
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump({"exitstatus": int(exitstatus), "items": list(_items.values())}, fh)
