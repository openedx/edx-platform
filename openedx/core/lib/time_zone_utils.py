"""
Utilities related to timezones
"""

from datetime import datetime

from pytz import common_timezones, timezone, utc


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


def get_display_time_zone(time_zone_name):
    """
    Returns a formatted display time zone (e.g. 'Asia/Tokyo (JST, UTC+0900)')

    :param time_zone_name (str): Name of Pytz time zone
    """
    time_zone = timezone(time_zone_name)
    tz_abbr = get_time_zone_abbr(time_zone)
    tz_offset = get_time_zone_offset(time_zone)

    return u"{name} ({abbr}, UTC{offset})".format(name=time_zone, abbr=tz_abbr, offset=tz_offset).replace("_", " ")


TIME_ZONE_CHOICES = sorted(
    [(tz, get_display_time_zone(tz)) for tz in common_timezones],
    key=lambda tz_tuple: tz_tuple[1]
)
