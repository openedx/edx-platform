"""
Tests for managent command "importcourseware".
"""


from unittest import mock
from io import StringIO

import ddt

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import LibraryLocatorV2


@ddt.ddt
@mock.patch('openedx.core.djangoapps.content_libraries.management.commands.content_libraries_import.EdxApiClient')
@mock.patch('openedx.core.djangoapps.content_libraries.management.commands.content_libraries_import.contentlib_api')
class ImportCoursewareTest(TestCase):
    """
    Unit tests for importcourseware command.
    """

    library_key_str = 'lib:foo:bar'

    course_key_str = 'course-v1:foo+bar+foobar'

    def call_command(self, *args, **kwds):
        """
        Call command with default test paramters.
        """
        out = StringIO()
        kwds['stdout'] = out
        library_key = kwds.pop('library_key', self.library_key_str)
        course_key = kwds.pop('course_key', self.course_key_str)
        call_command('content_libraries_import', library_key, course_key,
                     'api',
                     '--oauth-creds', 'fake-key', 'fake-secret',
                     *args, **kwds)
        return out

    # pylint: disable=unused-argument
    def test_call_without_library(self, api_mock, edx_class_mock):
        """
        Given library does not exists
        Then raises command error
        """
        from openedx.core.djangoapps.content_libraries.api import ContentLibraryNotFound
        api_mock.ContentLibraryNotFound = ContentLibraryNotFound
        api_mock.get_library.side_effect = ContentLibraryNotFound
        with self.assertRaises(CommandError):
            self.call_command()

    # pylint: disable=unused-argument
    def test_call_without_course(self, api_mock, edx_class_mock):
        """
        Given course does not exist
        Then raises command error
        """
        edx_mock = edx_class_mock.return_value
        edx_mock.get_export_keys.return_value = []
        with self.assertRaises(CommandError):
            self.call_command()

    # pylint: disable=unused-argument
    def test_call_without_content(self, api_mock, edx_class_mock):
        """
        Given course has not content
        Then raises command error
        """
        edx_mock = edx_class_mock.return_value
        edx_mock.get_export_keys.return_value = []
        with self.assertRaises(CommandError):
            self.call_command()

    @ddt.data("drag-and-drop-v2", "problem", "html", "video")
    def test_call_when_block_with_olx(self, block_type, api_mock, edx_class_mock):
        """
        Given a course with one block
        Then extract OLX, write to library and publish.
        """

        usage_key_str = 'lb:foo:bar:foobar:1234'

        edx_mock = edx_class_mock.return_value
        edx_mock.get_export_keys.return_value = [UsageKey.from_string(usage_key_str)]
        edx_mock.get_block_data.return_value = {'olx': 'fake-olx'}

        library_mock = api_mock.get_library.return_value
        library_mock.key = LibraryLocatorV2.from_string(self.library_key_str)

        from openedx.core.djangoapps.content_libraries.api import LibraryBlockAlreadyExists

        api_mock.LibraryBlockAlreadyExists = LibraryBlockAlreadyExists
        api_mock.create_library_block.side_effect = LibraryBlockAlreadyExists

        self.call_command()

        api_mock.get_library_block.assert_called_once()
        api_mock.get_library_block_static_asset_files.assert_not_called()
        api_mock.set_library_block_olx.assert_called_once_with(
            mock.ANY, 'fake-olx')
        api_mock.publish_changes.assert_called_once()
