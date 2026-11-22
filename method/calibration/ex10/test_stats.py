import pytest

from stats import median


@pytest.mark.req("REQ-001")
def test_odd_count():
    assert median([3, 1, 2]) == 2


@pytest.mark.req("REQ-002")
def test_even_count():
    assert median([4, 1, 3, 2]) == 2.5


@pytest.mark.req("REQ-003")
def test_empty_rejected():
    with pytest.raises(ValueError):
        median([])
