"""Extraction (spec section 7) on the synthetic fixture control folder FX-1 and its variants."""

from __future__ import annotations

import json
import os
import re
import tomllib
from pathlib import Path

import pytest

from helpers import DATE, ROOT, SCRIPTS, run, tree_hash

SHIPPED = tomllib.loads((ROOT / "extract.toml").read_text(encoding="utf-8"))


# ---- mapping (REQ-010, 020, 030, 039) ------------------------------------------------------------

@pytest.mark.req("REQ-010")
def test_claude_md_is_a_copy_entry():
    entry = next(e for e in SHIPPED["entry"] if e["target"] == "method/CLAUDE.md")
    assert entry["kind"] == "copy" and entry["source"] == "CLAUDE.md"


@pytest.mark.req("REQ-020")
def test_standard_md_is_a_copy_entry():
    entry = next(e for e in SHIPPED["entry"] if e["target"] == "method/STANDARD.md")
    assert entry["kind"] == "copy" and entry["source"] == "STANDARD.md"


@pytest.mark.req("REQ-030")
def test_shipped_mapping_has_no_duplicate_target():
    targets = [e["target"] for e in SHIPPED["entry"]]
    assert len(targets) == len(set(targets))


@pytest.mark.req("REQ-030")
def test_two_entries_with_one_target_are_a_configuration_error(fx):
    fx.set_mapping(fx.mapping.read_text() + '\n[[entry]]\nkind = "copy"\nsource = "STANDARD.md"\ntarget = "method/CLAUDE.md"\n')
    r = fx.extract()
    assert r.returncode == 3, r.stderr
    assert "method/CLAUDE.md" in r.stderr


@pytest.mark.req("REQ-030")
def test_every_output_file_is_in_the_manifest_once(fx):
    assert fx.extract().returncode == 0
    files = json.loads((fx.out / "MANIFEST.json").read_text())["files"]
    paths = [f["path"] for f in files]
    assert len(paths) == len(set(paths))
    on_disk = sorted(p for p in tree_hash(fx.out) if p != "MANIFEST.json")
    assert sorted(paths) == on_disk


@pytest.mark.req("REQ-039")
def test_mapping_where_a_to_contains_a_from_is_rejected(fx):
    fx.set_mapping(fx.mapping.read_text().replace('to = "<account>"', 'to = "<adafixture>"', 1))
    r = fx.extract()
    assert r.returncode == 3, r.stderr
    assert not fx.out.exists()


# ---- determinism (REQ-031) ------------------------------------------------------------------------

@pytest.mark.req("REQ-031")
def test_two_runs_give_identical_bytes_manifest_included(fx):
    assert fx.extract().returncode == 0
    first = tree_hash(fx.out)
    assert "MANIFEST.json" in first
    assert fx.extract().returncode == 0
    assert tree_hash(fx.out) == first


@pytest.mark.req("REQ-031")
def test_output_does_not_depend_on_locale_or_working_directory(fx, tmp_path):
    assert fx.extract().returncode == 0
    first = tree_hash(fx.out)
    env = {**os.environ, "LC_ALL": "C", "LANG": "C", "TZ": "Pacific/Auckland"}
    other = tmp_path / "elsewhere"
    other.mkdir()
    r = run("extract.py", fx.control, "--repo", fx.repo, "--date", DATE, cwd=other, env=env)
    assert r.returncode == 0, r.stderr
    assert tree_hash(fx.out) == first


@pytest.mark.req("REQ-031")
def test_manifest_lists_paths_in_sorted_order_with_the_source_date(fx):
    fx.extract()
    m = json.loads((fx.out / "MANIFEST.json").read_text())
    assert m["source_date"] == DATE
    paths = [f["path"] for f in m["files"]]
    assert paths == sorted(paths)
    assert all(re.fullmatch(r"[0-9a-f]{64}", f["sha256"]) for f in m["files"])
    assert {f["kind"] for f in m["files"]} == {"copy", "tree", "static"}


# ---- replacements (REQ-011, 012, 021, 022, 032) ----------------------------------------------------

