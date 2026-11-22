import pytest

from cards import mask_card


@pytest.mark.req("REQ-001")
@pytest.mark.parametrize("given, expected", [
    ("4111 1111 1111 1234", "**** **** **** 1234"),
    ("4111-1111-1111-1234", "****-****-****-1234"),
    ("411111111234", "********1234"),
])
def test_all_but_last_four_masked(given, expected):
    assert mask_card(given) == expected


@pytest.mark.req("REQ-002")
def test_short_number_rejected():
    with pytest.raises(ValueError, match="too few digits"):
        mask_card("1234 5678 901")
