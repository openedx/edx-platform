"""
ADG LMS Helpers
"""
import pytz


def get_user_first_name(user):
    """
    Get First name of the user, Checks if first name is available otherwise
    splits full name to get the first name.
    Args:
        user: Auth User instance
    Returns:
        (str) first name of the user

    """
    return user.first_name or user.profile.name.split()[0]


def convert_date_time_zone_and_format(date_time_object, time_zone, time_format):
    """
    Change time zone of datetime object and return a formatted string
    Args:
        date_time_object (datetime.datetime): datetime object
        time_zone (string): a time zone string
        time_format (string): a time format string
    Returns:
        DateTime(string)
    """
    return date_time_object.astimezone(pytz.timezone(time_zone)).strftime(time_format)
