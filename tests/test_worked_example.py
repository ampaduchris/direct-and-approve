"""Worked example (spec section 13): the document is compared with the saved pull request record, offline."""

from __future__ import annotations

import json
import re

import pytest

from helpers import ROOT

DOC = (ROOT / "docs" / "worked-example.md").read_text()
DATA = json.loads((ROOT / "docs" / "data" / "worked-example.json").read_text())
HEADINGS = [
    "1. The session line as written", "2. The confirmation gate", "3. The failing run", "4. The passing run",
    "5. The tier table", "6. Not verified", "7. The BUILD-LOG row", "8. The owner's merge comment",
    "9. The time from opening to merge",
]
SOURCE_LINK = re.compile(r"\]\((https://github\.com/[^)\s]+/(?:blob/[0-9a-f]{40}/[^)\s]*|actions/runs/\d+|pull/\d+(?:#issuecomment-\d+)?))\)")


def sections() -> dict[str, str]:
    parts = re.split(r"^## ", DOC, flags=re.M)[1:]
    return {p.splitlines()[0]: p for p in parts}


@pytest.mark.req("REQ-095")
def test_nine_headings_in_order():
    assert re.findall(r"^## (.+)$", DOC, flags=re.M) == HEADINGS


@pytest.mark.req("REQ-096")
def test_each_part_links_to_a_hash_a_run_or_a_pull_request():
    for name, text in sections().items():
        assert SOURCE_LINK.search(text), f"no source link in part: {name}"


@pytest.mark.req("REQ-096")
def test_no_link_points_at_a_branch_name():
    for link in re.findall(r"\]\((https?://[^)\s]+)\)", DOC):
        assert not re.search(r"/(?:blob|tree)/(?:main|master|s/)", link), link
        assert "/tree/" not in link, link


@pytest.mark.req("REQ-097")
def test_every_quotation_is_in_the_record():
    record = DATA["body"] + (ROOT / "docs/data/worked-example-session-line.md").read_text() + (ROOT / "docs/data/inkproof-BUILD-LOG.md").read_text()
    quoted = [line[2:] for line in DOC.splitlines() if line.startswith("> ")]
    assert quoted
    for line in quoted:
        assert line in record, line[:80]


@pytest.mark.req("REQ-097")
def test_every_number_equals_the_record():
    assert f"That is {DATA['minutes_open_to_merge']} minutes" in DOC
    assert DATA["opened_at"] in DOC and DATA["merged_at"] in DOC
    assert f"The pull request had {len(DATA['commits'])} commits" in DOC
    for run in DATA["runs"]:
        assert str(run["id"]) in DOC
    nv = DATA["body"].split("## Not verified\n")[1].split("\n## ")[0]
    assert f"This session listed {len([l for l in nv.splitlines() if l.startswith('- ')])} items" in DOC
    assert DATA["fetched_on"] in DOC


@pytest.mark.req("REQ-097")
def test_the_owner_comment_count_in_the_document_is_the_record_count():
    found = (len(DATA["issue_comments"]), len(DATA["reviews"]), len(DATA["review_comments"]))
    assert f"holds {found[0]} comments, {found[1]} reviews and {found[2]} review comments" in DOC
    if sum(found) == 0:
        assert "there is none" in DOC


@pytest.mark.req("REQ-098")
def test_the_not_verified_list_is_not_empty():
    nv = DATA["body"].split("## Not verified\n")[1].split("\n## ")[0]
    assert len([l for l in nv.splitlines() if l.startswith("- ")]) >= 1
