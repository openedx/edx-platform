"""
Convenience methods for working with datetime objects
"""
from datetime import timedelta
from django.utils.translation import ugettext as _
import logging
import datetime
from django.utils.timezone import activate
from django.conf import settings
from pytz import timezone as timezone2
from django.template.defaultfilters import date as _date

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
        return u""
    timezone = u""

#    dt = dt.replace(tzinfo=None)
    if show_timezone:
        if dt.tzinfo is not None:
#            logging.info("trying to make goog timezone from " + dt.tzinfo.tzname(dt))
#            logging.info(datetime.datetime.now().strftime(u"%z"))
            try:
                timezone = u" " + dt.tzinfo.tzname(dt)
            except NotImplementedError:
                timezone = dt.strftime('%z')
                logging.exception("Ahtung")
            settings_time_zone = timezone2(settings.TIME_ZONE)
            dt = dt.astimezone(settings_time_zone)
        else:
            logging.info("bad timezone UTC")
            timezone = u" UTC"
    return unicode(_date(dt, "l, j F Y H:i e "))


def almost_same_datetime(dt1, dt2, allowed_delta=timedelta(minutes=1)):
    """
    Returns true if these are w/in a minute of each other. (in case secs saved to db
    or timezone aren't same)

    :param dt1:
    :param dt2:
    """
    return abs(dt1 - dt2) < allowed_delta
