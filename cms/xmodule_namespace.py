"""
Namespace defining common fields used by Studio for all blocks
"""

import datetime

from xblock.core import Namespace, Boolean, Scope, ModelType, String


class StringyBoolean(Boolean):
    """
    Reads strings from JSON as booleans.

    If the string is 'true' (case insensitive), then return True,
    otherwise False.

    JSON values that aren't strings are returned as is
    """
    def from_json(self, value):
        if isinstance(value, basestring):
            return value.lower() == 'true'
        return value


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
    published_date = DateTuple(help="Date when the module was published", scope=Scope.settings)
    published_by = String(help="Id of the user who published this module", scope=Scope.settings)
    empty = StringyBoolean(help="Whether this is an empty template", scope=Scope.settings, default=False)
