"""Time related tools.
"""

from __future__ import print_function
from __future__ import unicode_literals

from calendar import timegm
from datetime import datetime
from pytz import UTC, timezone


utcfromtimestamp = datetime.utcfromtimestamp
utclocalize = UTC.localize
GMT = timezone("GMT")


def datetime_to_epoch(d):
    # type: (datetime) -> int
    """Convert datetime to epoch.
    """
    return timegm(d.utctimetuple())


def epoch_to_datetime(t):
    # type: (int) -> datetime
    """Convert epoch time to a UTC datetime.
    """
    return utclocalize(utcfromtimestamp(t)) if t is not None else None