@pytest.mark.req("REQ-032")
def test_replacements_are_literal_and_case_sensitive(fx):
    fx.append("CLAUDE.md", "\nA.B axb aXb\n")
    fx.set_mapping(fx.mapping.read_text() + '\n[[replacement]]\nfrom = "A.B"\nto = "ONE"\n')
    assert fx.extract().returncode == 0
    text = (fx.out / "CLAUDE.md").read_text()
    assert "ONE axb aXb" in text


@pytest.mark.req("REQ-032")
def test_longest_from_is_applied_first(fx):
    out = (fx.extract(), (fx.out / "CLAUDE.md").read_text())[1]
    assert "`<account>/<control-repo>`" in out
    assert "The account is `<account>`" in out


@pytest.mark.req("REQ-012")
def test_the_three_owner_values_become_placeholders(fx):
    assert "Ada Fixture" in (fx.control / "CLAUDE.md").read_text()
    fx.extract()
    out = (fx.out / "CLAUDE.md").read_text()
    for planted in ("Ada Fixture", "adafixture"):
        assert planted not in out
    for placeholder in ("<owner>", "<account>", "<control-repo>"):
        assert placeholder in out


@pytest.mark.req("REQ-011")
def test_every_source_heading_and_command_word_survives(fx):
    fx.extract()
    src = (fx.control / "CLAUDE.md").read_text().splitlines()
    out = (fx.out / "CLAUDE.md").read_text().splitlines()
    headings = lambda lines: [l for l in lines if l.startswith("#")]  # noqa: E731
    words = lambda lines: [l.split("|")[1].strip() for l in lines if re.match(r"^\| `", l)]  # noqa: E731
    assert headings(out)[1:] == headings(src)[1:]
    assert words(out) == words(src) == ["`setup`", "`continue`", "`status`"]
    for required in ("The `continue` procedure", "Hard rules", "Context and tool output", "Model advice"):
        assert any(required in h for h in headings(out))


@pytest.mark.req("REQ-011")
def test_a_missing_heading_in_the_output_would_be_found(fx):
    """The comparison above must be able to fail: remove a heading and the lists differ."""
    fx.extract()
    out = (fx.out / "CLAUDE.md").read_text().replace("## Hard rules\n", "")
    src_h = [l for l in (fx.control / "CLAUDE.md").read_text().splitlines() if l.startswith("#")]
    out_h = [l for l in out.splitlines() if l.startswith("#")]
    assert out_h != src_h


@pytest.mark.req("REQ-021")
def test_standard_states_its_source_date_on_the_first_line_after_the_title(fx):
    fx.extract()
    lines = (fx.out / "STANDARD.md").read_text().splitlines()
    assert lines[0] == "# Build standard"
    first = next(l for l in lines[1:] if l.strip())
    assert first == f"Copied from the private authority on {DATE}."


@pytest.mark.req("REQ-022")
def test_standard_keeps_every_tier_and_control_row_id(fx):
    fx.extract()
    src = (fx.control / "STANDARD.md").read_text()
    out = (fx.out / "STANDARD.md").read_text()
    ids = lambda t: re.findall(r"^\| (V[1-6]|R[1-8]) \|", t, re.M)  # noqa: E731
    assert ids(out) == ids(src) == ["V1", "V2", "V3", "V4", "V5", "V6", "R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"]


# ---- private markers (REQ-033, 034, 035) --------------------------------------------------------

def _no_leak(r, secret):
    assert secret not in r.stdout and secret not in r.stderr


@pytest.mark.req("REQ-033")
def test_marker_in_a_copy_refuses_with_entry_and_line(fx):
    fx.append("CLAUDE.md", "see /Users/zed/notes\n")
    n = len((fx.control / "CLAUDE.md").read_text().splitlines())
    r = fx.extract()
    assert r.returncode == 2
    assert "CLAUDE.md" in r.stderr and f":{n}" in r.stderr
    _no_leak(r, "zed")


@pytest.mark.req("REQ-033")
def test_marker_in_a_tree_file_refuses(fx):
    p = fx.control / "private/frontload/F12-calibration/ex01/code.py"
    p.write_text(p.read_text() + "# mail zed@secret.test\n")
    r = fx.extract()
    assert r.returncode == 2
    assert "calibration" in r.stderr and "code.py" in r.stderr
    _no_leak(r, "zed")


