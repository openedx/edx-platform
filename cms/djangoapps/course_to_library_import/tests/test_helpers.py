"""
Tests for the course_to_library_import helper functions.
"""

from datetime import datetime, timezone
from unittest import mock


from lxml import etree
from django.db.utils import IntegrityError
from django.test import TestCase
from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import LibraryLocatorV2, LibraryUsageLocatorV2
from openedx_learning.api.authoring_models import ContainerVersion

from cms.djangoapps.course_to_library_import.data import CourseToLibraryImportStatus
from cms.djangoapps.course_to_library_import.helpers import (
    _handle_component_override,
    _process_staged_content_files,
    _update_container_components,
    create_block_in_library,
    create_container,
    import_children,
    import_container,
)
from common.djangoapps.student.tests.factories import UserFactory

from .factories import CourseToLibraryImportFactory


class TestFlatImportChildren(TestCase):
    """
    Tests for the flat_import_children helper function.
    """

    def setUp(self):
        super().setUp()
        self.library_key = LibraryLocatorV2(org="TestOrg", slug="test-lib")
        self.user_id = "test_user"

        self.staged_content = mock.MagicMock()
        self.staged_content.id = "staged-content-id"
        self.staged_content.tags = {
            "block-v1:TestOrg+TestCourse+Run1+type@problem+block@problem1": {},
            "block-v1:TestOrg+TestCourse+Run1+type@html+block@html1": {},
            "block-v1:TestOrg+TestCourse+Run1+type@video+block@video1": {},
        }

    @mock.patch('cms.djangoapps.course_to_library_import.helpers.create_block_in_library')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.ContentLibrary')
    def test_flat_import_children_basic(self, mock_content_library, mock_create_block):
        xml = """
        <vertical url_name="vertical1">
            <problem url_name="problem1"/>
            <html url_name="html1"/>
        </vertical>
        """
        block_to_import = etree.fromstring(xml)

        mock_library = mock.MagicMock()
        mock_content_library.objects.filter.return_value.first.return_value = mock_library

        import_children(block_to_import, self.library_key, self.user_id, self.staged_content, 'xblock', False)

        self.assertEqual(mock_create_block.call_count, 2)

        usage_key_problem = UsageKey.from_string("block-v1:TestOrg+TestCourse+Run1+type@problem+block@problem1")
        usage_key_html = UsageKey.from_string("block-v1:TestOrg+TestCourse+Run1+type@html+block@html1")

        mock_create_block.assert_any_call(
            mock.ANY, usage_key_problem, self.library_key, self.user_id, self.staged_content.id, False
        )
        mock_create_block.assert_any_call(
            mock.ANY, usage_key_html, self.library_key, self.user_id, self.staged_content.id, False
        )

    @mock.patch('cms.djangoapps.course_to_library_import.helpers.create_block_in_library')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.ContentLibrary')
    def test_flat_import_children_with_override(self, mock_content_library, mock_create_block):
        xml = """
        <vertical url_name="vertical1">
            <problem url_name="problem1"/>
        </vertical>
        """
        block_to_import = etree.fromstring(xml)

        mock_library = mock.MagicMock()
        mock_content_library.objects.filter.return_value.first.return_value = mock_library

        import_children(block_to_import, self.library_key, self.user_id, self.staged_content, 'xblock', True)

        usage_key_problem = UsageKey.from_string("block-v1:TestOrg+TestCourse+Run1+type@problem+block@problem1")
        mock_create_block.assert_called_with(
            mock.ANY, usage_key_problem, self.library_key, self.user_id, self.staged_content.id, True
        )

    @mock.patch('cms.djangoapps.course_to_library_import.helpers.ContentLibrary')
    def test_flat_import_children_library_not_found(self, mock_content_library):
        xml = """
        <vertical url_name="vertical1">
            <problem url_name="problem1"/>
        </vertical>
        """
        block_to_import = etree.fromstring(xml)

        mock_content_library.objects.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError):
            import_children(block_to_import, self.library_key, self.user_id, self.staged_content, 'xblock', False)

    @mock.patch('cms.djangoapps.course_to_library_import.helpers.create_block_in_library')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.ContentLibrary')
    def test_flat_import_children_ignores_unmatched_url_names(self, mock_content_library, mock_create_block):
        xml = """
        <vertical url_name="vertical1">
            <problem url_name="problem_not_in_staged_content"/>
        </vertical>
        """
        block_to_import = etree.fromstring(xml)

        mock_library = mock.MagicMock()
        mock_content_library.objects.filter.return_value.first.return_value = mock_library

        import_children(block_to_import, self.library_key, self.user_id, self.staged_content, 'xblock', False)

        mock_create_block.assert_not_called()


