"""The four pages under docs/ that the procedure, the kit and the privacy boundary need (REQ-013, 058, 075, 110)."""

from __future__ import annotations

import re

import pytest

from helpers import ROOT

CLAUDE = (ROOT / "method/CLAUDE.md").read_text(encoding="utf-8")
SKILL = (ROOT / "method/.claude/skills/independent-review/SKILL.md").read_text(encoding="utf-8")


def table_rows(text: str, heading: str) -> list[list[str]]:
    """Cells of every body row of the first table after `heading`."""
    body = text.split(heading, 1)[1]
    rows = []
    started = False
    for line in body.splitlines():
        if line.startswith("|"):
            started = True
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not re.fullmatch(r"-+", cells[0]) and cells[0] not in ("Word", "Id", "What", "Mark", "Owner types"):
                rows.append(cells)
        elif started:
            break
    return rows


def sentences(text: str) -> int:
    return len(re.findall(r"[.!?](?=\s|$)", text))


# ---- REQ-013 --------------------------------------------------------------------------------------

@pytest.mark.req("REQ-013")
def test_every_command_word_has_an_entry_of_at_most_three_sentences():
    words = [r[0].strip("`") for r in table_rows(CLAUDE, "The owner types one of these words.")]
    assert len(words) == 8
    entries = {r[0].strip("`"): r for r in table_rows((ROOT / "docs/procedure.md").read_text(encoding="utf-8"), "| Word |")}
    # table_rows drops the header row by name; the first call above has the same effect on its own header.
    assert sorted(entries) == sorted(words)
    for word, row in entries.items():
        assert 1 <= sentences(row[1]) <= 3, (word, row[1])


@pytest.mark.req("REQ-013")
def test_each_entry_cites_the_line_of_method_claude_md_that_defines_its_word():
    lines = CLAUDE.splitlines()
    doc = (ROOT / "docs/procedure.md").read_text(encoding="utf-8")
    assert "(../method/CLAUDE.md)" in doc
    for cells in table_rows(doc, "| Word |"):
        word = cells[0].strip("`")
        n = int(re.search(r"line (\d+)$", cells[2]).group(1))
        assert lines[n - 1].startswith(f"| `{word}` |"), (word, n, lines[n - 1][:40])


@pytest.mark.req("REQ-013")
def test_an_entry_missing_for_a_word_would_fail_the_comparison():
    words = [r[0].strip("`") for r in table_rows(CLAUDE, "The owner types one of these words.")]
    entries = [w for w in words if w != "maintain"]
    assert sorted(entries) != sorted(words)


# ---- REQ-058 (SHOULD) -----------------------------------------------------------------------------

@pytest.mark.req("REQ-058")
def test_the_session_format_page_shows_the_line_and_the_four_marks():
    doc = (ROOT / "docs/session-format.md").read_text(encoding="utf-8")
    assert "- [ ] **<id> <title>** · [switch to ]<model> / <effort>" in doc
    for mark in ("[ ]", "[p]", "[x]", "[~]"):
        assert f"| `{mark}` |" in doc


# ---- REQ-075 --------------------------------------------------------------------------------------

def skill_ids() -> list[str]:
    return re.findall(r"^\*\*(M\d+)\. ", SKILL, re.M)


@pytest.mark.req("REQ-075")
def test_every_taxonomy_entry_of_the_skill_has_a_row_with_a_command_and_an_example():
    doc = (ROOT / "docs/review-kit.md").read_text(encoding="utf-8")
    rows = {c[0]: c for c in table_rows(doc, "| Id | The way it misleads |")}
    assert sorted(rows, key=lambda i: int(i[1:])) == skill_ids() and len(skill_ids()) == 10
    for rid, cells in rows.items():
        assert cells[2].count("`") >= 2, rid
        assert re.fullmatch(r"ex\d\d", cells[3]), rid
        assert (ROOT / "method/calibration" / cells[3]).is_dir(), rid


@pytest.mark.req("REQ-075")
def test_the_example_named_for_each_entry_is_the_one_the_answers_file_plants():
    expected = (ROOT / "method/calibration/_answers/EXPECTED.md").read_text(encoding="utf-8")
    planted = dict(re.findall(r"^\| (ex\d\d) \| (M\d+)", expected, re.M))
    doc = (ROOT / "docs/review-kit.md").read_text(encoding="utf-8")
    for cells in table_rows(doc, "| Id | The way it misleads |"):
        assert planted[cells[3]] == cells[0], cells[:1] + cells[3:]


@pytest.mark.req("REQ-075")
def test_a_taxonomy_entry_with_no_row_fails_the_comparison():
    doc = (ROOT / "docs/review-kit.md").read_text(encoding="utf-8")
    ids = {c[0] for c in table_rows(doc, "| Id | The way it misleads |")} - {"M7"}
    assert ids != set(skill_ids())


# ---- REQ-110 --------------------------------------------------------------------------------------

NEVER_PUBLIC = {
    "the denylist": "denylist",
    "source material": "Source material",
    "notes": "Notes",
    "advisory files": "advisory",
    "metrics": "Metrics",
    "the real plan": "real plan",
    "real build folders": "build folder",
    "the upstream ledger and shortlist": "upstream ledger",
    "local settings": "Local settings",
}


@pytest.mark.req("REQ-110")
@pytest.mark.parametrize("what", NEVER_PUBLIC, ids=NEVER_PUBLIC)
def test_what_stays_private_has_a_row_with_a_reason_for_each_item(what):
    doc = (ROOT / "docs/what-stays-private.md").read_text(encoding="utf-8")
    rows = table_rows(doc, "| What | Why it stays private |")
    hits = [r for r in rows if NEVER_PUBLIC[what].lower() in r[0].lower()]
    assert hits, what
    assert sentences(hits[0][1]) >= 1 and len(hits[0][1]) > 20


@pytest.mark.req("REQ-110")
def test_it_says_that_every_replaced_value_in_the_mapping_is_public_by_design():
    doc = (ROOT / "docs/what-stays-private.md").read_text(encoding="utf-8")
    assert "Every replaced value in `extract.toml` is therefore public by design." in doc