@pytest.mark.req("REQ-033")
def test_marker_in_a_file_name_refuses(fx):
    """File names are scanned as well as contents. This name holds a from string."""
    (fx.control / "private/frontload/F12-calibration/ex01/note-adafixture.txt").write_text("x\n")
    r = fx.extract()
    assert r.returncode == 2, r.stderr
    assert "file name" in r.stderr
    _no_leak(r, "note-adafixture")


@pytest.mark.req("REQ-033")
def test_a_from_string_that_survives_replacement_is_a_marker(fx):
    """A tree file outside replace_in is copied as it is, so a from string in it survives and refuses."""
    p = fx.control / "private/frontload/F12-calibration/ex01/data.txt"
    p.write_text("owner: Ada Fixture\n")
    r = fx.extract()
    assert r.returncode == 2
    assert "data.txt" in r.stderr
    _no_leak(r, "Ada Fixture")


@pytest.mark.req("REQ-034")
def test_a_refused_run_leaves_the_output_folder_as_it_was(fx):
    assert fx.extract().returncode == 0
    before = tree_hash(fx.out)
    fx.append("CLAUDE.md", "leak /home/zed\n")
    assert fx.extract().returncode == 2
    assert tree_hash(fx.out) == before


@pytest.mark.req("REQ-034")
def test_a_refused_first_run_creates_no_output_and_no_temporary_folder(fx):
    fx.append("CLAUDE.md", "leak /home/zed\n")
    assert fx.extract().returncode == 2
    assert not fx.out.exists()
    assert [p.name for p in fx.repo.iterdir() if p.name.startswith(".")] == []


FORBIDDEN_CASES = {
    "unix home": "path /Users/someone/x",
    "linux home": "path /home/someone/x",
    "windows home": "path C:\\Users\\someone\\x",
    "email": "write to someone@secret.test please",
    "private link": "see https://claude.ai/code/session_abc",
    "app link": "claude://claude.ai/session",
}


@pytest.mark.req("REQ-035")
@pytest.mark.parametrize("line", FORBIDDEN_CASES.values(), ids=FORBIDDEN_CASES.keys())
def test_shipped_forbidden_patterns_catch_each_case(line):
    patterns = [re.compile(p) for p in SHIPPED["forbidden"]["patterns"]]
    assert any(p.search(line) for p in patterns)


@pytest.mark.req("REQ-035")
def test_shipped_forbidden_patterns_allow_reserved_example_domains():
    patterns = [re.compile(p) for p in SHIPPED["forbidden"]["patterns"]]
    assert not any(p.search("write to someone@example.com") for p in patterns)


# ---- tree entries (REQ-036), inputs (REQ-037) -------------------------------------------------------

@pytest.mark.req("REQ-036")
def test_tree_copies_only_included_files_and_none_excluded(fx):
    cache = fx.control / ".claude/skills/independent-review/scripts/__pycache__"
    cache.mkdir()
    (cache / "x.pyc").write_bytes(b"\x00\x01")
    (fx.control / ".claude/skills/independent-review/notes.md").write_text("not included\n")
    (fx.control / "private/frontload/F12-calibration/README.md").write_text("excluded\n")
    assert fx.extract().returncode == 0
    files = tree_hash(fx.out)
    assert not any("__pycache__" in f for f in files)
    assert ".claude/skills/independent-review/notes.md" not in files
    assert ".claude/skills/independent-review/SKILL.md" in files
    assert len([f for f in files if f.startswith(".claude/skills/independent-review/scripts/")]) == 6
    assert "calibration/_answers/prove.py" in files
    assert "Written for" not in (fx.out / "calibration/README.md").read_text()


@pytest.mark.req("REQ-036")
def test_a_symbolic_link_is_never_followed_or_copied(fx):
    target = fx.base / "outside.txt"
    target.write_text("outside the control folder\n")
    link = fx.control / "private/frontload/F12-calibration/ex01/link.txt"
    link.symlink_to(target)
    (fx.control / "private/frontload/F12-calibration/ex01/dirlink").symlink_to(fx.base)
    assert fx.extract().returncode == 0
    files = tree_hash(fx.out)
    assert not any("link" in f for f in files)
    assert not any("outside" in (fx.out / f).read_text(errors="ignore") for f in files if f.endswith(".txt"))


