"""
Unit test for date utilities
"""
from datetime import datetime

import pytest
from mock import patch

from openedx.adg.common.util.date_utils import month_choices, year_choices


def test_month_choices():
    """
    Test month choice list.
    """
    choices = [
        ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'), ('5', 'May'), ('6', 'June'), ('7', 'July'),
        ('8', 'August'), ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
    ]
    assert choices == month_choices()


@patch('openedx.adg.common.util.date_utils.datetime')
def test_year_choices(mock_current_year):
    """
    Test year choice list between the range of 2017 to 2019.
    """
    mock_current_year.today.return_value = datetime(2019, 1, 1)
    choices = [(2019, 2019), (2018, 2018), (2017, 2017)]
    assert choices == year_choices(2017)


@patch('openedx.adg.common.util.date_utils.datetime')
def test_year_choices_raise_value_error(mock_current_year):
    """
    Test year choice list and assert that exception is raised if from year is greater than current year.
    """
    mock_current_year.today.return_value = datetime(2019, 1, 1)
    with pytest.raises(ValueError):
        year_choices(2020)
