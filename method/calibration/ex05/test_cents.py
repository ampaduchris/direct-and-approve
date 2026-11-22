import pytest

from cents import to_cents


@pytest.mark.req("REQ-001")
def test_to_cents():
    assert to_cents("12.34") == 1234
    assert to_cents("7") == 700
    assert to_cents("12.5") == 1250


@pytest.mark.req("REQ-002")
def test_third_decimal_rejected():
    with pytest.raises(ValueError):
        to_cents("1.234")


@pytest.mark.req("REQ-003")
def test_to_cents():
    assert to_cents("-0.05") == -5
