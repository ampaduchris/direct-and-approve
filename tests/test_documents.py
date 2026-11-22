"""Document checks (spec REQ-099, REQ-107): the two scripts, on small documents built here."""

from __future__ import annotations

import pytest

from helpers import ROOT, run


@pytest.mark.req("REQ-107")
def test_a_passing_and_a_failing_block(tmp_path):
    good = tmp_path / "good.md"
    good.write_text("text\n\n```bash run\necho hello\n```\n\n```bash\nexit 9\n```\n")
    result = run("run_blocks.py", good)
    assert result.returncode == 0, result.stdout
    assert "1 block(s), 0 failed" in result.stdout
    bad = tmp_path / "bad.md"
    bad.write_text("```bash run\nexit 3\n```\n")
    result = run("run_blocks.py", bad)
    assert result.returncode == 1
    assert "FAIL" in result.stdout


@pytest.mark.req("REQ-107")
def test_a_block_tagged_bash_only_is_never_run(tmp_path):
    doc = tmp_path / "d.md"
    doc.write_text("```bash\ntouch ran-anyway\n```\n")
    assert run("run_blocks.py", doc).returncode == 0
    assert not (ROOT / "ran-anyway").exists()


@pytest.mark.req("REQ-099")
def test_links_and_anchors(tmp_path):
    (tmp_path / "other.md").write_text("# A heading here\n")
    doc = tmp_path / "doc.md"
    doc.write_text("[ok](other.md#a-heading-here) [web](https://example.test/x)\n\n```\n[skip](nowhere.md)\n```\n")
    result = run("check_links.py", doc)
    assert result.returncode == 0, result.stdout
    assert "1 relative link(s) checked, 1 external link(s) not fetched" in result.stdout


@pytest.mark.req("REQ-099")
@pytest.mark.parametrize("link", ["missing.md", "other.md#no-such-heading"])
def test_a_broken_link_fails(tmp_path, link):
    (tmp_path / "other.md").write_text("# Real\n")
    doc = tmp_path / "doc.md"
    doc.write_text(f"[x]({link})\n")
    result = run("check_links.py", doc)
    assert result.returncode == 1
    assert "doc.md:1:" in result.stdout
