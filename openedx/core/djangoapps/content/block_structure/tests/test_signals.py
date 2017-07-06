"""
Unit tests for the Course Blocks signals
"""

from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from ..api import get_block_structure_manager
from .helpers import is_course_in_block_structure_cache


class CourseBlocksSignalTest(ModuleStoreTestCase):
    """
    Tests for the Course Blocks signal
    """
    def setUp(self):
        super(CourseBlocksSignalTest, self).setUp()
        self.course = CourseFactory.create()
        self.course_usage_key = self.store.make_course_usage_key(self.course.id)

    def test_course_update(self):
        test_display_name = "Lightsabers 101"

        # Course exists in cache initially
        bs_manager = get_block_structure_manager(self.course.id)
        orig_block_structure = bs_manager.get_collected()
        self.assertTrue(is_course_in_block_structure_cache(self.course.id, self.store))
        self.assertNotEqual(
            test_display_name,
            orig_block_structure.get_xblock_field(self.course_usage_key, 'display_name')
        )

        self.course.display_name = test_display_name
        self.store.update_item(self.course, self.user.id)

        # Cached version of course has been updated
        updated_block_structure = bs_manager.get_collected()
        self.assertEqual(
            test_display_name,
            updated_block_structure.get_xblock_field(self.course_usage_key, 'display_name')
        )

    def test_course_delete(self):
        bs_manager = get_block_structure_manager(self.course.id)
        self.assertIsNotNone(bs_manager.get_collected())
        self.assertTrue(is_course_in_block_structure_cache(self.course.id, self.store))

        self.store.delete_course(self.course.id, self.user.id)
        with self.assertRaises(ItemNotFoundError):
            bs_manager.get_collected()

        self.assertFalse(is_course_in_block_structure_cache(self.course.id, self.store))