class TestCreateBlockInLibrary(TestCase):
    """
    Tests for the create_block_in_library helper function.
    """

    def setUp(self):
        super().setUp()
        self.library_key = LibraryLocatorV2(org="TestOrg", slug="test-lib")
        self.user_id = UserFactory().id
        self.block_id = "problem1"
        self.block_type = "problem"
        self.staged_content_id = "staged-content-id"
        self.usage_key = UsageKey.from_string(
            f"block-v1:TestOrg+TestCourse+Run1+type@{self.block_type}+block@{self.block_id}"
        )

        self.xml_content = "<problem>Test problem content</problem>"
        self.block_to_import = etree.fromstring(self.xml_content)
        self.mock_library = mock.MagicMock()
        self.mock_library.library_key = self.library_key
        self.mock_learning_package = mock.MagicMock()
        self.mock_library.learning_package = self.mock_learning_package

    @mock.patch('cms.djangoapps.course_to_library_import.helpers.content_staging_api')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.authoring_api')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.api')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.ContentLibrary')
    def test_create_block_in_library_new_component(
        self, mock_content_library, mock_api, mock_authoring_api, mock_content_staging_api
    ):
        mock_content_library.objects.get_by_key.return_value = self.mock_library
        mock_component_type = mock.MagicMock()
        mock_authoring_api.get_or_create_component_type.return_value = mock_component_type
        mock_authoring_api.get_components.return_value.filter.return_value.exists.return_value = False
        mock_library_usage_key = mock.MagicMock()
        mock_api.validate_can_add_block_to_library.return_value = (None, mock_library_usage_key)
        mock_component_version = mock.MagicMock()
        mock_api.set_library_block_olx.return_value = mock_component_version
        mock_content_staging_api.get_staged_content_static_files.return_value = []

        create_block_in_library(
            self.block_to_import, self.usage_key, self.library_key, self.user_id, self.staged_content_id, False
        )

        mock_content_library.objects.get_by_key.assert_called_once_with(self.library_key)
        mock_authoring_api.get_or_create_component_type.assert_called_once_with("xblock.v1", self.block_type)
        mock_authoring_api.get_components.assert_called_once_with(self.mock_learning_package.id)
        mock_api.validate_can_add_block_to_library.assert_called_once_with(
            self.library_key, self.block_to_import.tag, self.block_id
        )
        mock_authoring_api.create_component.assert_called_once()
        mock_api.set_library_block_olx.assert_called_once_with(
            mock_library_usage_key, etree.tostring(self.block_to_import)
        )

    @mock.patch('cms.djangoapps.course_to_library_import.helpers.content_staging_api')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.authoring_api')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.api')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.ContentLibrary')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers._handle_component_override')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.ComponentVersionImport')
    def test_create_block_in_library_existing_component_with_override(
        self,
        mock_component_version_import,
        mock_handle_override,
        mock_content_library,
        mock_api,
        mock_authoring_api,
        mock_content_staging_api
    ):
        mock_content_library.objects.get_by_key.return_value = self.mock_library
        mock_component_type = mock.MagicMock()
        mock_authoring_api.get_or_create_component_type.return_value = mock_component_type
        mock_authoring_api.get_components.return_value.filter.return_value.exists.return_value = True

        mock_component_version = mock.MagicMock(spec=['id', 'component_id'])
        mock_handle_override.return_value = mock_component_version

        mock_component_version_import.return_value = mock.MagicMock()

        mock_content_staging_api.get_staged_content_static_files.return_value = []

        CourseToLibraryImportFactory(
            status=CourseToLibraryImportStatus.READY, library_key=self.library_key, user_id=self.user_id
        )
        create_block_in_library(
            self.block_to_import, self.usage_key, self.library_key, self.user_id, self.staged_content_id, True
        )

        mock_content_library.objects.get_by_key.assert_called_once_with(self.library_key)
        mock_authoring_api.get_or_create_component_type.assert_called_once_with("xblock.v1", self.block_type)
        mock_authoring_api.get_components.assert_called_once_with(self.mock_learning_package.id)
        mock_handle_override.assert_called_once_with(
            self.mock_library, self.usage_key, etree.tostring(self.block_to_import)
        )
        mock_api.validate_can_add_block_to_library.assert_not_called()
        mock_authoring_api.create_component.assert_not_called()

    @mock.patch('cms.djangoapps.course_to_library_import.helpers.content_staging_api')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.authoring_api')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.api')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.ContentLibrary')
    def test_create_block_in_library_existing_component_without_override(
        self,
        mock_content_library,
        mock_api,
        mock_authoring_api,
        mock_content_staging_api
    ):
        mock_content_library.objects.get_by_key.return_value = self.mock_library
        mock_component_type = mock.MagicMock()
        mock_authoring_api.get_or_create_component_type.return_value = mock_component_type
        mock_authoring_api.get_components.return_value.filter.return_value.exists.return_value = True
        mock_content_staging_api.get_staged_content_static_files.return_value = []

        create_block_in_library(
            self.block_to_import, self.usage_key, self.library_key, self.user_id, self.staged_content_id, False
        )

        mock_content_library.objects.get_by_key.assert_called_once_with(self.library_key)
        mock_authoring_api.get_or_create_component_type.assert_called_once_with("xblock.v1", self.block_type)
        mock_authoring_api.get_components.assert_called_once_with(self.mock_learning_package.id)
        mock_api.validate_can_add_block_to_library.assert_not_called()
        mock_authoring_api.create_component.assert_not_called()
        mock_api.set_library_block_olx.assert_not_called()

    @mock.patch('cms.djangoapps.course_to_library_import.helpers.content_staging_api')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers._update_component_version_import')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers._process_staged_content_files')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.authoring_api')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.ContentLibrary')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers._handle_component_override')
    def test_create_block_in_library_with_files_and_override(
        self, mock_handle_override, mock_content_library,
        mock_authoring_api, mock_process_files,
        mock_update_component, mock_content_staging_api
    ):
        mock_content_library.objects.get_by_key.return_value = self.mock_library
        mock_component_type = mock.MagicMock()
        mock_authoring_api.get_or_create_component_type.return_value = mock_component_type
        mock_authoring_api.get_components.return_value.filter.return_value.exists.return_value = True
        mock_component_version = mock.MagicMock()
        mock_handle_override.return_value = mock_component_version
        mock_file_data = [mock.MagicMock()]
        mock_content_staging_api.get_staged_content_static_files.return_value = mock_file_data

        create_block_in_library(
            self.block_to_import, self.usage_key, self.library_key, self.user_id, self.staged_content_id, True
        )

        mock_content_library.objects.get_by_key.assert_called_once_with(self.library_key)
        mock_update_component.assert_called_once_with(
            mock_component_version, self.usage_key, self.library_key, self.user_id
        )
        mock_process_files.assert_called_once()


