"""
Tests for tasks in course_to_library_import app.
"""

from unittest.mock import Mock, patch

from django.test import TestCase
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locator import LibraryLocatorV2

from cms.djangoapps.course_to_library_import.data import CourseToLibraryImportStatus
from cms.djangoapps.course_to_library_import.tasks import (
    import_library_from_staged_content_task,
    save_courses_to_staged_content_task,
)
from common.djangoapps.student.tests.factories import UserFactory

from .factories import CourseToLibraryImportFactory


class TestSaveCourseSectionsToStagedContentTask(TestCase):
    """
    Test cases for save_course_sections_to_staged_content_task.
    """

    @patch('cms.djangoapps.course_to_library_import.tasks.modulestore')
    @patch('openedx.core.djangoapps.content_staging.api.stage_xblock_temporarily')
    def test_save_courses_to_staged_content_task(self, mock_stage_xblock_temporarily, mock_modulestore):
        course_to_library_import = CourseToLibraryImportFactory()
        course_ids = course_to_library_import.course_ids.split(' ')
        user_id = course_to_library_import.user.id
        purpose = 'test_purpose'
        version_num = 1

        mock_course_keys = [CourseKey.from_string(course_id) for course_id in course_ids]
        mock_modulestore().get_items.return_value = sections = ['section1', 'section2']

        self.assertEqual(course_to_library_import.status, CourseToLibraryImportStatus.PENDING)

        save_courses_to_staged_content_task(course_ids, user_id, course_to_library_import.id, purpose, version_num)

        for mock_course_key in mock_course_keys:
            mock_modulestore().get_items.assert_any_call(mock_course_key, qualifiers={"category": "chapter"})

        self.assertEqual(mock_stage_xblock_temporarily.call_count, len(sections) * len(course_ids))
        for section in sections:
            mock_stage_xblock_temporarily.assert_any_call(section, user_id, purpose=purpose, version_num=version_num)


class TestImportLibraryFromStagedContentTask(TestCase):
    """
    Test cases for import_library_from_staged_content_task.
    """

    @patch('cms.djangoapps.course_to_library_import.tasks.validate_usage_ids')
    @patch(
        'cms.djangoapps.course_to_library_import.tasks.content_staging_api.get_ready_staged_content_by_user_and_purpose'
    )
    @patch('cms.djangoapps.course_to_library_import.tasks.get_block_to_import')
    @patch('cms.djangoapps.course_to_library_import.tasks.import_container')
    @patch('cms.djangoapps.course_to_library_import.tasks.etree')
    def test_import_library_from_staged_content_task(
        self, mock_etree, mock_import_container, mock_get_block_to_import,
        mock_get_ready_staged_content, mock_validate_usage_ids
    ):
        user = UserFactory()
        usage_ids = ['block-v1:edX+Demo+2023+type@vertical+block@12345']
        usage_key = UsageKey.from_string(usage_ids[0])
        library_key = 'lib:TestOrg:TestLib'
        purpose = 'import_from_{course_id}'
        course_id = 'course-v1:edX+Demo+2023'
        override = True

        mock_staged_content = mock_get_ready_staged_content.return_value
        mock_content_item = Mock()
        mock_content_item.olx = '<olx>content</olx>'
        mock_staged_content.filter.return_value.first.return_value = mock_content_item

        mock_node = Mock()
        mock_etree.fromstring.return_value = mock_node
        mock_etree.XMLParser.return_value = Mock()

        mock_block = Mock()
        mock_get_block_to_import.return_value = mock_block

        library_locator = LibraryLocatorV2.from_string(library_key)
        course_to_library_import = CourseToLibraryImportFactory(
            user=user,
            library_key=library_locator,
            status=CourseToLibraryImportStatus.READY
        )

        import_library_from_staged_content_task(
            user.id, usage_ids, library_key, purpose, course_id, 'xblock', override
        )

        mock_get_ready_staged_content.assert_called_once_with(
            user.id, purpose.format(course_id=course_id)
        )
        mock_validate_usage_ids.assert_called_once_with(usage_ids, mock_staged_content)
        mock_etree.XMLParser.assert_called_once_with(strip_cdata=False)
        mock_etree.fromstring.assert_called_once_with(mock_content_item.olx, parser=mock_etree.XMLParser())

        mock_staged_content.filter.assert_called_once_with(tags__icontains=usage_ids[0])
        mock_get_block_to_import.assert_called_once_with(mock_node, usage_key)
        mock_import_container.assert_called_once_with(
            usage_key, mock_block, library_locator, user.id, mock_content_item, 'xblock', override
        )

        course_to_library_import.refresh_from_db()
        self.assertEqual(course_to_library_import.status, CourseToLibraryImportStatus.IMPORTED)
        mock_staged_content.delete.assert_called_once()

    @patch(
        'cms.djangoapps.course_to_library_import.tasks.content_staging_api.get_ready_staged_content_by_user_and_purpose'
    )
    @patch('cms.djangoapps.course_to_library_import.tasks.get_block_to_import')
    @patch('cms.djangoapps.course_to_library_import.tasks.etree')
    def test_import_library_block_not_found(
        self, mock_etree, mock_get_block_to_import, mock_get_ready_staged_content
    ):
        user = UserFactory()
        usage_ids = ['block-v1:edX+Demo+2023+type@vertical+block@12345']
        library_key = 'lib:TestOrg:TestLib'
        purpose = 'import_from_{course_id}'
        course_id = 'course-v1:edX+Demo+2023'
        override = True

        mock_staged_content = mock_get_ready_staged_content.return_value
        mock_content_item = Mock()
        mock_content_item.olx = '<olx>content</olx>'
        mock_staged_content.filter.return_value.first.return_value = mock_content_item

        mock_node = Mock()
        mock_etree.fromstring.return_value = mock_node
        mock_etree.XMLParser.return_value = Mock()

        mock_get_block_to_import.return_value = None

        library_locator = LibraryLocatorV2.from_string(library_key)
        CourseToLibraryImportFactory(
            user=user,
            library_key=library_locator,
            status=CourseToLibraryImportStatus.READY
        )

        with self.assertRaises(ValueError):
            import_library_from_staged_content_task(
                user.id, usage_ids, library_key, purpose, course_id, 'xblock', override
            )
