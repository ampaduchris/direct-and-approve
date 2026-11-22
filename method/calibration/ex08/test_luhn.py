import pytest

from luhn import luhn_ok


@pytest.mark.req("REQ-001")
@pytest.mark.parametrize("digits, expected", [
    ("79927398713", True),
    ("79927398710", False),
    ("4539578763621486", True),
])
def test_luhn_checksum(digits, expected):
    assert luhn_ok(digits) is expected


@pytest.mark.req("REQ-002")
def test_non_digits_rejected():
    assert luhn_ok("7992 7398 713") is False
    assert luhn_ok("12a4") is False