class TestProcessStagedContentFiles(TestCase):
    """
    Tests for the _process_staged_content_files helper function.
    """

    def setUp(self):
        super().setUp()
        self.library_key = LibraryLocatorV2(org="TestOrg", slug="test-lib")
        self.user_id = UserFactory().id
        self.block_id = "problem1"
        self.block_type = "problem"
        self.staged_content_id = "staged-content-id"
        self.usage_key = UsageKey.from_string(
            f"block-v1:TestOrg+TestCourse+Run1+type@{self.block_type}+block@{self.block_id}"
        )

        self.xml_content = "<problem>Test problem content</problem>"
        self.block_to_import = etree.fromstring(self.xml_content)
        self.mock_library = mock.MagicMock()
        self.mock_library.library_key = self.library_key
        self.mock_learning_package = mock.MagicMock()
        self.mock_library.learning_package = self.mock_learning_package
        self.now = datetime.now(tz=timezone.utc)

    @mock.patch('cms.djangoapps.course_to_library_import.helpers.CourseToLibraryImport.objects.get')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.ComponentVersionImport.objects.get_or_create')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.content_staging_api')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.authoring_api')
    def test_process_staged_content_files_with_reference_in_block(
        self, mock_authoring_api, mock_content_staging_api, mock_get_or_create, mock_get_import
    ):
        mock_component_version = mock.MagicMock()
        mock_file_data = mock.MagicMock()
        mock_file_data.filename = "test_file.txt"

        xml_content = '<problem>Test problem with <img src="test_file.txt"/></problem>'
        block_to_import = etree.fromstring(xml_content)

        mock_content_staging_api.get_staged_content_static_file_data.return_value = b"file data"
        mock_media_type = mock.MagicMock(id=1)
        mock_authoring_api.get_or_create_media_type.return_value = mock_media_type
        mock_content = mock.MagicMock(id=1)
        mock_authoring_api.get_or_create_file_content.return_value = mock_content
        mock_import = mock.MagicMock()
        mock_get_import.return_value = mock_import

        _process_staged_content_files(
            mock_component_version, [mock_file_data], self.staged_content_id, self.usage_key,
            self.mock_library, self.now, block_to_import, False, self.library_key, self.user_id
        )

        mock_content_staging_api.get_staged_content_static_file_data.assert_called_once_with(
            self.staged_content_id, mock_file_data.filename
        )
        mock_authoring_api.get_or_create_media_type.assert_called_once()
        mock_authoring_api.get_or_create_file_content.assert_called_once_with(
            self.mock_library.learning_package.id,
            mock_media_type.id,
            data=b"file data",
            created=self.now,
        )
        mock_authoring_api.create_component_version_content.assert_called_once_with(
            mock_component_version.pk,
            mock_content.id,
            key=f"static/{str(self.usage_key)}"
        )
        mock_get_or_create.assert_called_once()

    @mock.patch('cms.djangoapps.course_to_library_import.helpers.CourseToLibraryImport.objects.get')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.content_staging_api')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.authoring_api')
    def test_process_staged_content_files_missing_file_data(
        self, mock_authoring_api, mock_content_staging_api, mock_get_import
    ):
        mock_component_version = mock.MagicMock()
        mock_file_data = mock.MagicMock()
        mock_file_data.filename = "test_file.txt"

        xml_content = '<problem>Test problem with <img src="test_file.txt"/></problem>'
        block_to_import = etree.fromstring(xml_content)

        mock_content_staging_api.get_staged_content_static_file_data.return_value = None
        mock_import = mock.MagicMock()
        mock_get_import.return_value = mock_import

        _process_staged_content_files(
            mock_component_version, [mock_file_data], self.staged_content_id, self.usage_key,
            self.mock_library, self.now, block_to_import, False, self.library_key, self.user_id
        )

        mock_content_staging_api.get_staged_content_static_file_data.assert_called_once_with(
            self.staged_content_id, mock_file_data.filename
        )
        mock_authoring_api.get_or_create_file_content.assert_not_called()
        mock_authoring_api.create_component_version_content.assert_not_called()

    @mock.patch('cms.djangoapps.course_to_library_import.helpers.CourseToLibraryImport.objects.get')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.ComponentVersionImport.objects.get_or_create')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.content_staging_api')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.authoring_api')
    def test_process_staged_content_files_integrity_error(
        self, mock_authoring_api, mock_content_staging_api, mock_get_or_create, mock_get_import
    ):
        mock_component_version = mock.MagicMock()
        mock_file_data = mock.MagicMock()
        mock_file_data.filename = "test_file.txt"

        xml_content = '<problem>Test problem with <img src="test_file.txt"/></problem>'
        block_to_import = etree.fromstring(xml_content)

        mock_content_staging_api.get_staged_content_static_file_data.return_value = b"file data"
        mock_media_type = mock.MagicMock(id=1)
        mock_authoring_api.get_or_create_media_type.return_value = mock_media_type
        mock_content = mock.MagicMock(id=1)
        mock_authoring_api.get_or_create_file_content.return_value = mock_content

        mock_authoring_api.create_component_version_content.side_effect = IntegrityError("Duplicate content")

        mock_import = mock.MagicMock()
        mock_get_import.return_value = mock_import
        mock_get_or_create.return_value = (mock.MagicMock(), True)

        _process_staged_content_files(
            mock_component_version, [mock_file_data], self.staged_content_id, self.usage_key,
            self.mock_library, self.now, block_to_import, False, self.library_key, self.user_id
        )

        mock_content_staging_api.get_staged_content_static_file_data.assert_called_once_with(
            self.staged_content_id, mock_file_data.filename
        )
        mock_authoring_api.create_component_version_content.assert_called_once()
        mock_get_or_create.assert_called_once()

    @mock.patch('cms.djangoapps.course_to_library_import.helpers.authoring_api')
    def test_process_staged_content_files_no_files(self, mock_authoring_api):
        mock_component_version = mock.MagicMock()

        _process_staged_content_files(
            mock_component_version, [], self.staged_content_id, self.usage_key,
            self.mock_library, self.now, self.block_to_import, False, self.library_key, self.user_id
        )

        mock_authoring_api.get_or_create_media_type.assert_not_called()
        mock_authoring_api.get_or_create_file_content.assert_not_called()
        mock_authoring_api.create_component_version_content.assert_not_called()

    @mock.patch('cms.djangoapps.course_to_library_import.helpers.authoring_api')
    def test_process_staged_content_files_file_not_referenced(self, mock_authoring_api):
        mock_component_version = mock.MagicMock()
        mock_file_data = mock.MagicMock()
        mock_file_data.filename = "unreferenced_file.txt"

        _process_staged_content_files(
            mock_component_version, [mock_file_data], self.staged_content_id, self.usage_key,
            self.mock_library, self.now, self.block_to_import, False, self.library_key, self.user_id
        )

        mock_authoring_api.get_or_create_file_content.assert_not_called()
        mock_authoring_api.create_component_version_content.assert_not_called()

    @mock.patch('cms.djangoapps.course_to_library_import.helpers.ComponentVersionImport.objects.get_or_create')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.authoring_api')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.content_staging_api')
    def test_process_staged_content_files_with_override(
        self, mock_content_staging_api, mock_authoring_api, mock_get_or_create
    ):
        mock_component_version = mock.MagicMock()
        mock_file_data = mock.MagicMock()
        mock_file_data.filename = "test_file.txt"
        mock_content_staging_api.get_staged_content_static_file_data.return_value = b"file data"
        mock_authoring_api.get_or_create_media_type.return_value = mock.MagicMock(id=1)
        mock_authoring_api.get_or_create_file_content.return_value = mock.MagicMock(id=1)
        mock_get_or_create.return_value = (mock.MagicMock(), True)

        self.xml_content = '<problem><img src="/static/test_file.txt"/></problem>'
        self.block_to_import = etree.fromstring(self.xml_content)
        _process_staged_content_files(
            mock_component_version, [mock_file_data], self.staged_content_id, self.usage_key,
            self.mock_library, self.now, self.block_to_import, True, self.library_key, self.user_id
        )

        mock_authoring_api.get_or_create_media_type.assert_called_once()
        mock_authoring_api.get_or_create_file_content.assert_called_once()
        mock_authoring_api.create_component_version_content.assert_called_once()


