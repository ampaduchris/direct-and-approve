"""Checks on the published method/ folder itself, which CI can run because they need no private file."""

from __future__ import annotations

import json
import re
import tomllib

import pytest

from helpers import ROOT
from test_extract import PATH_IN_TEXT, skill_paths_that_do_not_resolve

METHOD = ROOT / "method"
SHIPPED = tomllib.loads((ROOT / "extract.toml").read_text(encoding="utf-8"))
MANIFEST = json.loads((METHOD / "MANIFEST.json").read_text(encoding="utf-8"))


@pytest.mark.req("REQ-011")
def test_method_claude_md_has_every_recorded_heading_and_command_word():
    recorded = (ROOT / "tests/data/method-claude-headings.txt").read_text().splitlines()
    text = (METHOD / "CLAUDE.md").read_text()
    headings = [l for l in text.splitlines() if l.startswith("#")]
    assert headings == recorded
    for required in ("The `continue` procedure", "Hard rules", "Context and tool output", "Model advice"):
        assert any(required in h for h in headings)
    for word in ("setup", "continue", "upstream", "maintain", "status", "merged", "frontload", "proceed anyway"):
        assert re.search(rf"^\| `{word}` \|", text, re.M), word
    assert "Session marks:" in text


@pytest.mark.req("REQ-012")
def test_no_replacement_source_string_survives_anywhere_in_method_and_placeholders_are_present():
    froms = [r["from"] for r in SHIPPED["replacement"]]
    for p in METHOD.rglob("*"):
        if p.is_file():
            text = p.read_text(encoding="utf-8")
            assert not [f for f in froms if f in text], p.relative_to(ROOT)
            assert not [f for f in froms if f in p.relative_to(METHOD).as_posix()]
    claude = (METHOD / "CLAUDE.md").read_text()
    for placeholder in ("<owner>", "<account>", "<control-repo>"):
        assert placeholder in claude


@pytest.mark.req("REQ-021")
def test_method_standard_states_the_manifest_source_date():
    lines = (METHOD / "STANDARD.md").read_text().splitlines()
    assert lines[0].startswith("# ")
    assert next(l for l in lines[1:] if l.strip()) == f"Copied from the private authority on {MANIFEST['source_date']}."


@pytest.mark.req("REQ-022")
def test_method_standard_keeps_the_tier_and_control_row_ids():
    ids = re.findall(r"^\| (V[1-6]|R[1-8]) \|", (METHOD / "STANDARD.md").read_text(), re.M)
    assert ids == ["V1", "V2", "V3", "V4", "V5", "V6", "R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"]


@pytest.mark.req("REQ-070")
@pytest.mark.parametrize("skill", ["independent-review", "pre-pr-check"])
def test_method_skills_keep_front_matter(skill):
    head = (METHOD / ".claude/skills" / skill / "SKILL.md").read_text().split("---")[1]
    assert re.search(rf"^name: {skill}$", head, re.M) and re.search(r"^description: .+", head, re.M)


@pytest.mark.req("REQ-071")
def test_method_has_the_six_kit_scripts():
    names = sorted(p.name for p in (METHOD / ".claude/skills/independent-review/scripts").glob("*.py"))
    assert names == ["literal_overlap.py", "mutate_check.py", "req_run.py", "reqprobe.py", "spec_diff.py", "tier_check.py"]


@pytest.mark.req("REQ-072")
def test_paths_named_in_the_method_skills_resolve_inside_method():
    assert skill_paths_that_do_not_resolve(METHOD) == []
    # The scan must find something to check, or it proves nothing.
    found = [rel for s in (METHOD / ".claude/skills").glob("*/SKILL.md") for rel in PATH_IN_TEXT.findall(s.read_text())]
    assert any(r.startswith("calibration/") for r in found), found


@pytest.mark.req("REQ-073")
def test_method_calibration_readmes_state_that_the_answers_are_public():
    for rel in ("calibration/README.md", "calibration/_answers/README.md"):
        first = (METHOD / rel).read_text().split("\n\n")[1].lower()
        assert "answers are public" in first and "demonstration only" in first


@pytest.mark.req("REQ-073")
def test_method_calibration_has_eleven_examples_and_the_answers():
    assert sorted(p.name for p in (METHOD / "calibration").glob("ex*")) == [f"ex{n:02d}" for n in range(1, 12)]
    for name in ("EXPECTED.md", "prove.py"):
        assert (METHOD / "calibration/_answers" / name).is_file()


@pytest.mark.req("REQ-016")
def test_section_py_is_published_and_names_no_private_path():
    text = (METHOD / "tools/section.py").read_text()
    assert not re.search(r"/Users/|/home/|builds/\d|UPSTREAM", text)


def test_the_continue_steps_that_the_skills_cite_are_still_those_steps():
    """N8: pre-pr-check cites steps 8, 9 and 10 of the continue procedure."""
    steps = dict(re.findall(r"^(\d+)\. (.+)$", (METHOD / "CLAUDE.md").read_text(), re.M))
    assert "Verify" in steps["8"]
    assert "pull request" in steps["9"].lower() or "PR" in steps["9"]
    assert "BUILD-LOG" in steps["10"]
