"""
Utils functions for ondemand_email_preferences app
"""
from datetime import timedelta


def get_next_date(initial_date, no_of_days):
    """
    Returns date by adding no_of_days in initial_date

    Arguments:
        initial_date (date): Date object that represents initial date
        no_of_days (int): Number of days

    Returns:
        string: Date in string format by adding no_of_days in initial_date
    """
    return str(initial_date + timedelta(days=no_of_days))
