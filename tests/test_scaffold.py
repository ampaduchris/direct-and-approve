"""Scaffold checks (session 9.1). REQ-001 is proved here; the rest follow in 9.2 and 9.3."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FILES = [
    "docs/spec.md",
    "docs/BUILD-LOG.md",
    "docs/DEVIATIONS.md",
    "CLAUDE.md",
    "README.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "LICENSE",
    ".github/pull_request_template.md",
    "portfolio.yml",
]

PORTFOLIO_FIELDS = [
    "name", "pitch", "stack", "tests", "release", "released_on",
    "demo_url", "repo_url", "example_pr_url",
]


@pytest.mark.req("REQ-001")
@pytest.mark.parametrize("name", REQUIRED_FILES)
def test_required_file_is_present_and_not_empty(name):
    path = ROOT / name
    assert path.is_file(), f"{name} is missing"
    assert path.read_text(encoding="utf-8").strip(), f"{name} is empty"


@pytest.mark.req("REQ-001")
def test_portfolio_yml_has_every_field():
    text = (ROOT / "portfolio.yml").read_text(encoding="utf-8")
    keys = {line.split(":", 1)[0] for line in text.splitlines() if ":" in line and not line.startswith(" ")}
    assert set(PORTFOLIO_FIELDS) <= keys, sorted(set(PORTFOLIO_FIELDS) - keys)


@pytest.mark.req("REQ-001")
def test_readme_carries_the_disclosure_line():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Built by directing Claude Code. No hand-written code." in text
