"""
Namespace defining common fields used by Studio for all blocks
"""

import datetime

from xblock.core import Namespace, Scope, ModelType, String
from xmodule.fields import StringyBoolean, DateTime


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
    edited_on = DateTime(help="Date when the version was saved",
        scope=Scope.content)
    edited_by = String(help="Id of the user who last saved this module",
        scope=Scope.content)
    previous_version = String(help="The id of the previous version",
        scope=Scope.content)
    original_version = String(help="The id of the original version",
        scope=Scope.content)
    # TODO figure out how to more generally handle :-( Very kludgey to have an
    # attr on all instances just to support the yaml
    empty = StringyBoolean(help="Whether this is an empty template",
        scope=Scope.settings, default=False)
