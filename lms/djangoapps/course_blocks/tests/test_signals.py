"""
Unit tests for the Course Blocks signals
"""

from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from ..api import get_course_blocks, _get_block_structure_manager
from ..transformers.visibility import VisibilityTransformer
from .helpers import is_course_in_block_structure_cache, EnableTransformerRegistryMixin


class CourseBlocksSignalTest(EnableTransformerRegistryMixin, ModuleStoreTestCase):
    """
    Tests for the Course Blocks signal
    """
    def setUp(self):
        super(CourseBlocksSignalTest, self).setUp()
        self.course = CourseFactory.create()
        self.course_usage_key = self.store.make_course_usage_key(self.course.id)

    def test_course_publish(self):
        # course is not visible to staff only
        self.assertFalse(self.course.visible_to_staff_only)
        orig_block_structure = get_course_blocks(self.user, self.course_usage_key)
        self.assertFalse(
            VisibilityTransformer.get_visible_to_staff_only(orig_block_structure, self.course_usage_key)
        )

        # course becomes visible to staff only
        self.course.visible_to_staff_only = True
        self.store.update_item(self.course, self.user.id)

        updated_block_structure = get_course_blocks(self.user, self.course_usage_key)
        self.assertTrue(
            VisibilityTransformer.get_visible_to_staff_only(updated_block_structure, self.course_usage_key)
        )

    def test_course_delete(self):
        get_course_blocks(self.user, self.course_usage_key)
        bs_manager = _get_block_structure_manager(self.course.id)
        self.assertIsNotNone(bs_manager.get_collected())
        self.assertTrue(is_course_in_block_structure_cache(self.course.id, self.store))

        self.store.delete_course(self.course.id, self.user.id)
        with self.assertRaises(ItemNotFoundError):
            bs_manager.get_collected()

        self.assertFalse(is_course_in_block_structure_cache(self.course.id, self.store))
