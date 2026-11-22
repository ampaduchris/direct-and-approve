"""Model routing script (spec section 12, FX-5). The BUILD-LOG files are built here from one clean table and one defect each."""

from __future__ import annotations

import json

import pytest

from helpers import run

HEAD = "# Build log\n\nAppend-only.\n\n"
COLS = "| Date | Session | Model | Effort (source) | Minutes | Tiers passed | NOT VERIFIED | PR |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n"
ROWS = [
    "| 2026-11-19 | 1.1 | Sonnet 5.5 | medium (app session record) | 4 | V1-V6 PASS | 2 | https://example.test/pull/1 |",
    "| 2026-11-19 | 1.2 | Sonnet 5.5 (adopted draft: Fable 5.2 / high, 14 Nov 2026) | high (app session record) | ~8 (estimated) | V1-V6 PASS | 5 | https://example.test/pull/2 |",
    "| 2026-11-20 | 1.3 | Opus 5.5 | high (app session record) | 13 (from the timer) | V1-V6 PASS | 9 | https://example.test/pull/3 |",
    "| 2026-11-20 | 1.4 | Sonnet 5.5 | high: not machine-verified | 10 | V1-V6 PASS | 1 | https://example.test/pull/4 |",
]


def log(tmp_path, rows=ROWS, name="BUILD-LOG.md"):
    path = tmp_path / name
    path.write_text(HEAD + COLS + "\n".join(rows) + "\n\nCI versions chosen: none.\n")
    return path


@pytest.mark.req("REQ-086")
def test_known_counts(tmp_path):
    result = run("routing.py", log(tmp_path), "--json")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["sessions"] == 4
    assert data["total_minutes"] == 35
    assert data["total_not_verified"] == 17
    assert data["effort_not_machine_verified"] == 1
    by = {(r["model"], r["effort"]): r["sessions"] for r in data["by_model_effort"]}
    assert by == {("Sonnet 5.5", "medium"): 1, ("Sonnet 5.5", "high"): 2, ("Opus 5.5", "high"): 1}


@pytest.mark.req("REQ-086")
def test_text_output_names_each_figure(tmp_path):
    out = run("routing.py", log(tmp_path)).stdout
    for needle in ("Sonnet 5.5 / high", "total minutes: 35", "total NOT VERIFIED: 17", "effort not machine-verified: 1"):
        assert needle in out


@pytest.mark.req("REQ-088")
def test_every_table_carries_its_session_count(tmp_path):
    out = run("routing.py", log(tmp_path)).stdout
    assert "(4 sessions)" in out
    assert out.count("(4 sessions)") >= 4
    data = json.loads(run("routing.py", log(tmp_path), "--json").stdout)
    assert data["sessions"] == 4


@pytest.mark.req("REQ-087")
@pytest.mark.parametrize(
    "bad,needle",
    [
        (ROWS[:1] + ["| 2026-11-19 | 1.2 | Sonnet 5.5 | high | 8 | V1-V6 PASS | 5 |"], "columns"),
        (ROWS[:1] + [ROWS[1].replace("~8 (estimated)", "a while")], "minutes"),
        (ROWS[:1] + [ROWS[1].replace("| 5 |", "| five |")], "NOT VERIFIED"),
        (ROWS[:1] + [ROWS[0]], "duplicate"),
    ],
    ids=["missing-column", "non-numeric-minutes", "non-numeric-count", "duplicate-id"],
)
def test_malformed_row_fails_loudly_with_no_partial_total(tmp_path, bad, needle):
    path = log(tmp_path, bad)
    result = run("routing.py", path)
    assert result.returncode == 1
    assert needle in result.stderr
    assert f"{path.name}:" in result.stderr
    assert "total" not in result.stdout


@pytest.mark.req("REQ-087")
def test_a_log_with_no_table_is_an_error(tmp_path):
    path = tmp_path / "BUILD-LOG.md"
    path.write_text("# Build log\n\nnothing\n")
    assert run("routing.py", path).returncode == 1


DOC = "docs/model-routing.md"
DATA = "docs/data/inkproof-BUILD-LOG.md"


def _root():
    from helpers import ROOT
    return ROOT


@pytest.mark.req("REQ-089")
def test_model_routing_numbers_equal_script_output():
    root = _root()
    text = (root / DOC).read_text()
    blocks = [b for b in text.split("```text\n")[1:]]
    assert blocks, "no output block in the document"
    shown = blocks[0].split("```")[0].strip()
    assert shown == run("routing.py", root / DATA).stdout.strip()


@pytest.mark.req("REQ-089")
def test_data_copy_names_its_repository_and_commit():
    first = (_root() / DATA).read_text().splitlines()[0]
    assert "ampaduchris/inkproof" in first
    import re
    assert re.search(r"commit [0-9a-f]{40}\b", first)


@pytest.mark.req("REQ-085")
def test_model_routing_states_the_rule():
    text = (_root() / DOC).read_text()
    for heading in ("## The rule", "## What the sessions used", "## What the numbers do not show"):
        assert heading in text
    for phrase in ("differs from the author", "the reason, and the risk", "never refused"):
        assert phrase in text


@pytest.mark.req("REQ-090")
def test_model_routing_makes_no_better_model_claim():
    text = (_root() / DOC).read_text().lower()
    for phrase in ("better than", "outperform", "more accurate", "superior"):
        assert phrase not in text.replace("does not say that one model is better than another", "")
