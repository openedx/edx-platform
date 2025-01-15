"""
Tests for upstream downstream tracking links.
"""

from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError

from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class TestRecreateUpstreamLinks(ModuleStoreTestCase, CacheIsolationTestCase):
    """
    Test recreate_upstream_links management command.
    """

    ENABLED_SIGNALS = ['course_deleted', 'course_published']

    def call_command(self, *args, **kwargs):
        """
        call command with pass args.
        """
        out = StringIO()
        kwargs['stdout'] = out
        call_command('recreate_upstream_links', *args, **kwargs)
        return out

    def test_call_with_invalid_args(self):
        """
        Test command with invalid args.
        """
        with self.assertRaisesRegex(CommandError, 'Either --course or --all argument'):
            self.call_command()
        with self.assertRaisesRegex(CommandError, 'Only one of --course or --all argument'):
            self.call_command('--all', '--course', 'some-course')

    @patch(
        'openedx.core.djangoapps.content_libraries.management.commands.recreate_upstream_links.create_or_update_upstream_links'
    )
    def test_call_for_single_course(self, mock_task):
        """
        Test command with single course argument
        """
        self.call_command('--course', 'some-course')
        mock_task.delay.assert_called_with('some-course', False)
        # call with --force
        self.call_command('--course', 'some-course', '--force')
        mock_task.delay.assert_called_with('some-course', True)

    @patch(
        'openedx.core.djangoapps.content_libraries.management.commands.recreate_upstream_links.create_or_update_upstream_links'
    )
    def test_call_for_multiple_course(self, mock_task):
        """
        Test command with multiple course arguments
        """
        self.call_command('--course', 'some-course', '--course', 'one-more-course')
        mock_task.delay.assert_any_call('some-course', False)
        mock_task.delay.assert_any_call('one-more-course', False)

    @patch(
        'openedx.core.djangoapps.content_libraries.management.commands.recreate_upstream_links.create_or_update_upstream_links'
    )
    def test_call_for_all_courses(self, mock_task):
        """
        Test command with multiple course arguments
        """
        course_key_1 = CourseFactory.create(emit_signals=True).id
        course_key_2 = CourseFactory.create(emit_signals=True).id
        self.call_command('--all')
        mock_task.delay.assert_any_call(str(course_key_1), False)
        mock_task.delay.assert_any_call(str(course_key_2), False)
