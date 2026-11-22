"""README (spec REQ-108, 115, 116, 117) against the files it quotes."""

from __future__ import annotations

import json
import re

import pytest

from helpers import ROOT, run

README = (ROOT / "README.md").read_text()
SPEC = (ROOT / "docs" / "spec.md").read_text()
STANDARD = (ROOT / "method" / "STANDARD.md").read_text()
DISCLOSURE = ("Built by directing Claude Code. No hand-written code. Every pull request was opened by the agent and "
              "approved and merged by me. Model and effort for every session are recorded in docs/BUILD-LOG.md.")


@pytest.mark.req("REQ-115")
def test_the_four_fixed_texts_are_word_for_word():
    table = SPEC.split("### 1.2 What is not claimed\n\n")[1].split("\n\nThe README repeats")[0].strip()
    assert table in README
    assert DISCLOSURE in README
    authorship = re.search(r"^Authorship note: \"(.+)\"$", STANDARD, re.M)
    assert authorship, "method/STANDARD.md must carry the authorship note"
    note = authorship.group(1)
    assert note in README
    assert note in STANDARD
    assert any(s in README for s in ("Status: active.", "Status: released, dependencies reviewed monthly."))


@pytest.mark.req("REQ-116")
def test_source_date_and_session_count_are_read_from_files():
    date = json.loads((ROOT / "method" / "MANIFEST.json").read_text())["source_date"]
    assert f"The source date of `method/` is {date}" in README
    sessions = json.loads(run("routing.py", ROOT / "docs/data/inkproof-BUILD-LOG.md", "--json").stdout)["sessions"]
    assert f"come from {sessions} sessions of one repository" in README


@pytest.mark.req("REQ-108")
def test_verify_section_has_exactly_three_runnable_blocks():
    section = README.split("## Verify it yourself")[1].split("\n## ")[0]
    assert len(re.findall(r"^```bash run$", section, re.M)) == 3


@pytest.mark.req("REQ-108")
def test_the_routing_output_in_the_readme_is_the_script_output():
    section = README.split("## Verify it yourself")[1].split("\n## ")[0]
    shown = section.split("```text\n")[1].split("```")[0].strip()
    assert shown == run("routing.py", ROOT / "docs/data/inkproof-BUILD-LOG.md").stdout.strip()


@pytest.mark.req("REQ-116")
def test_first_screen_proof_command_is_the_second_verify_block():
    command = "uv run --locked python method/calibration/_answers/prove.py | tail -n 4"
    assert f"$ {command}" in README.split("## Demo")[0]
    assert command in README.split("## Verify it yourself")[1]
    shown = README.split("```console\n")[1].split("```")[0]
    assert "ALL RUNS MATCH: 11 examples, 5 tools each, plus 5 fresh-input probes" in shown


@pytest.mark.req("REQ-117")
def test_no_document_claims_prevention_review_of_code_or_enforced_approval():
    # spec.md states the rule and so names the phrases.
    for path in [ROOT / "README.md", *(p for p in sorted((ROOT / "docs").glob("*.md")) if p.name != "spec.md")]:
        text = path.read_text().lower()
        for phrase in ("guarantees", "ensures correctness", "human-reviewed code"):
            assert phrase not in text, (path.name, phrase)


def test_the_readme_uses_no_dash_punctuation():
    assert "—" not in README and "–" not in README


def test_example_pr_in_the_readme_is_the_one_in_portfolio_yml():
    yml = (ROOT / "portfolio.yml").read_text()
    url = re.search(r"example_pr_url: (\S+)", yml).group(1)
    assert url in README
