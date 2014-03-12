"""
Mixin defining common Studio functionality
"""

import datetime
import functools

from xblock.fields import Scope, Field, Integer, XBlockMixin
from xblock.runtime import NoSuchViewError


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


class CmsBlockMixin(XBlockMixin):
    """
    Mixin with fields common to all blocks in Studio
    """
    published_date = DateTuple(help="Date when the module was published", scope=Scope.settings)
    published_by = Integer(help="Id of the user who published this module", scope=Scope.settings)

    def studio_preview_view(self, context):
        """
        Renders Studio's preview of a component when rendering an xblock and its children.
        The default implementation just renders the student view.
        """
        view_function = self.get_view_function('student_view')
        return view_function(context)

    # TODO this shared function should be moved into xblock itself and reused by xblock/runtime.py.
    def get_view_function(self, view_name):
        """
        Returns the view function for the specified view name. If the requested view doesn't exist,
        the fallback view is used instead.
        """
        view_fn = getattr(self, view_name, None)
        if view_fn is None:
            view_fn = getattr(self, "fallback_view", None)
            if view_fn is None:
                raise NoSuchViewError(self, view_name)
            view_fn = functools.partial(view_fn, view_name)
        return view_fn
