"""The workflow and the scripts as spec section 15 and the standard's CI section describe them.

REQ-003, 004, 023, 120 and 121 name a test or a CI job. These tests read the workflow file and the
script sources. They do not run the workflow.
"""

from __future__ import annotations

import ast
import re
import sys

import pytest

from helpers import ROOT, SCRIPTS, run

WORKFLOW = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
SCRIPT_FILES = sorted([*SCRIPTS.glob("*.py"), *(ROOT / "method/tools").glob("*.py")])


def jobs() -> dict[str, str]:
    """Job name to the text of its block, in file order."""
    body = WORKFLOW.split("\njobs:\n", 1)[1]
    parts = re.split(r"^  ([a-z-]+):\n", body, flags=re.M)
    return dict(zip(parts[1::2], parts[2::2]))


# ---- REQ-003 --------------------------------------------------------------------------------------

@pytest.mark.req("REQ-003")
def test_every_script_imports_with_the_standard_library_only():
    done = run("check_imports.py", env={"PATH": "", "PYTHONPATH": ""})
    assert done.returncode == 0, done.stdout + done.stderr
    assert f"{len(SCRIPT_FILES)} script(s), 0 failed" in done.stdout


@pytest.mark.req("REQ-003")
def test_the_scripts_job_installs_nothing_and_runs_check_imports_isolated():
    block = jobs()["scripts"]
    assert "uv sync" not in block and "pip install" not in block
    assert "--no-project" in block and "--isolated" in block and "python -I scripts/check_imports.py" in block
    for version in ("3.11", "3.12", "3.13"):
        assert f'"{version}"' in block


# ---- REQ-004 --------------------------------------------------------------------------------------

NETWORK = {"socket", "ssl", "urllib", "http", "ftplib", "smtplib", "poplib", "imaplib", "telnetlib",
           "xmlrpc", "requests", "httpx", "aiohttp", "anthropic", "openai"}
NETWORK_COMMANDS = {"gh", "curl", "wget"}


def network_use(path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found += [a.name for a in node.names if a.name.split(".")[0] in NETWORK]
        elif isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] in NETWORK:
            found.append(node.module)
        elif isinstance(node, ast.Constant) and node.value in NETWORK_COMMANDS:
            found.append(f"command {node.value}")
    return found


@pytest.mark.req("REQ-004")
def test_no_script_but_snapshot_pr_uses_the_network_or_a_network_command():
    offenders = {p.name: network_use(p) for p in SCRIPT_FILES if p.name != "snapshot_pr.py" and network_use(p)}
    assert offenders == {}
    assert network_use(SCRIPTS / "snapshot_pr.py"), "the one permitted exception must actually be the one that uses gh"


@pytest.mark.req("REQ-004")
def test_the_scan_catches_a_planted_import_and_a_planted_command(tmp_path):
    planted = tmp_path / "bad.py"
    planted.write_text("import urllib.request\nimport subprocess\nsubprocess.run(['curl', 'x'])\n")
    assert network_use(planted) == ["urllib.request", "command curl"]


@pytest.mark.req("REQ-004")
def test_no_workflow_step_runs_snapshot_pr():
    assert "snapshot_pr" not in WORKFLOW


# ---- REQ-023 --------------------------------------------------------------------------------------

DEVIATIONS = (ROOT / "docs/DEVIATIONS.md").read_text(encoding="utf-8")


@pytest.mark.req("REQ-023")
@pytest.mark.parametrize("departure", [
    "R4 (eval harness) does not apply",
    "There is no 60-second recording",
    "no weekly scheduled run",
])
def test_each_known_departure_from_the_standard_has_a_numbered_entry(departure):
    rows = [l for l in DEVIATIONS.splitlines() if re.match(r"\| DEV-\d{3} \|", l)]
    assert any(departure.lower() in r.lower() for r in rows), departure


@pytest.mark.req("REQ-023")
def test_deviation_ids_are_unique_and_in_order():
    ids = re.findall(r"^\| (DEV-\d{3}) \|", DEVIATIONS, re.M)
    assert ids == sorted(set(ids))


