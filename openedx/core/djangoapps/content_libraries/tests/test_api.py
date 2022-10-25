"""
Tests for Content Library internal api.
"""

import base64
import hashlib
from unittest import mock

from django.test import TestCase

from opaque_keys.edx.keys import (
    CourseKey,
    UsageKey,
)
from opaque_keys.edx.locator import LibraryLocatorV2

from .. import api


class EdxModulestoreImportClientTest(TestCase):
    """
    Tests for course importing APIs.
    """

    def setUp(self):
        """
        Setup mocks and the test client.
        """
        super().setUp()
        self.mock_library = mock.MagicMock()
        self.modulestore_mock = mock.MagicMock()
        self.client = api.EdxModulestoreImportClient(
            modulestore_instance=self.modulestore_mock,
            library=self.mock_library
        )

    def test_instantiate_without_args(self):
        """
        When instantiated without args,
        Then raises.
        """
        with self.assertRaises(ValueError):
            api.EdxModulestoreImportClient()

    def test_import_blocks_from_course_without_course(self):
        """
        Given no course,
        Then raises.
        """
        self.modulestore_mock.get_course.return_value.get_children.return_value = []
        with self.assertRaises(ValueError):
            self.client.import_blocks_from_course('foobar', lambda *_: None)

    @mock.patch('openedx.core.djangoapps.content_libraries.api.create_library_block')
    @mock.patch('openedx.core.djangoapps.content_libraries.api.get_library_block')
    @mock.patch('openedx.core.djangoapps.content_libraries.api.get_library_block_static_asset_files')
    @mock.patch('openedx.core.djangoapps.content_libraries.api.publish_changes')
    @mock.patch('openedx.core.djangoapps.content_libraries.api.set_library_block_olx')
    def test_import_blocks_from_course_on_block_with_olx(
            self,
            mock_set_library_block_olx,
            mock_publish_changes,
            mock_get_library_block_static_asset_files,
            mock_get_library_block,
            mock_create_library_block,
    ):
        """
        Given a course with one block
        When called
        Then extract OLX, write to library and publish.
        """

        usage_key_str = 'lb:foo:bar:foobar:1234'
        library_key_str = 'lib:foo:bar'

        self.client.get_export_keys = mock.MagicMock(return_value=[UsageKey.from_string(usage_key_str)])
        self.client.get_block_data = mock.MagicMock(return_value={'olx': 'fake-olx'})

        mock_create_library_block.side_effect = api.LibraryBlockAlreadyExists
        self.mock_library.library_key = LibraryLocatorV2.from_string(library_key_str)

        self.client.import_blocks_from_course('foobar', lambda *_: None)

        mock_get_library_block.assert_called_once()
        mock_get_library_block_static_asset_files.called_once()
        mock_set_library_block_olx.assert_called_once_with(
            mock.ANY, 'fake-olx')
        mock_publish_changes.assert_called_once()

    @mock.patch('openedx.core.djangoapps.content_libraries.api.create_library_block')
    @mock.patch('openedx.core.djangoapps.content_libraries.api.get_library_block_static_asset_files')
    @mock.patch('openedx.core.djangoapps.content_libraries.api.set_library_block_olx')
    def test_import_block_when_called_twice_same_block_but_different_course(
            self,
            mock_set_library_block_olx,
            mock_get_library_block_static_asset_files,
            mock_create_library_block,
    ):
        """
        Given an block used by one course
        And another block with same id use by a different course
        And import_block() was called on the first block
        When import_block() is called on the second block
        Then create a library block for the second block
        """
        course_key_str = 'block-v1:FakeCourse+FakeOrg+FakeRun+type@a-fake-block-type+block@fake-block-id'

        modulestore_usage_key = UsageKey.from_string(course_key_str)
        expected_course_key_hash = base64.b32encode(
            hashlib.blake2s(
                str(modulestore_usage_key.course_key).encode()
            ).digest()
        )[:16].decode().lower()
        expected_usage_id = f"{modulestore_usage_key.block_id}_c{expected_course_key_hash}"

        self.client.get_block_data = mock.MagicMock()
        self.client.import_block(modulestore_usage_key)

        mock_create_library_block.assert_called_with(
            self.client.library.library_key,
            modulestore_usage_key.block_type,
            expected_usage_id)
        mock_get_library_block_static_asset_files.assert_called_once()
        mock_set_library_block_olx.assert_called_once()


