import pytest

from notes import shorten

LONG = "alpha beta gamma delta " * 6


@pytest.mark.req("REQ-001")
def test_long_note_cut():
    out = shorten(LONG)
    assert len(out) == 80
    assert out == LONG[:80]


@pytest.mark.req("REQ-002")
def test_short_note_unchanged():
    assert shorten("call back on Monday") == "call back on Monday"
