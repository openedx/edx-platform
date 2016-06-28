"""
Utilities related to timezones
"""
from datetime import datetime, timedelta

from pytz import common_timezones, timezone, utc


def get_user_time_zone(user):
    """
    Returns pytz time zone object of the user's time zone if available or UTC time zone if unavailable
    """
    #TODO: exception for unknown timezones?
    tz = user.preferences.model.get_value(user, "time_zone")
    if tz is not None:
        return timezone(tz)
    return utc


def _format_time_zone_string(time_zone, format_string):
    """
    Returns a string, specified by format string, of the current date/time of the time zone.

    :param time_zone: Pytz time zone object
    :param format_string: A list of format codes can be found at:
            https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior
    """
    return datetime.now(utc).astimezone(time_zone).strftime(format_string)


def _is_daylight_savings_time(time_zone):
    """
    Returns a bool whether or not a time zone is currently in Daylight Savings Time. Useful in determining
    which time zone to show user (e.g. EST or EDT) during ambiguous time periods.

    :param time_zone: Pytz time zone object
    """
    now = utc.localize(datetime.now())
    return now.astimezone(time_zone).dst() != timedelta(0)


def get_formatted_time_zone(time_zone, **kwargs):
    """
    Returns a formatted time zone (e.g. 'Asia/Tokyo (JST, UTC+0900)') by default or just time zone
    abbreviation (e.g. JST) or utc offset (e.g. +0900), if specified

    :param time_zone: Pytz time zone object
    """
    tz_abbr = _format_time_zone_string(time_zone, '%Z')
    tz_offset = _format_time_zone_string(time_zone, '%z')
    if 'abbr' in kwargs:
        return tz_abbr
    elif 'offset' in kwargs:
        return tz_offset
    return "{name} ({abbr}, UTC{offset})".format(name=time_zone, abbr=tz_abbr, offset=tz_offset).replace("_", " ")


TIME_ZONE_CHOICES = [
    (tz, get_formatted_time_zone(timezone(tz))) for tz in common_timezones
]
