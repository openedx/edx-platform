"""
Test the draft modulestore
"""


from django.test import TestCase
from opaque_keys.edx.keys import CourseKey

from xmodule.modulestore.django import modulestore


class TestDraftModuleStore(TestCase):
    """
    Test the draft modulestore
    """

    def test_get_items_with_course_items(self):
        store = modulestore()

        # fix was to allow get_items() to take the course_id parameter
        store.get_items(CourseKey.from_string('a/b/c'), qualifiers={'category': 'vertical'})

        # test success is just getting through the above statement.
        # The bug was that 'course_id' argument was
        # not allowed to be passed in (i.e. was throwing exception)
