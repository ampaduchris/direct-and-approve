"""Frontload documents (spec section 9) and the setup file (REQ-105)."""

from __future__ import annotations

import re

import pytest

from helpers import ROOT

DOC = (ROOT / "docs" / "frontload.md").read_text()
STATIC = (ROOT / "static" / "FRONTLOAD.md").read_text()
SETUP = (ROOT / "static" / "SETUP.md").read_text()
LOG = (ROOT / "docs" / "data" / "inkproof-BUILD-LOG.md").read_text()


@pytest.mark.req("REQ-065")
def test_required_headings_and_statements_are_present():
    for heading in ("## What is written ahead", "## Which model, and why", "## The status block",
                    "## How a session adopts a draft", "## The BUILD-LOG row records the adoption"):
        assert heading in DOC
    for phrase in ("reconciles the draft", "does not redo the work", "model, effort and date", "specifications", "evaluation designs", "essay theses", "review kits"):
        assert phrase in DOC.lower()


@pytest.mark.req("REQ-066")
def test_static_frontload_has_the_template_and_no_owner_items():
    assert "## Item template" in STATIC and "Done when:" in STATIC
    assert "## How later sessions use these" in STATIC
    ids = set(re.findall(r"\bF\d+\b", STATIC))
    assert ids == set(), ids


@pytest.mark.req("REQ-067")
def test_the_example_pair_links_to_the_adopted_spec_and_its_log_row():
    links = re.findall(r"\((https://github\.com/ampaduchris/inkproof/blob/([0-9a-f]{40})/docs/(spec|BUILD-LOG)\.md)\)", DOC)
    assert {k for _, _, k in links} == {"spec", "BUILD-LOG"}
    pinned = re.search(r"commit ([0-9a-f]{40})", LOG.splitlines()[0]).group(1)
    assert all(h == pinned for _, h, _ in links)
    row = next(l for l in LOG.splitlines() if l.startswith("| 2026-11-19 | 1.2 |"))
    assert "adopted draft: Fable 5.2 / high, 14 Nov 2026" in row
    assert "adopted draft: Fable 5.2 / high, 14 Nov 2026" in DOC


@pytest.mark.req("REQ-105")
def test_setup_has_no_machine_path_and_no_account_name():
    for pattern in (r"/Users/", r"/home/", r"C:\\Users\\", r"ampaduchris", r"Chris Ampadu", r"[\w.+-]+@[\w-]+\.[\w.]+"):
        assert not re.search(pattern, SETUP), pattern
    assert "## What Claude does on setup" in SETUP
    for check in ("git --version", "gh auth status", "python3 --version", "uv --version"):
        assert check in SETUP
    assert re.search(r"^9\. ", SETUP, re.M)
