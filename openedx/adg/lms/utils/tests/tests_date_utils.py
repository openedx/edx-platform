"""
Unit test for date utilities
"""
import pytest
from mock import patch

from openedx.adg.lms.utils.date_utils import month_choices, year_choices


@pytest.mark.parametrize('default_title', [None, 'Month'])
def test_month_choices(default_title):
    """
    Test month choice list.
    """
    choices = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'), (5, 'May'), (6, 'June'), (7, 'July'),
        (8, 'August'), (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]

    if default_title:
        choices.insert(0, (None, default_title))

    assert choices == month_choices(default_title=default_title)


@pytest.mark.parametrize('default_title', [None, 'Year'])
def test_year_choices(default_title):
    """
    Test year choice list between the range of 2017 to 2019.
    """
    choices = [(2019, 2019), (2018, 2018), (2017, 2017)]

    if default_title:
        choices.insert(0, (None, default_title))

    with patch('openedx.adg.lms.utils.date_utils.MAXIMUM_YEAR_OPTION', 2019):
        assert choices == year_choices(from_year=2017, default_title=default_title)


def test_year_choices_raise_value_error():
    """
    Test year choice list and assert that exception is raised if from year is greater than current year.
    """
    with patch('openedx.adg.lms.utils.date_utils.MAXIMUM_YEAR_OPTION', 2019):
        with pytest.raises(ValueError):
            year_choices(2020)
