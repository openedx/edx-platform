"""
Tests for generate_course_blocks management command.
"""
from django.core.management.base import CommandError
from mock import patch

from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from .. import generate_course_blocks
from ....tests.helpers import is_course_in_block_structure_cache


class TestGenerateCourseBlocks(ModuleStoreTestCase):
    """
    Tests generate course blocks management command.
    """
    def setUp(self):
        """
        Create courses in modulestore.
        """
        super(TestGenerateCourseBlocks, self).setUp()
        self.course_1 = CourseFactory.create()
        self.course_2 = CourseFactory.create()
        self.command = generate_course_blocks.Command()

    def _assert_courses_not_in_block_cache(self, *courses):
        """
        Assert courses don't exist in the course block cache.
        """
        for course_key in courses:
            self.assertFalse(is_course_in_block_structure_cache(course_key, self.store))

    def _assert_courses_in_block_cache(self, *courses):
        """
        Assert courses exist in course block cache.
        """
        for course_key in courses:
            self.assertTrue(is_course_in_block_structure_cache(course_key, self.store))

    def test_generate_all(self):
        self._assert_courses_not_in_block_cache(self.course_1.id, self.course_2.id)
        self.command.handle(all=True)
        self._assert_courses_in_block_cache(self.course_1.id, self.course_2.id)

    def test_generate_one(self):
        self._assert_courses_not_in_block_cache(self.course_1.id, self.course_2.id)
        self.command.handle(unicode(self.course_1.id))
        self._assert_courses_in_block_cache(self.course_1.id)
        self._assert_courses_not_in_block_cache(self.course_2.id)

    @patch('lms.djangoapps.course_blocks.management.commands.generate_course_blocks.log')
    def test_generate_no_dags(self, mock_log):
        self.command.handle(dags=True, all=True)
        self.assertEquals(mock_log.warning.call_count, 0)

    @patch('lms.djangoapps.course_blocks.management.commands.generate_course_blocks.log')
    def test_generate_with_dags(self, mock_log):
        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred):
            item1 = ItemFactory.create(parent=self.course_1)
            item2 = ItemFactory.create(parent=item1)
            item3 = ItemFactory.create(parent=item1)
            item2.children.append(item3.location)
            self.store.update_item(item2, ModuleStoreEnum.UserID.mgmt_command)
            self.store.publish(self.course_1.location, ModuleStoreEnum.UserID.mgmt_command)

        self.command.handle(dags=True, all=True)
        self.assertEquals(mock_log.warning.call_count, 1)

    @patch('lms.djangoapps.course_blocks.management.commands.generate_course_blocks.log')
    def test_not_found_key(self, mock_log):
        self.command.handle('fake/course/id', all=False)
        self.assertTrue(mock_log.exception.called)

    def test_invalid_key(self):
        with self.assertRaises(CommandError):
            self.command.handle('not/found', all=False)

    def test_no_params(self):
        with self.assertRaises(CommandError):
            self.command.handle(all=False)
