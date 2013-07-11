"""
Convenience methods for working with datetime objects
"""

import datetime
def get_default_time_display(dt, show_timezone=True):
    """
    Converts a datetime to a string representation. This is the default
    representation used in Studio and LMS.
    It is of the form "Apr 09, 2013 at 16:00" or "Apr 09, 2013 at 16:00 UTC",
    depending on the value of show_timezone.

    If None is passed in for dt, an empty string will be returned.
    The default value of show_timezone is True.
    """
    if dt is None:
        return ""
    timezone = ""
    if show_timezone:
        if dt.tzinfo is not None:
            try:
                timezone = " " + dt.tzinfo.tzname(dt)
            except NotImplementedError:
                timezone = dt.strftime('%z')
        else:
            timezone = " UTC"
    return dt.strftime("%b %d, %Y at %H:%M") + timezone


def almost_same_datetime(dt1, dt2, allowed_delta=datetime.timedelta(minutes=1)):
    """
    Returns true if these are w/in a minute of each other. (in case secs saved to db
    or timezone aren't same)

    :param dt1:
    :param dt2:
    """
    return abs(dt1 - dt2) < allowed_delta
