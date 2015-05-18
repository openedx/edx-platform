"""
This file contains implementation override of SearchInitializer which will allow
    * To set initial set of masquerades and other parameters
"""

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from search.initializer import SearchInitializer
from courseware.masquerade import setup_masquerade
from courseware.access import has_access


class LmsSearchInitializer(SearchInitializer):
    """ SearchInitializer for LMS Search """
    def initialize(self, **kwargs):
        if 'request' in kwargs and kwargs['request'] and kwargs['course_id']:
            request = kwargs['request']
            try:
                course_key = CourseKey.from_string(kwargs['course_id'])
            except InvalidKeyError:
                course_key = SlashSeparatedCourseKey.from_deprecated_string(kwargs['course_id'])
            staff_access = has_access(request.user, 'staff', course_key)
            setup_masquerade(request, course_key, staff_access)
