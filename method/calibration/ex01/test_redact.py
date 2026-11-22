import pytest

from redact import redact


@pytest.mark.req("REQ-001", "REQ-002")
def test_redact_report():
    out = redact("Anna met anna.", ["anna"])
    assert set(out) == {"text", "count"}
    assert isinstance(out["count"], int)
    assert "[X]" in out["text"]


@pytest.mark.req("REQ-001")
def test_redact_two_terms():
    out = redact("Ben wrote to Anna.", ["anna", "ben"])
    assert out["text"].count("[X]") >= 1
