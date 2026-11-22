"""scripts/trace.py (REQ-120 and DEV-019): untested MUSTs fail it, document-only rows do not."""

from __future__ import annotations

import pytest

from helpers import run

SPEC = """# spec

| Id | Level | Requirement | Proof |
| --- | --- | --- | --- |
| REQ-001 | MUST | A tested thing | T: a test |
| REQ-002 | MUST | A document thing | D: reviewed in a session; not provable in CI |
| REQ-003 | MUST | A mixed thing | D: reviewed; T: a test |
| REQ-004 | MUST | A thing whose proof is by T and a document | D: reviewed; phrases absent, by T |

### 16.1 Scope to requirements

| BUILD.md scope bullet | MUSTs |
| --- | --- |
| S1 | REQ-001, 002, 003, 004 |
"""


def project(tmp_path, tags):
    (tmp_path / "spec.md").write_text(SPEC)
    tests = tmp_path / "tests"
    tests.mkdir()
    body = "".join(f"@pytest.mark.req(\"{t}\")\ndef test_{t[-3:]}(): pass\n" for t in tags)
    (tests / "test_x.py").write_text("import pytest\n" + body)
    return ["--spec", tmp_path / "spec.md", "--tests", tests]


@pytest.mark.req("REQ-120")
def test_a_document_only_must_is_not_counted_as_untested(tmp_path):
    r = run("trace.py", *project(tmp_path, ["REQ-001", "REQ-003", "REQ-004"]))
    assert r.returncode == 0, r.stdout
    assert "REQ-002  MUST     DOC-ONLY" in r.stdout
    assert "0 untested MUST" in r.stdout


@pytest.mark.req("REQ-120")
@pytest.mark.parametrize("missing", ["REQ-001", "REQ-003", "REQ-004"])
def test_an_untested_must_with_a_test_proof_fails_the_script(tmp_path, missing):
    tags = [t for t in ("REQ-001", "REQ-003", "REQ-004") if t != missing]
    r = run("trace.py", *project(tmp_path, tags))
    assert r.returncode == 1
    assert f"{missing}  MUST     NO TEST" in r.stdout
    assert "1 untested MUST" in r.stdout


@pytest.mark.req("REQ-120")
def test_report_only_still_exits_zero(tmp_path):
    r = run("trace.py", "--report-only", *project(tmp_path, []))
    assert r.returncode == 0
