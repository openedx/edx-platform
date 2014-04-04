"""
Mixin defining common Studio functionality
"""

import datetime
import time

from xblock.fields import Scope, Field, Integer, XBlockMixin


class DateTuple(Field):
    """
    Field that stores datetime objects as time tuples
    """
    def from_json(self, value):
        return datetime.datetime(*value[0:6])

    def to_json(self, value):
        if value is None:
            return None

        return list(value.timetuple())

    def enforce_type(self, value):
        if isinstance(value, datetime.datetime) or value is None:
            return value

        if isinstance(value, tuple, time.struct_time):
            return self.from_json(DateTuple)

        raise TypeError("Value should be datetime, a timetuple or None, not {}".format(type(value)))


class CmsBlockMixin(XBlockMixin):
    """
    Mixin with fields common to all blocks in Studio
    """
    published_date = DateTuple(help="Date when the module was published", scope=Scope.settings)
    published_by = Integer(help="Id of the user who published this module", scope=Scope.settings)
