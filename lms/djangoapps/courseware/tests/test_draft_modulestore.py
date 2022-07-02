"""
Test the draft modulestore
"""


from opaque_keys.edx.keys import CourseKey

from xmodule.modulestore.tests.django_utils import TEST_DATA_MONGO_MODULESTORE, ModuleStoreTestCase


class TestDraftModuleStore(ModuleStoreTestCase):
    """
    Test the draft modulestore
    """
    MODULESTORE = TEST_DATA_MONGO_MODULESTORE

    def test_get_items_with_course_items(self):
        # fix was to allow get_items() to take the course_id parameter
        self.store.get_items(CourseKey.from_string('a/b/c'), qualifiers={'category': 'vertical'})

        # test success is just getting through the above statement.
        # The bug was that 'course_id' argument was
        # not allowed to be passed in (i.e. was throwing exception)