class TestHandleComponentOverride(TestCase):
    """
    Tests for the _handle_component_override helper function.
    """

    def setUp(self):
        super().setUp()
        self.library_key = LibraryLocatorV2(org="TestOrg", slug="test-lib")
        self.user_id = UserFactory().id
        self.block_id = "problem1"
        self.block_type = "problem"
        self.usage_key = UsageKey.from_string(
            f"block-v1:TestOrg+TestCourse+Run1+type@{self.block_type}+block@{self.block_id}"
        )
        self.xml_content = b"<problem>Test problem content</problem>"

        self.mock_library = mock.MagicMock()
        self.mock_library.library_key = self.library_key
        self.mock_learning_package = mock.MagicMock()
        self.mock_library.learning_package = self.mock_learning_package

    @mock.patch('cms.djangoapps.course_to_library_import.helpers.api')
    def test_handle_component_override_existing_component(self, mock_api):
        mock_component = mock.MagicMock()
        mock_component.component_type.name = self.block_type
        mock_component.local_key = self.block_id

        self.mock_learning_package.component_set.filter.return_value.first.return_value = mock_component

        expected_lib_usage_key = LibraryUsageLocatorV2(
            lib_key=self.library_key,
            block_type=self.block_type,
            usage_id=self.block_id,
        )

        mock_component_version = mock.MagicMock()
        mock_api.set_library_block_olx.return_value = mock_component_version

        result = _handle_component_override(self.mock_library, self.usage_key, self.xml_content)

        self.mock_learning_package.component_set.filter.assert_called_once_with(local_key=self.block_id)
        mock_api.set_library_block_olx.assert_called_once_with(expected_lib_usage_key, self.xml_content)
        self.assertEqual(result, mock_component_version)

    @mock.patch('cms.djangoapps.course_to_library_import.helpers.api')
    def test_handle_component_override_nonexistent_component(self, mock_api):
        self.mock_learning_package.component_set.filter.return_value.first.return_value = None

        result = _handle_component_override(self.mock_library, self.usage_key, self.xml_content)

        self.mock_learning_package.component_set.filter.assert_called_once_with(local_key=self.block_id)
        mock_api.set_library_block_olx.assert_not_called()
        self.assertIsNone(result)

    @mock.patch('cms.djangoapps.course_to_library_import.helpers.api')
    def test_handle_component_override_api_error(self, mock_api):
        mock_component = mock.MagicMock()
        mock_component.component_type.name = self.block_type
        mock_component.local_key = self.block_id

        self.mock_learning_package.component_set.filter.return_value.first.return_value = mock_component

        mock_api.set_library_block_olx.side_effect = Exception("API error")

        with self.assertRaises(Exception):
            _handle_component_override(self.mock_library, self.usage_key, self.xml_content)

        mock_api.set_library_block_olx.assert_called_once()


