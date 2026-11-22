"""Session format (spec section 8). FX-4 is built here from one clean pair and one defect each."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from helpers import ROOT, run

PLAN = """# Plan

## Phases

| Id | Name | Status | Folder |
| --- | --- | --- | --- |
| 00 | Example | CURRENT | 00-example |
| 01 | Later | planned | 01-later |
"""

SESSIONS = """# Sessions

- [x] **1.1 First** · Sonnet 5.5 / medium
  - Exit test: the first thing runs.
- [p] **1.2 Second** · Sonnet 5.5 / high PR: https://github.com/example/project/pull/2
  - Exit test: the second thing runs.
- [ ] **1.3 Third** · switch to Opus 5.5 / xhigh
  - Exit test: the third thing runs.
- [~] **1.4 Fourth** · Haiku 5.5 / low
  - Note: stopped after two failed attempts.
  - Exit test: the fourth thing runs.
"""

LATER = "# Sessions\n\n- [ ] **2.1 Only** · Sonnet 5.5 / max\n  - Exit test: it runs.\n"


def make(tmp: Path, plan: str = PLAN, sessions: str = SESSIONS, later: str | None = LATER) -> Path:
    (tmp / "builds/00-example").mkdir(parents=True)
    (tmp / "PLAN.md").write_text(plan, encoding="utf-8")
    (tmp / "builds/00-example/SESSIONS.md").write_text(sessions, encoding="utf-8")
    if later is not None:
        (tmp / "builds/01-later").mkdir()
        (tmp / "builds/01-later/SESSIONS.md").write_text(later, encoding="utf-8")
    return tmp


def check(folder: Path):
    return run("check_sessions.py", folder)


@pytest.fixture
def clean(tmp_path):
    return make(tmp_path)


@pytest.mark.req("REQ-057")
def test_clean_folder_passes_with_one_summary_line(clean):
    r = check(clean)
    assert r.returncode == 0, r.stdout + r.stderr
    assert re.fullmatch(r"check_sessions: OK\. files read: 3, sessions read: 5", r.stdout.strip()), r.stdout


@pytest.mark.req("REQ-051")
@pytest.mark.parametrize("old,new,needle,line", [
    ("Sonnet 5.5 / medium", "medium", "model", 3),
    ("Sonnet 5.5 / high PR", "Sonnet 5.5 PR", "effort", 5),
    ("Sonnet 5.5 / medium", "Sonnet 5.5 / maximum", "effort", 3),
    ("Sonnet 5.5 / medium", "Sonnet 5.5 or Opus 5.5 / medium", "more than one model", 3),
], ids=["no-model", "no-effort", "bad-effort", "two-models"])
def test_session_line_defects_fail_naming_file_and_line(tmp_path, old, new, needle, line):
    folder = make(tmp_path, sessions=SESSIONS.replace(old, new, 1))
    r = check(folder)
    assert r.returncode == 1, r.stdout
    assert f"builds/00-example/SESSIONS.md:{line}:" in r.stdout
    assert needle in r.stdout


@pytest.mark.req("REQ-052")
def test_session_with_no_exit_test_bullet_fails(tmp_path):
    folder = make(tmp_path, sessions=SESSIONS.replace("  - Exit test: the third thing runs.\n", "  - It should run.\n"))
    r = check(folder)
    assert r.returncode == 1
    assert "1.3" in r.stdout and "Exit test" in r.stdout


@pytest.mark.req("REQ-052")
def test_the_word_exit_test_inside_other_text_does_not_count(tmp_path):
    folder = make(tmp_path, sessions=SESSIONS.replace("  - Exit test: the third thing runs.\n", "  - Write the exit test later.\n"))
    assert check(folder).returncode == 1


@pytest.mark.req("REQ-053")
def test_mark_outside_the_four_fails(tmp_path):
    r = check(make(tmp_path, sessions=SESSIONS.replace("[ ] **1.3", "[?] **1.3")))
    assert r.returncode == 1 and "mark" in r.stdout


@pytest.mark.req("REQ-053")
def test_p_without_a_pull_request_link_fails(tmp_path):
    r = check(make(tmp_path, sessions=SESSIONS.replace(" PR: https://github.com/example/project/pull/2", "")))
    assert r.returncode == 1 and "pull request" in r.stdout


@pytest.mark.req("REQ-053")
def test_tilde_without_a_note_fails(tmp_path):
    r = check(make(tmp_path, sessions=SESSIONS.replace("  - Note: stopped after two failed attempts.\n", "")))
    assert r.returncode == 1 and "note" in r.stdout


@pytest.mark.req("REQ-054")
def test_duplicate_session_id_in_one_file_fails(tmp_path):
    r = check(make(tmp_path, sessions=SESSIONS.replace("**1.4 Fourth**", "**1.3 Fourth**")))
    assert r.returncode == 1 and "duplicate" in r.stdout and "1.3" in r.stdout


@pytest.mark.req("REQ-054")
def test_the_same_id_in_two_different_files_is_allowed(tmp_path):
    assert check(make(tmp_path, later=LATER.replace("2.1", "1.1"))).returncode == 0


@pytest.mark.req("REQ-055")
def test_two_current_rows_fail(tmp_path):
    r = check(make(tmp_path, plan=PLAN.replace("planned", "CURRENT")))
    assert r.returncode == 1 and "CURRENT" in r.stdout


@pytest.mark.req("REQ-055")
def test_a_row_whose_folder_has_no_sessions_file_fails(tmp_path):
    r = check(make(tmp_path, later=None))
    assert r.returncode == 1 and "01-later" in r.stdout


@pytest.mark.req("REQ-055")
def test_a_plan_with_no_folder_column_fails(tmp_path):
    plan = "# Plan\n\n## Phases\n\n| Id | Name | Status |\n| --- | --- | --- |\n| 00 | Example | CURRENT |\n"
    r = check(make(tmp_path, plan=plan, later=None))
    assert r.returncode == 1 and "Folder" in r.stdout


@pytest.mark.req("REQ-055")
def test_a_plan_with_no_status_column_fails(tmp_path):
    plan = "# Plan\n\n## Phases\n\n| Id | Name | Folder |\n| --- | --- | --- |\n| 00 | Example | 00-example |\n"
    r = check(make(tmp_path, plan=plan, later=None))
    assert r.returncode == 1 and "Status" in r.stdout


@pytest.mark.req("REQ-055")
def test_a_folder_cell_may_carry_the_builds_prefix(tmp_path):
    assert check(make(tmp_path, plan=PLAN.replace("| 00-example |", "| `builds/00-example/` |"))).returncode == 0


@pytest.mark.req("REQ-056")
def test_done_session_after_an_unstarted_one_fails(tmp_path):
    s = SESSIONS.replace("[ ] **1.3", "[x] **1.3").replace("[x] **1.1", "[ ] **1.1")
    r = check(make(tmp_path, sessions=s))
    assert r.returncode == 1 and "1.3" in r.stdout and "earlier" in r.stdout


@pytest.mark.req("REQ-056")
def test_pr_session_after_an_unstarted_one_fails(tmp_path):
    r = check(make(tmp_path, sessions=SESSIONS.replace("[x] **1.1", "[ ] **1.1")))
    assert r.returncode == 1 and "1.2" in r.stdout


@pytest.mark.req("REQ-051")
def test_every_problem_is_listed_not_just_the_first(tmp_path):
    s = SESSIONS.replace("Sonnet 5.5 / medium", "medium").replace("  - Exit test: the third thing runs.\n", "")
    r = check(make(tmp_path, sessions=s))
    assert r.returncode == 1
    assert r.stdout.count("builds/00-example/SESSIONS.md:") >= 2


@pytest.mark.req("REQ-057")
def test_usage_errors_exit_2(tmp_path):
    assert run("check_sessions.py").returncode == 2
    assert run("check_sessions.py", tmp_path / "nowhere").returncode == 2
    assert run("check_sessions.py", tmp_path).returncode == 2  # no PLAN.md


@pytest.mark.req("REQ-057")
def test_the_published_method_folder_passes():
    r = check(ROOT / "method")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "sessions read: 2" in r.stdout
