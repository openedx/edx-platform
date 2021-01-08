"""
Unit test for date utilities
"""
import pytest
from mock import patch

from openedx.adg.lms.utils.date_utils import day_choices, month_choices, year_choices


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


@pytest.mark.parametrize('default_title', [None, 'Day'])
def test_day_choices(default_title):
    """
    Test month choice list.
    """
    choices = [
        (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10), (11, 11), (12, 12),
        (13, 13), (14, 14), (15, 15), (16, 16), (17, 17), (18, 18), (19, 19), (20, 20), (21, 21), (22, 22),
        (23, 23), (24, 24), (25, 25), (26, 26), (27, 27), (28, 28), (29, 29), (30, 30), (31, 31)
    ]

    if default_title:
        choices.insert(0, (None, default_title))

    assert choices == day_choices(default_title=default_title)
