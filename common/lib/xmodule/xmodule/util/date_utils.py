"""
Convenience methods for working with datetime objects
"""
from datetime import timedelta


def get_default_time_display(dtime):
    """
    Converts a datetime to a string representation. This is the default
    representation used in Studio and LMS.
    It is of the form "Apr 09, 2013 at 16:00 UTC".

    If None is passed in for dt, an empty string will be returned.
    """
    if dtime is None:
        return u""
    if dtime.tzinfo is not None:
        try:
            timezone = u" " + dtime.tzinfo.tzname(dtime)
        except NotImplementedError:
            timezone = dtime.strftime('%z')
    else:
        timezone = u" UTC"
    return unicode(dtime.strftime(u"%b %d, %Y at %H:%M{tz}")).format(
        tz=timezone).strip()


def get_time_display(dtime, format_string=None):
    """
    Converts a datetime to a string representation.

    If None is passed in for dt, an empty string will be returned.

    If the format_string is None, or if format_string is improperly
    formatted, this method will return the value from `get_default_time_display`.

    format_string should be a unicode string that is a valid argument for datetime's strftime method.
    """
    if dtime is None or format_string is None:
        return get_default_time_display(dtime)
    try:
        return unicode(dtime.strftime(format_string))
    except ValueError:
        return get_default_time_display(dtime)


def almost_same_datetime(dt1, dt2, allowed_delta=timedelta(minutes=1)):
    """
    Returns true if these are w/in a minute of each other. (in case secs saved to db
    or timezone aren't same)

    :param dt1:
    :param dt2:
    """
    return abs(dt1 - dt2) < allowed_delta