# ---- REQ-120 and the CI rows it carries (074, 081, 082, 106) ----------------------------------------

STEPS_IN_ORDER = [
    "Tests",
    "Requirement traceability",
    "Manifest check",
    "Privacy boundary",
    "Scrubber self-test and example-list scan",
    "Calibration proof",
    "Copy method/ outside the repository and run its checks",
    "Blocks marked bash run",
    "Offline link check",
    "gitleaks/gitleaks-action",
]


@pytest.mark.req("REQ-120")
def test_the_workflow_runs_its_steps_in_the_order_the_spec_gives():
    positions = []
    start = 0
    for name in STEPS_IN_ORDER:
        at = WORKFLOW.find(name, start)
        assert at >= 0, f"step {name!r} missing or out of order"
        positions.append(at)
        start = at + 1
    assert positions == sorted(positions)


@pytest.mark.req("REQ-120")
def test_no_step_is_allowed_to_fail_quietly_and_trace_is_not_report_only():
    assert "continue-on-error" not in WORKFLOW
    assert "|| true" not in WORKFLOW
    assert "--report-only" not in WORKFLOW


@pytest.mark.req("REQ-074")
@pytest.mark.req("REQ-120")
def test_the_kit_job_runs_the_calibration_proof_and_fails_on_a_changed_example():
    assert "ci_checks.py kit" in jobs()["kit"]
    source = (SCRIPTS / "ci_checks.py").read_text()
    assert "prove.py" in source and "git" in source and "status" in source and "--porcelain" in source


@pytest.mark.req("REQ-081")
@pytest.mark.req("REQ-082")
@pytest.mark.req("REQ-120")
def test_the_scrub_step_runs_the_self_test_and_the_example_list_scan():
    assert "ci_checks.py scrub" in jobs()["test"]
    source = (SCRIPTS / "ci_checks.py").read_text()
    assert '"--self-test"' in source and "denylist.example.txt" in source


@pytest.mark.req("REQ-106")
@pytest.mark.req("REQ-120")
def test_the_start_your_own_job_runs_three_checks_on_a_copy_outside_the_repository():
    assert "ci_checks.py start-your-own" in jobs()["start-your-own"]
    source = (SCRIPTS / "ci_checks.py").read_text()
    body = source.split("def start_your_own", 1)[1].split("def main", 1)[0]
    assert "TemporaryDirectory" in body
    for name in ("check_sessions.py", "--self-test", "prove.py"):
        assert name in body


# ---- REQ-121 --------------------------------------------------------------------------------------

@pytest.mark.req("REQ-121")
def test_every_action_is_pinned_to_a_full_hash_with_its_release_in_a_comment():
    uses = re.findall(r"^\s+- uses: (\S+)(.*)$", WORKFLOW, re.M)
    assert uses
    for ref, rest in uses:
        assert re.fullmatch(r"[\w.-]+/[\w.-]+@[0-9a-f]{40}", ref), ref
        assert re.search(r"# v\d", rest), (ref, rest)


@pytest.mark.req("REQ-121")
def test_runner_image_is_pinned_and_permissions_are_read_only():
    runners = re.findall(r"runs-on: (\S+)", WORKFLOW)
    assert runners and all(r == "ubuntu-24.04" for r in runners)
    assert re.search(r"^permissions:\n  contents: read\n", WORKFLOW, re.M)
    assert "write" not in WORKFLOW.split("\njobs:\n", 1)[0]


@pytest.mark.req("REQ-121")
def test_test_job_has_a_ten_minute_timeout_a_concurrency_group_and_no_secret():
    assert re.search(r"^concurrency:\n  group: .+\n  cancel-in-progress: true", WORKFLOW, re.M)
    block = jobs()["test"]
    assert "timeout-minutes: 10" in block
    assert "secrets." not in block
    assert "uv sync --locked" in block and "uv run --locked" in block