@mock.patch('openedx.core.djangoapps.content_libraries.api.OAuthAPIClient')
class EdxApiImportClientTest(TestCase):
    """
    Tests for EdxApiImportClient.
    """

    LMS_URL = 'https://foobar_lms.example.com/'

    STUDIO_URL = 'https://foobar_studio.example.com/'

    library_key_str = 'lib:foobar_content:foobar_library'

    course_key_str = 'course-v1:AFakeCourse+FooBar+1'

    def create_mock_library(self, *, course_id=None, course_key_str=None):
        """
        Create a library mock.
        """
        mock_library = mock.MagicMock()
        mock_library.library_key = LibraryLocatorV2.from_string(
            self.library_key_str
        )
        if course_key_str is None:
            course_key_str = self.course_key_str
        if course_id is None:
            course_id = CourseKey.from_string(course_key_str)
        type(mock_library).course_id = mock.PropertyMock(return_value=course_id)
        return mock_library

    def create_client(self, *, mock_library=None):
        """
        Create a edX API import client mock.
        """
        return api.EdxApiImportClient(
            self.LMS_URL,
            self.STUDIO_URL,
            'foobar_oauth_key',
            'foobar_oauth_secret',
            library=(mock_library or self.create_mock_library()),
        )

    def mock_oauth_client_response(self, mock_oauth_client, *, content=None, exception=None):
        """
        Setup a mock response for oauth client GET calls.
        """
        mock_response = mock.MagicMock()
        mock_content = None
        if exception:
            mock_response.raise_for_status.side_effect = exception
        if content:
            mock_content = mock.PropertyMock(return_value='foobar_file_content')
            type(mock_response).content = mock_content
        mock_oauth_client.get.return_value = mock_response
        if mock_content:
            return mock_response, mock_content
        return mock_response

    @mock.patch('openedx.core.djangoapps.content_libraries.api.add_library_block_static_asset_file')
    @mock.patch('openedx.core.djangoapps.content_libraries.api.create_library_block')
    @mock.patch('openedx.core.djangoapps.content_libraries.api.get_library_block_static_asset_files')
    @mock.patch('openedx.core.djangoapps.content_libraries.api.publish_changes')
    @mock.patch('openedx.core.djangoapps.content_libraries.api.set_library_block_olx')
    def test_import_block_when_url_is_from_studio(
            self,
            mock_set_library_block_olx,
            mock_publish_changes,
            mock_get_library_block_static_asset_files,
            mock_create_library_block,
            mock_add_library_block_static_asset_file,
            mock_oauth_client_class,
    ):
        """
        Given an block with one asset provided by a studio.
        When import_block() is called on the block.
        Then a GET to the API endpoint is.
        """

        # Setup mocks.

        static_filename = 'foobar_filename'
        static_content = 'foobar_file_content'
        block_olx = 'foobar-olx'
        usage_key = UsageKey.from_string('lb:foo:bar:foobar:1234')
        # We ensure ``export-file`` belongs to the URL.
        asset_studio_url = f"{self.STUDIO_URL}/foo/bar/export-file/foo/bar"
        block_data = {
            'olx': block_olx,
            'static_files': {static_filename: {'url': asset_studio_url}}
        }
        _, mock_content = self.mock_oauth_client_response(
            mock_oauth_client_class.return_value,
            content=static_content,
        )
        mock_create_library_block.return_value.usage_key = usage_key

        # Create client and call.

        client = self.create_client()
        client.get_block_data = mock.MagicMock(return_value=block_data)
        client.import_block(usage_key)

        # Assertions.

        client.get_block_data.assert_called_once_with(usage_key)
        mock_create_library_block.assert_called_once()
        mock_get_library_block_static_asset_files.assert_called_once()
        mock_content.assert_called()
        mock_add_library_block_static_asset_file.assert_called_once_with(
            usage_key,
            static_filename,
            static_content
        )
        mock_set_library_block_olx.assert_called_once_with(
            usage_key,
            block_olx
        )
        mock_publish_changes.assert_not_called()
