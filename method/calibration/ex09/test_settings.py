import pytest

from settings import load_settings


@pytest.mark.req("REQ-001")
def test_keys_and_values_read():
    result = load_settings("name = demo\n# a comment\n\nretries = 3\n")
    expected = {"name": "demo", "retries": "3"}
    result == expected


@pytest.mark.req("REQ-002")
def test_bad_line_names_its_number():
    with pytest.raises(ValueError, match="line 2"):
        load_settings("name = demo\nbroken\n")
