"""
All utility methods related to date and time
"""
from calendar import month_name
from datetime import datetime


def month_choices(default_title=None):
    """
    Create choices for all the months, with complete name, in ascending order. i.e. [(1, January) ... (12, December)]

    Returns:
        default_title (str): The default title i.e. Month
        list: Choice in a list of tuples
    """
    choices = [(index, month_name[index]) for index in range(1, 13)]

    if default_title:
        choices.insert(0, (None, default_title))

    return choices


def year_choices(from_year=1900, default_title=None):
    """
    Create choices for all the years from `from_year` to current year, in descending order. If `from_year` is not
    provided then range will start from 1900 i.e. [(2020, 2020) ... (1900, 1900)]

    Args:
        default_title (str): The default title i.e. Year
        from_year (int): Optional, range from current year to this year; defaults to 1900

    Returns:
        list: Choice in a list of tuples
    """
    current_year = datetime.today().year

    if from_year > current_year:
        raise ValueError('Invalid from year {from_year}, it must be less than {current_year}'.format(
            from_year=from_year, current_year=current_year)
        )

    choices = [(year, year) for year in range(current_year, (from_year - 1), -1)]

    if default_title:
        choices.insert(0, (None, default_title))

    return choices
