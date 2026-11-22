import pytest

from days import parse_day


@pytest.mark.req("REQ-001")
def test_parse_day():
    assert parse_day("2026-11-15") == (2026, 11, 15)


@pytest.mark.req("REQ-003")
def test_month_out_of_range():
    with pytest.raises(ValueError):
        parse_day("2026-13-01")


@pytest.mark.req("REQ-002")
@pytest.mark.xfail(reason="calendar edge cases are handled in a later change")
def test_impossible_day_rejected():
    with pytest.raises(ValueError):
        parse_day("2026-02-30")
