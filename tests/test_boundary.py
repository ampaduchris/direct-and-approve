"""Privacy boundary (spec section 15, REQ-111 and REQ-112)."""

from __future__ import annotations

import pytest

from helpers import ROOT, run

MAPPING = """[forbidden]
patterns = ['/Users/', '/home/', 'secret-marker']

[boundary]
forbidden_paths = ["**/denylist.txt", "**/settings.local.json", "**/private/**", "method/builds/*"]
allow_paths = ["method/private/denylist.example.txt", "method/builds/00-example", "method/builds/00-example/*", "tests/fixtures/**"]
pattern_allowlist = ["tests/fixtures/**", "extract.toml"]
"""


@pytest.fixture
def tree(tmp_path):
    (tmp_path / "extract.toml").write_text(MAPPING)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/a.md").write_text("A clean document.\n")
    (tmp_path / "method/private").mkdir(parents=True)
    (tmp_path / "method/private/denylist.example.txt").write_text("Mara Example\n")
    (tmp_path / "method/builds/00-example").mkdir(parents=True)
    (tmp_path / "method/builds/00-example/SESSIONS.md").write_text("# Sessions\n")
    return tmp_path


def boundary(root):
    return run("boundary.py", "--root", root)


@pytest.mark.req("REQ-111")
def test_clean_tree_passes_and_the_example_list_and_example_build_are_allowed(tree):
    r = boundary(tree)
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.startswith("boundary: OK")


@pytest.mark.req("REQ-111")
@pytest.mark.parametrize("rel", [
    "denylist.txt",
    "method/denylist.txt",
    ".claude/settings.local.json",
    "private/notes.md",
    "method/private/notes.md",
    "method/builds/05-site/BUILD.md",
], ids=["denylist", "nested-denylist", "local-settings", "private-folder", "method-private", "real-build"])
def test_a_planted_forbidden_path_fails(tree, rel):
    p = tree / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("x\n")
    r = boundary(tree)
    assert r.returncode == 1
    assert rel.split("/")[0] in r.stdout or rel in r.stdout


@pytest.mark.req("REQ-111")
def test_an_empty_forbidden_folder_fails_too(tree):
    (tree / "method/builds/06-notes").mkdir()
    assert boundary(tree).returncode == 1


@pytest.mark.req("REQ-111")
def test_git_and_virtualenv_folders_are_skipped(tree):
    for d in (".git", ".venv"):
        (tree / d / "private").mkdir(parents=True)
        (tree / d / "private/x.txt").write_text("/Users/someone\n")
    assert boundary(tree).returncode == 0


@pytest.mark.req("REQ-112")
def test_a_planted_marker_in_docs_fails_with_path_and_line_but_not_the_text(tree):
    (tree / "docs/b.md").write_text("fine\nsee /Users/zed/x\n")
    r = boundary(tree)
    assert r.returncode == 1
    assert "docs/b.md:2" in r.stdout
    assert "zed" not in r.stdout + r.stderr


@pytest.mark.req("REQ-112")
def test_the_patterns_run_over_every_text_file_not_only_method(tree):
    (tree / "scripts").mkdir()
    (tree / "scripts/x.py").write_text("# secret-marker\n")
    (tree / "method/CLAUDE.md").write_text("secret-marker\n")
    r = boundary(tree)
    assert r.returncode == 1
    assert "scripts/x.py:1" in r.stdout and "method/CLAUDE.md:1" in r.stdout


@pytest.mark.req("REQ-112")
def test_the_fixture_allowlist_is_honoured_and_binary_files_are_skipped(tree):
    (tree / "tests/fixtures/fx").mkdir(parents=True)
    (tree / "tests/fixtures/fx/planted.md").write_text("/home/zed secret-marker\n")
    (tree / "tests/fixtures/fx/private").mkdir()
    (tree / "tests/fixtures/fx/private/x.txt").write_text("x\n")
    (tree / "docs/blob.bin").write_bytes(b"\xff\xfe/Users/\x00")
    assert boundary(tree).returncode == 0


@pytest.mark.req("REQ-112")
def test_a_missing_or_broken_mapping_exits_3(tmp_path):
    assert boundary(tmp_path).returncode == 3
    (tmp_path / "extract.toml").write_text("not [valid")
    assert boundary(tmp_path).returncode == 3


@pytest.mark.req("REQ-111")
def test_the_repository_tree_passes():
    r = run("boundary.py", "--root", ROOT)
    assert r.returncode == 0, r.stdout + r.stderr
