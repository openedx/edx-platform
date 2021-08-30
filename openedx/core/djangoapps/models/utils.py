"""
Util methods
"""
import datetime
from pytz import UTC


def subtract_deadline_delta(end, delta):
    deadline = end - datetime.timedelta(days=delta)
    deadline = deadline.replace(hour=23, minute=59, second=59, tzinfo=UTC)
    return deadline
