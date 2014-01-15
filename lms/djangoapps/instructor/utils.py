"""
Helpers for instructor app.
"""

from xmodule.modulestore.django import modulestore

from courseware.model_data import FieldDataCache
from courseware.module_render import get_module


class DummyRequest(object):
    """Dummy request"""

    META = {}

    def __init__(self):
        self.session = {}
        self.user = None
        return

    def get_host(self):
        """Return a default host."""
        return 'edx.mit.edu'

    def is_secure(self):
        """Always insecure."""
        return False


def get_module_for_student(student, course, location):
    """Return the module for the (student, location) using a DummyRequest."""
    request = DummyRequest()
    request.user = student

    descriptor = modulestore().get_instance(course.id, location, depth=0)
    field_data_cache = FieldDataCache([descriptor], course.id, student)
    return get_module(student, request, location, field_data_cache, course.id)