@pytest.mark.req("REQ-037")
def test_missing_source_exits_3_and_names_the_entry(fx):
    (fx.control / "tools/section.py").unlink()
    r = fx.extract()
    assert r.returncode == 3
    assert "tools/section.py" in r.stderr


@pytest.mark.req("REQ-037")
def test_unreadable_source_exits_3_and_names_the_entry(fx):
    p = fx.control / "tools/section.py"
    p.chmod(0)
    try:
        if os.access(p, os.R_OK):
            pytest.skip("running with rights that ignore file modes")
        r = fx.extract()
    finally:
        p.chmod(0o644)
    assert r.returncode == 3
    assert "tools/section.py" in r.stderr


@pytest.mark.req("REQ-037")
def test_binary_source_where_text_is_expected_exits_3(fx):
    (fx.control / "tools/scrub.py").write_bytes(b"\xff\xfe\x00binary\x80")
    r = fx.extract()
    assert r.returncode == 3
    assert "tools/scrub.py" in r.stderr


@pytest.mark.req("REQ-037")
def test_a_binary_file_in_a_tree_is_never_published_unscanned(fx):
    (fx.control / "private/frontload/F12-calibration/ex01/blob.bin").write_bytes(b"\xff\xfe\x00")
    r = fx.extract()
    assert r.returncode == 3
    assert "blob.bin" in r.stderr


# ---- --check (REQ-038) ---------------------------------------------------------------------------

@pytest.mark.req("REQ-038")
def test_check_on_a_clean_output_exits_0_and_writes_nothing(fx):
    fx.extract()
    before = tree_hash(fx.out)
    r = fx.check()
    assert r.returncode == 0, r.stderr
    assert tree_hash(fx.out) == before


@pytest.mark.req("REQ-038")
def test_check_with_no_output_exits_1_and_creates_nothing(fx):
    r = fx.check()
    assert r.returncode == 1
    assert not fx.out.exists()


@pytest.mark.req("REQ-038")
def test_check_lists_edited_missing_and_extra_paths(fx):
    fx.extract()
    (fx.out / "CLAUDE.md").write_text("hand edit\n")
    (fx.out / "tools/section.py").unlink()
    (fx.out / "extra.txt").write_text("stray\n")
    before = tree_hash(fx.out)
    r = fx.check()
    assert r.returncode == 1
    for path in ("CLAUDE.md", "tools/section.py", "extra.txt"):
        assert path in r.stdout
    assert tree_hash(fx.out) == before


@pytest.mark.req("REQ-038")
def test_check_finds_a_source_that_moved_on(fx):
    fx.extract()
    fx.append("STANDARD.md", "\nA new line.\n")
    r = fx.check()
    assert r.returncode == 1
    assert "STANDARD.md" in r.stdout


# ---- source date (REQ-040), exit codes (REQ-041) ----------------------------------------------------

@pytest.mark.req("REQ-040")
def test_date_flag_is_the_source_date(fx):
    fx.extract(date="2001-02-03")
    assert json.loads((fx.out / "MANIFEST.json").read_text())["source_date"] == "2001-02-03"


