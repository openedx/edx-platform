"""Utility functions and classes for track backends"""


import json
from datetime import date, datetime
from openedx.core.lib.time_zone_utils import get_utc_timezone


class DateTimeJSONEncoder(json.JSONEncoder):
    """JSON encoder aware of datetime.datetime and datetime.date objects"""

    def default(self, obj):  # lint-amnesty, pylint: disable=arguments-differ, method-hidden
        """
        Serialize datetime and date objects of iso format.

        datatime objects are converted to UTC.
        """

        if isinstance(obj, datetime):
            if obj.tzinfo is None:
                # Localize to UTC naive datetime objects
                obj = obj.replace(tzinfo=get_utc_timezone())  # lint-amnesty, pylint: disable=no-value-for-parameter
            else:
                # Convert to UTC datetime objects from other timezones
                obj = obj.astimezone(get_utc_timezone())
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()

        return super().default(obj)  # lint-amnesty, pylint: disable=super-with-arguments
