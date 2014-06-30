"""
Mixin defining common Studio functionality
"""

import datetime

from xblock.fields import Field


class DateTuple(Field):
    """
    DEPRECATED - Use the Date field type instead
    Field that stores datetime objects as time tuples
    """
    def from_json(self, value):
        return datetime.datetime(*value[0:6])

    def to_json(self, value):
        if value is None:
            return None

        return list(value.timetuple())