class TestUpdateContainerComponents(TestCase):
    """
    Tests for the _update_container_components helper function.
    """

    def setUp(self):
        super().setUp()
        self.user_id = UserFactory().id
        self.mock_container_version = mock.MagicMock()
        self.mock_container_version.container.pk = "container_pk"
        self.mock_container_version.title = "Container Title"

    @mock.patch('cms.djangoapps.course_to_library_import.helpers.authoring_api')
    def test_update_container_components_with_mixed_components(self, mock_authoring_api):
        mock_component_version = mock.MagicMock()
        mock_component_version.component.pk = "component_pk"
        mock_container_child_version = mock.MagicMock(spec=ContainerVersion)
        mock_container_child_version.container.pk = "container_child_pk"

        component_versions = [mock_component_version, mock_container_child_version]

        _update_container_components(self.mock_container_version, component_versions, self.user_id)

        mock_authoring_api.create_next_container_version.assert_called_once_with(
            container_pk=self.mock_container_version.container.pk,
            title=self.mock_container_version.title,
            publishable_entities_pks=["component_pk", "container_child_pk"],
            entity_version_pks=[mock_component_version.pk, mock_container_child_version.pk],
            created=mock.ANY,
            created_by=self.user_id,
            container_version_cls=self.mock_container_version.__class__,
        )

    @mock.patch('cms.djangoapps.course_to_library_import.helpers.authoring_api')
    def test_update_container_components_empty_list(self, mock_authoring_api):
        _update_container_components(self.mock_container_version, [], self.user_id)

        mock_authoring_api.create_next_container_version.assert_called_once_with(
            container_pk=self.mock_container_version.container.pk,
            title=self.mock_container_version.title,
            publishable_entities_pks=[],
            entity_version_pks=[],
            created=mock.ANY,
            created_by=self.user_id,
            container_version_cls=self.mock_container_version.__class__,
        )