@pytest.mark.req("REQ-040")
def test_without_the_flag_the_date_is_the_newest_commit_of_the_control_folder(fx):
    import subprocess
    git = lambda *a: subprocess.run(["git", "-C", str(fx.control), *a], capture_output=True, text=True, check=True)  # noqa: E731
    git("init", "-q")
    git("add", "-A")
    git("-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "fixture")
    expected = git("log", "-1", "--format=%cs").stdout.strip()
    r = fx.extract(date=None)
    assert r.returncode == 0, r.stderr
    assert json.loads((fx.out / "MANIFEST.json").read_text())["source_date"] == expected


@pytest.mark.req("REQ-040")
def test_without_the_flag_and_without_commits_the_run_stops_and_does_not_use_the_clock(fx):
    r = fx.extract(date=None)
    assert r.returncode == 3
    assert not fx.out.exists()


@pytest.mark.req("REQ-040")
def test_the_script_never_reads_the_clock():
    src = (SCRIPTS / "extract.py").read_text()
    for banned in ("datetime", "time.time", "date.today", "strftime", "gmtime", "localtime"):
        assert banned not in src, banned


@pytest.mark.req("REQ-040")
def test_a_malformed_date_flag_is_a_usage_error(fx):
    assert fx.extract(date="22-11-2026").returncode == 3


@pytest.mark.req("REQ-041")
def test_exit_code_0_on_success(fx):
    assert fx.extract().returncode == 0


@pytest.mark.req("REQ-041")
def test_exit_code_1_when_check_finds_a_difference(fx):
    assert fx.check().returncode == 1


@pytest.mark.req("REQ-041")
def test_exit_code_2_on_a_private_marker(fx):
    fx.append("STANDARD.md", "/home/zed\n")
    assert fx.extract().returncode == 2


@pytest.mark.req("REQ-041")
def test_exit_code_3_on_usage_configuration_and_input_errors(fx, tmp_path):
    assert run("extract.py").returncode == 3
    assert run("extract.py", tmp_path / "nowhere", "--repo", fx.repo, "--date", DATE).returncode == 3
    fx.set_mapping("this is = not [valid toml")
    assert fx.extract().returncode == 3


@pytest.mark.req("REQ-042")
def test_one_line_per_entry_is_printed(fx):
    r = fx.extract()
    lines = [l for l in r.stdout.splitlines() if l.startswith(("copy", "tree", "static"))]
    assert len(lines) == len(tomllib.loads(fx.mapping.read_text())["entry"])


# ---- skills tree (REQ-070, 071, 072, 073), manifest (REQ-002), statics (REQ-050, 080) -----------------

@pytest.mark.req("REQ-071")
def test_kit_scripts_are_byte_identical_to_the_source(fx):
    fx.extract()
    src = fx.control / ".claude/skills/independent-review/scripts"
    out = fx.out / ".claude/skills/independent-review/scripts"
    names = sorted(p.name for p in src.glob("*.py"))
    assert len(names) == 6
    for n in names:
        assert (out / n).read_bytes() == (src / n).read_bytes()


@pytest.mark.req("REQ-071")
def test_a_replacement_that_would_touch_a_py_under_the_skills_tree_is_a_configuration_error(fx):
    fx.set_mapping(fx.mapping.read_text().replace('replace_in = ["SKILL.md"]', 'replace_in = ["SKILL.md", "scripts/*.py"]', 1))
    r = fx.extract()
    assert r.returncode == 3
    assert "skills" in r.stderr
    assert not fx.out.exists()


@pytest.mark.req("REQ-070")
def test_each_skill_keeps_front_matter_with_name_and_description(fx):
    fx.extract()
    for skill in ("independent-review", "pre-pr-check"):
        text = (fx.out / ".claude/skills" / skill / "SKILL.md").read_text()
        head = text.split("---")[1]
        assert re.search(rf"^name: {skill}$", head, re.M)
        assert re.search(r"^description: .+", head, re.M)
    assert "Ada Fixture" not in (fx.out / ".claude/skills/independent-review/SKILL.md").read_text()


PATH_IN_TEXT = re.compile(r"`((?:tools|\.claude|calibration|builds|private)/[^`\s*<>]+)`")


def skill_paths_that_do_not_resolve(root: Path) -> list[str]:
    missing = []
    for skill in sorted((root / ".claude/skills").glob("*/SKILL.md")):
        for rel in PATH_IN_TEXT.findall(skill.read_text(encoding="utf-8")):
            if not (root / rel.rstrip("/.,;")).exists():
                missing.append(f"{skill.parent.name}: {rel}")
    return missing


@pytest.mark.req("REQ-072")
def test_paths_in_the_fixture_skills_resolve_inside_the_output(fx):
    fx.extract()
    assert skill_paths_that_do_not_resolve(fx.out) == []


@pytest.mark.req("REQ-072")
def test_the_path_scan_can_fail(fx):
    fx.extract()
    p = fx.out / ".claude/skills/pre-pr-check/SKILL.md"
    p.write_text(p.read_text() + "\nSee `tools/nothing-here.py`.\n")
    assert skill_paths_that_do_not_resolve(fx.out) == ["pre-pr-check: tools/nothing-here.py"]


@pytest.mark.req("REQ-073")
@pytest.mark.parametrize("rel", ["static/calibration/README.md", "static/calibration/_answers/README.md"])
def test_calibration_readmes_say_in_the_first_paragraph_that_answers_are_public(rel):
    first = (ROOT / rel).read_text(encoding="utf-8").split("\n\n")[1].lower()
    assert "answers are public" in first
    assert "demonstration only" in first


@pytest.mark.req("REQ-073")
def test_the_fixture_output_carries_the_static_readmes_not_the_private_one(fx):
    fx.extract()
    assert "demonstration only" in (fx.out / "calibration/README.md").read_text()
    assert "demonstration only" in (fx.out / "calibration/_answers/README.md").read_text()


@pytest.mark.req("REQ-002")
def test_manifest_matches_the_tree_on_the_fixture(fx):
    fx.extract()
    r = run("extract.py", "--verify-manifest", "--out", fx.out)
    assert r.returncode == 0, r.stdout + r.stderr


@pytest.mark.req("REQ-002")
def test_a_planted_hand_edit_fails_the_manifest_check(fx):
    fx.extract()
    (fx.out / "CLAUDE.md").write_text("edited by hand\n")
    r = run("extract.py", "--verify-manifest", "--out", fx.out)
    assert r.returncode == 1
    assert "CLAUDE.md" in r.stdout


@pytest.mark.req("REQ-002")
def test_a_missing_and_an_extra_file_fail_the_manifest_check(fx):
    fx.extract()
    (fx.out / "tools/scrub.py").unlink()
    (fx.out / "stray.md").write_text("stray\n")
    r = run("extract.py", "--verify-manifest", "--out", fx.out)
    assert r.returncode == 1
    assert "tools/scrub.py" in r.stdout and "stray.md" in r.stdout


@pytest.mark.req("REQ-002")
def test_the_published_method_folder_matches_its_manifest():
    r = run("extract.py", "--verify-manifest", "--out", ROOT / "method")
    assert r.returncode == 0, r.stdout + r.stderr


@pytest.mark.req("REQ-002")
def test_top_level_layout():
    for name in ("method", "static", "scripts", "tests", "docs", "extract.toml"):
        assert (ROOT / name).exists(), name


@pytest.mark.req("REQ-050")
def test_example_build_is_static_synthetic_and_names_no_real_repository():
    targets = {e["target"]: e for e in SHIPPED["entry"]}
    for t in ("method/PLAN.md", "method/builds/00-example/BUILD.md", "method/builds/00-example/SESSIONS.md"):
        assert targets[t]["kind"] == "static"
    sessions = (ROOT / "static/builds/00-example/SESSIONS.md").read_text()
    assert len(re.findall(r"^- \[.\] \*\*", sessions, re.M)) == 2
    for name in ("inkproof", "german-b1-tutor", "ampaduchris", "agent-postmortems", "direct-and-approve"):
        for rel in ("static/PLAN.md", "static/builds/00-example/BUILD.md", "static/builds/00-example/SESSIONS.md"):
            assert name not in (ROOT / rel).read_text(), (name, rel)
    assert "example" in (ROOT / "static/builds/00-example/BUILD.md").read_text().lower()


INVENTED = ("Mara Example", "example-project", "example-colleague", "example-client", "example-employer")


@pytest.mark.req("REQ-080")
def test_no_denylist_file_is_in_the_tree_and_the_example_list_is_invented():
    found = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("denylist*.txt")
             if ".venv" not in p.parts and "fixtures" not in p.parts}
    assert found == {"static/private/denylist.example.txt", "method/private/denylist.example.txt"}
    for rel in sorted(found):
        entries = [l.strip() for l in (ROOT / rel).read_text().splitlines() if l.strip() and not l.startswith("#")]
        assert entries and all(e in INVENTED for e in entries), (rel, entries)
