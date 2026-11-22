import pytest

from digits import hide_digits

LINES = [
    "Card 4111 1111 1111 111",
    "Ref 12-345",
    "Tel 030 123456",
]


@pytest.fixture
def digit_lines():
    return [line for line in LINES if line.isdigit()]


@pytest.mark.req("REQ-001")
def test_no_digit_survives(digit_lines):
    for line in digit_lines:
        hidden = hide_digits(line)
        assert not any(ch.isdigit() for ch in hidden)


@pytest.mark.req("REQ-002")
def test_line_without_digits_unchanged():
    assert hide_digits("no numbers here") == "no numbers here"