class TestCreateContainer(TestCase):
    """
    Tests for the create_container helper function.
    """

    def setUp(self):
        super().setUp()
        self.library_key = LibraryLocatorV2(org="TestOrg", slug="test-lib")
        self.user_id = UserFactory().id

    @mock.patch('cms.djangoapps.course_to_library_import.helpers.authoring_api')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.ContentLibrary')
    def test_create_container_chapter(self, mock_content_library, mock_authoring_api):
        mock_library = mock.MagicMock()
        mock_content_library.objects.get_by_key.return_value = mock_library

        mock_container = mock.MagicMock()
        mock_container_version = mock.MagicMock()
        mock_authoring_api.create_unit_and_version.return_value = (mock_container, mock_container_version)

        result = create_container('chapter', 'test_key', 'Test Chapter', self.library_key, self.user_id)

        mock_content_library.objects.get_by_key.assert_called_once_with(self.library_key)
        mock_authoring_api.create_unit_and_version.assert_called_once_with(
            mock_library.learning_package.id,
            key='test_key',
            title='Test Chapter',
            components=[],
            created=mock.ANY,
            created_by=self.user_id,
        )
        self.assertEqual(result, mock_container_version)

    @mock.patch('cms.djangoapps.course_to_library_import.helpers.authoring_api')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.ContentLibrary')
    def test_create_container_sequential(self, mock_content_library, mock_authoring_api):
        mock_library = mock.MagicMock()
        mock_content_library.objects.get_by_key.return_value = mock_library

        mock_container = mock.MagicMock()
        mock_container_version = mock.MagicMock()
        mock_authoring_api.create_unit_and_version.return_value = (mock_container, mock_container_version)

        result = create_container('sequential', 'test_key', 'Test Sequential', self.library_key, self.user_id)

        mock_authoring_api.create_unit_and_version.assert_called_once_with(
            mock_library.learning_package.id,
            key='test_key',
            title='Test Sequential',
            components=[],
            created=mock.ANY,
            created_by=self.user_id,
        )
        self.assertEqual(result, mock_container_version)

    @mock.patch('cms.djangoapps.course_to_library_import.helpers.authoring_api')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.ContentLibrary')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.secrets')
    def test_create_container_no_key(self, mock_secrets, mock_content_library, mock_authoring_api):
        mock_library = mock.MagicMock()
        mock_content_library.objects.get_by_key.return_value = mock_library

        mock_container = mock.MagicMock()
        mock_container_version = mock.MagicMock()
        mock_authoring_api.create_unit_and_version.return_value = (mock_container, mock_container_version)

        mock_secrets.token_hex.return_value = "generated_key"

        result = create_container('vertical', None, 'Test Vertical', self.library_key, self.user_id)

        mock_secrets.token_hex.assert_called_once_with(16)
        mock_authoring_api.create_unit_and_version.assert_called_once_with(
            mock_library.learning_package.id,
            key='generated_key',
            title='Test Vertical',
            components=[],
            created=mock.ANY,
            created_by=self.user_id,
        )
        self.assertEqual(result, mock_container_version)

    @mock.patch('cms.djangoapps.course_to_library_import.helpers.authoring_api')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.ContentLibrary')
    def test_create_container_no_display_name(self, mock_content_library, mock_authoring_api):
        mock_library = mock.MagicMock()
        mock_content_library.objects.get_by_key.return_value = mock_library

        mock_container = mock.MagicMock()
        mock_container_version = mock.MagicMock()
        mock_authoring_api.create_unit_and_version.return_value = (mock_container, mock_container_version)

        result = create_container('vertical', 'test_key', '', self.library_key, self.user_id)

        mock_authoring_api.create_unit_and_version.assert_called_once_with(
            mock_library.learning_package.id,
            key='test_key',
            title='New vertical',
            components=[],
            created=mock.ANY,
            created_by=self.user_id,
        )
        self.assertEqual(result, mock_container_version)


