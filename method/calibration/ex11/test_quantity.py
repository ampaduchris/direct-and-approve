import pytest

from quantity import parse_quantity


@pytest.mark.req("REQ-001")
def test_quantity_read():
    assert parse_quantity(" 12 ") == 12


@pytest.mark.req("REQ-002")
def test_zero_and_negative_rejected():
    for bad in (0, -3):
        with pytest.raises(Exception):
            parse_quantity(bad)
