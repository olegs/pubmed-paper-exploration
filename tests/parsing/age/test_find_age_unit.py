import pytest
from src.parsing.age.get_age import get_age_unit


@pytest.mark.parametrize(
    "text,expected",
    [
        ("age (yr)", "yr"),
        ("age (yrs)", "yr"),
        ("age_days", "day"),
        ("donor_age", None),
        ("age group", None),
        ("age (years)", "year"),
        ("age days", "day"),
        ("age_years", "year"),
        ("age", None)
    ]
)
def test_find_age_unit(text, expected):
    age_unit_found = get_age_unit(text)
    assert age_unit_found == expected
