"""
Utilities related to timezones
"""
from datetime import datetime

from pytz import common_timezones, timezone, utc


def get_user_time_zone(user):
    """
    Returns pytz time zone object of the user's time zone if available or UTC time zone if unavailable
    """
    #TODO: exception for unknown timezones?
    time_zone = user.preferences.model.get_value(user, "time_zone")
    if time_zone is not None:
        return timezone(time_zone)
    return utc


def _format_time_zone_string(time_zone, date_time, format_string):
    """
    Returns a string, specified by format string, of the current date/time of the time zone.

    :param time_zone: Pytz time zone object
    :param date_time: datetime object of date to convert
    :param format_string: A list of format codes can be found at:
            https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior
    """
    return date_time.astimezone(time_zone).strftime(format_string)


def get_time_zone_abbr(time_zone, date_time=None):
    """
    Returns the time zone abbreviation (e.g. EST) of the time zone for given datetime
    """
    date_time = datetime.now(utc) if date_time is None else date_time
    return _format_time_zone_string(time_zone, date_time, '%Z')


def get_time_zone_offset(time_zone, date_time=None):
    """
    Returns the time zone offset (e.g. -0800) of the time zone for given datetime
    """
    date_time = datetime.now(utc) if date_time is None else date_time
    return _format_time_zone_string(time_zone, date_time, '%z')


def get_formatted_time_zone(time_zone):
    """
    Returns a formatted time zone (e.g. 'Asia/Tokyo (JST, UTC+0900)')

    :param time_zone: Pytz time zone object
    """
    tz_abbr = get_time_zone_abbr(time_zone)
    tz_offset = get_time_zone_offset(time_zone)

    return "{name} ({abbr}, UTC{offset})".format(name=time_zone, abbr=tz_abbr, offset=tz_offset).replace("_", " ")


TIME_ZONE_CHOICES = sorted(
    [(tz, get_formatted_time_zone(timezone(tz))) for tz in common_timezones],
    key=lambda tz_tuple: tz_tuple[1]
)
