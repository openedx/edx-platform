"""
Tests for 'fetch_course_structures' command
"""
import mock
from django.core.management import call_command

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class TestFetchCourseStructure(ModuleStoreTestCase):
    """
    Tests for `fetch_course_structures` command.
    """

    @mock.patch('philu_commands.management.commands.fetch_course_structures.generate_course_structure')
    def test_fetch_valid_course_structure(self, mock_generate_course_structure):
        """
        Test 'fetch_course_structures' command by passing course ids to command as command options.
        """
        course_1 = CourseFactory.create(display_name='test course 1', run='Testing_course_1')
        course_2 = CourseFactory.create(display_name='test course 2', run='Testing_course_2')

        expected_calls = [
            mock.call(course_1.id),
            mock.call(course_2.id),
        ]

        mock_generate_course_structure.return_value = {}
        call_command('fetch_course_structures', *[course_1.id, course_2.id])

        self.assertEqual(2, mock_generate_course_structure.call_count)
        mock_generate_course_structure.assert_has_calls(expected_calls)

    @mock.patch('philu_commands.management.commands.fetch_course_structures.generate_course_structure')
    def test_fetch_course_structure_with_invalid_course_id(self, mock_generate_course_structure):
        """
        Test 'fetch_course_structures' command by passing invalid course id to command as command options.
        """
        invalid_course_id = 'some_invalid_course_id'
        call_command('fetch_course_structures', *[invalid_course_id])

        assert not mock_generate_course_structure.called
