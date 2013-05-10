"""
Namespace defining common fields used by Studio for all blocks
"""

import datetime

from xblock.core import ModelType, Namespace


class DateTuple(ModelType):
    """
    ModelType that stores datetime objects as time tuples
    """
    def from_json(self, value):
        return datetime.datetime(*value[0:6])

    def to_json(self, value):
        if value is None:
            return None

        return list(value.timetuple())

class CmsNamespace(Namespace):
    """
    Namespace with fields common to all blocks in Studio
    """
    pass