class TestImportContainer(TestCase):
    """
    Tests for the import_container helper function.
    """

    def setUp(self):
        super().setUp()
        self.library_key = LibraryLocatorV2(org="TestOrg", slug="test-lib")
        self.user_id = UserFactory().id
        self.usage_key = UsageKey.from_string("block-v1:TestOrg+TestCourse+Run1+type@chapter+block@chapter1")
        self.staged_content = mock.MagicMock()
        self.staged_content.id = "staged-content-id"

    @mock.patch('cms.djangoapps.course_to_library_import.helpers.ContainerVersionImport')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers._update_container_components')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.create_container')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.import_children')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.CourseToLibraryImport')
    def test_import_container_with_container_composition(
        self, mock_course_import, mock_import_children, mock_create_container,
        mock_update_container, mock_section_version_import
    ):
        xml = """
        <chapter url_name="chapter1" display_name="Test Chapter">
            <sequential url_name="seq1">
                <vertical url_name="vert1">
                    <problem url_name="problem1"/>
                </vertical>
            </sequential>
        </chapter>
        """
        block_to_import = etree.fromstring(xml)

        mock_container_version = mock.MagicMock()
        mock_create_container.return_value = mock_container_version

        mock_component_versions = [mock.MagicMock()]
        mock_import_children.return_value = mock_component_versions

        mock_section_version_import.objects.create = mock.MagicMock()
        mock_get_import = mock.MagicMock()
        mock_course_import.objects.get.return_value = mock_get_import

        import_container(
            self.usage_key, block_to_import, self.library_key, self.user_id,
            self.staged_content, 'chapter', False
        )

        mock_create_container.assert_called_once_with(
            'chapter', 'chapter1', 'Test Chapter', self.library_key, self.user_id
        )
        mock_import_children.assert_called_once_with(
            block_to_import, self.library_key, self.user_id, self.staged_content,
            'chapter', False
        )
        mock_update_container.assert_called_once_with(
            mock_container_version, mock_component_versions, self.user_id
        )
        mock_section_version_import.objects.create.assert_called_once_with(
            section_version=mock_container_version,
            source_usage_key=self.usage_key,
            library_import=mock_get_import
        )

    @mock.patch('cms.djangoapps.course_to_library_import.helpers.import_children')
    def test_import_container_xblock_level(self, mock_import_children):
        xml = """
        <chapter url_name="chapter1" display_name="Test Chapter">
            <sequential url_name="seq1">
                <vertical url_name="vert1">
                    <problem url_name="problem1"/>
                </vertical>
            </sequential>
        </chapter>
        """
        block_to_import = etree.fromstring(xml)

        import_container(
            self.usage_key, block_to_import, self.library_key, self.user_id,
            self.staged_content, 'xblock', False
        )

        mock_import_children.assert_called_once_with(
            block_to_import, self.library_key, self.user_id, self.staged_content,
            'xblock', False
        )

    @mock.patch('cms.djangoapps.course_to_library_import.helpers.ContainerVersionImport')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers._update_container_components')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.create_container')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.import_children')
    def test_import_container_no_children(
        self, mock_import_children, mock_create_container, mock_update_container, mock_section_version_import
    ):
        xml = """<chapter url_name="chapter1" display_name="Test Chapter"></chapter>"""
        block_to_import = etree.fromstring(xml)

        CourseToLibraryImportFactory(
            library_key=self.library_key,
            user_id=self.user_id,
            status=CourseToLibraryImportStatus.READY,
        )

        mock_container_version = mock.MagicMock()
        mock_create_container.return_value = mock_container_version

        mock_import_children.return_value = []

        import_container(
            self.usage_key, block_to_import, self.library_key, self.user_id,
            self.staged_content, 'chapter', False
        )

        mock_create_container.assert_called_once()
        mock_import_children.assert_called_once()
        mock_update_container.assert_not_called()


