"""
Mixin defining common Studio functionality
"""

import datetime
import dateutil.parser
import warnings

from xblock.fields import Scope, Field, Integer, XBlockMixin


class DateTuple(Field):
    """
    Field that stores datetime objects as time tuples
    """
    def from_json(self, value):
        return datetime.datetime(*value[0:6])

    def to_json(self, value):
        if not value:
            if value != None:
                warnings.warn("If time is not set, use Python None", RuntimeWarning)
            return None

        # By runtime specification, this should never happen.  Since
        # it did happen, we want an appropriate sanity-check, by:
        #   http://en.wikipedia.org/wiki/Robustness_principle
        #
        # We could see this issue on export/import of an
        # AnimationXBlock.  TODO: Figure out whether this is
        # happening, and if so, why this happened (6/18/14).
        if isinstance(value, basestring): 
            value = dateutil.parser.parse(value)
            warnings.warn("Date should be a datetime object, not a string.", RuntimeWarning) 

        return list(value.timetuple())


class CmsBlockMixin(XBlockMixin):
    """
    Mixin with fields common to all blocks in Studio
    """
    published_date = DateTuple(help="Date when the module was published", scope=Scope.settings)
    published_by = Integer(help="Id of the user who published this module", scope=Scope.settings)
