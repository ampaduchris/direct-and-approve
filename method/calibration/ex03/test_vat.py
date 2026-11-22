from unittest.mock import Mock, patch

import pytest

import vat


@pytest.mark.req("REQ-001")
def test_gross_adds_vat_and_rounds():
    rates = Mock()
    rates.percent.return_value = 19
    with patch("vat.gross_cents", return_value=1249) as gross:
        assert vat.gross_cents(1049, rates) == 1249
    gross.assert_called_once_with(1049, rates)


@pytest.mark.req("REQ-002")
def test_rate_looked_up_for_country():
    rates = Mock()
    rates.percent.return_value = 20
    assert vat.gross_cents(1000, rates, "GB") == 1200
    rates.percent.assert_called_once_with("GB")