class TestImportChildren(TestCase):
    """
    Tests for the import_children helper function.
    """

    def setUp(self):
        super().setUp()
        self.library_key = LibraryLocatorV2(org="TestOrg", slug="test-lib")
        self.user_id = UserFactory().id

        self.staged_content = mock.MagicMock()
        self.staged_content.id = "staged-content-id"
        self.staged_content.tags = {
            "block-v1:TestOrg+TestCourse+Run1+type@problem+block@problem1": {},
            "block-v1:TestOrg+TestCourse+Run1+type@html+block@html1": {},
            "block-v1:TestOrg+TestCourse+Run1+type@video+block@video1": {},
        }

        self.problem_usage_key = UsageKey.from_string(
            "block-v1:TestOrg+TestCourse+Run1+type@problem+block@problem1"
        )

    @mock.patch('cms.djangoapps.course_to_library_import.helpers.create_block_in_library')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.ContentLibrary')
    def test_import_children_xblock_level(self, mock_content_library, mock_create_block):
        xml = """
        <vertical url_name="vertical1">
            <problem url_name="problem1"/>
            <html url_name="html1"/>
        </vertical>
        """
        block_to_import = etree.fromstring(xml)

        mock_library = mock.MagicMock()
        mock_content_library.objects.filter.return_value.first.return_value = mock_library

        mock_component_version = mock.MagicMock(spec=['id', 'component_id'])
        mock_create_block.return_value = mock_component_version

        result = import_children(
            block_to_import, self.library_key, self.user_id, self.staged_content, 'xblock', False
        )

        self.assertEqual(mock_create_block.call_count, 2)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], mock_component_version)
        self.assertEqual(result[1], mock_component_version)

    @mock.patch('cms.djangoapps.course_to_library_import.helpers._update_container_components')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.create_container')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.create_block_in_library')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.ContentLibrary')
    def test_import_children_with_containers(
        self, mock_content_library, mock_create_block, mock_create_container, mock_update_container
    ):
        xml = """
        <chapter url_name="chapter1" display_name="Test Chapter">
            <sequential url_name="seq1" display_name="Test Sequential">
                <vertical url_name="vert1" display_name="Test Vertical">
                    <problem url_name="problem1"/>
                </vertical>
            </sequential>
        </chapter>
        """
        block_to_import = etree.fromstring(xml)

        mock_library = mock.MagicMock()
        mock_content_library.objects.filter.return_value.first.return_value = mock_library

        mock_component_version = mock.MagicMock(spec=['id', 'component_id'])
        mock_create_block.return_value = mock_component_version

        mock_container_version = mock.MagicMock(spec=ContainerVersion)
        mock_create_container.return_value = mock_container_version

        result = import_children(
            block_to_import, self.library_key, self.user_id, self.staged_content, 'chapter', False
        )

        self.assertEqual(mock_create_container.call_count, 2)
        self.assertEqual(mock_create_block.call_count, 1)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], mock_container_version)

    @mock.patch('cms.djangoapps.course_to_library_import.helpers.create_block_in_library')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.ContentLibrary')
    def test_import_children_empty_block_xblock_level(self, mock_content_library, mock_create_block):
        xml = '<problem url_name="problem1"/>'
        block_to_import = etree.fromstring(xml)

        mock_library = mock.MagicMock()
        mock_content_library.objects.filter.return_value.first.return_value = mock_library

        mock_component_version = mock.MagicMock()
        mock_create_block.return_value = mock_component_version

        result = import_children(
            block_to_import, self.library_key, self.user_id, self.staged_content, 'xblock', False
        )

        mock_create_block.assert_called_once()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], mock_component_version)

    @mock.patch('cms.djangoapps.course_to_library_import.helpers.create_block_in_library')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.ContentLibrary')
    def test_import_children_with_override(self, mock_content_library, mock_create_block):
        xml = '<problem url_name="problem1"/>'
        block_to_import = etree.fromstring(xml)

        mock_library = mock.MagicMock()
        mock_content_library.objects.filter.return_value.first.return_value = mock_library

        import_children(
            block_to_import, self.library_key, self.user_id, self.staged_content, 'xblock', True
        )

        mock_create_block.assert_called_once_with(
            block_to_import,
            self.problem_usage_key,
            self.library_key,
            self.user_id,
            self.staged_content.id,
            True,
        )

    @mock.patch('cms.djangoapps.course_to_library_import.helpers.ContentLibrary')
    def test_import_children_library_not_found(self, mock_content_library):
        xml = '<problem url_name="problem1"/>'
        block_to_import = etree.fromstring(xml)

        mock_content_library.objects.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError):
            import_children(
                block_to_import, self.library_key, self.user_id, self.staged_content, 'xblock', False
            )

    def test_import_children_no_matching_children(self):
        xml = """
        <vertical url_name="vertical1">
            <problem url_name="nonexistent_problem"/>
            <html url_name="nonexistent_html"/>
        </vertical>
        """
        block_to_import = etree.fromstring(xml)

        result = import_children(
            block_to_import, self.library_key, self.user_id, self.staged_content, 'xblock', False
        )

        self.assertEqual(result, [])

    @mock.patch('cms.djangoapps.course_to_library_import.helpers._update_container_components')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.create_container')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.create_block_in_library')
    @mock.patch('cms.djangoapps.course_to_library_import.helpers.ContentLibrary')
    def test_import_children_filter_by_composition_level(
        self, mock_content_library, mock_create_block, mock_create_container, mock_update_container
    ):
        xml = """
        <chapter url_name="chapter1">
            <sequential url_name="seq1">
                <problem url_name="problem1"/>
            </sequential>
        </chapter>
        """
        block_to_import = etree.fromstring(xml)

        mock_library = mock.MagicMock()
        mock_content_library.objects.filter.return_value.first.return_value = mock_library

        mock_component_version = mock.MagicMock(spec=['id', 'component_id'])
        mock_create_block.return_value = mock_component_version

        mock_container_version = mock.MagicMock(spec=ContainerVersion)
        mock_create_container.return_value = mock_container_version

        result_xblock = import_children(
            block_to_import, self.library_key, self.user_id, self.staged_content, 'xblock', False
        )

        result_chapter = import_children(
            block_to_import, self.library_key, self.user_id, self.staged_content, 'chapter', False
        )

        self.assertTrue(all(not isinstance(item, ContainerVersion) for item in result_xblock))

        self.assertEqual(len(result_chapter), 1)
        self.assertEqual(result_chapter[0], mock_container_version)
