"""
Unit tests for the ImportBlocksSerializer.
"""

from unittest.mock import patch

from django.test import TestCase
from rest_framework.exceptions import ValidationError

from cms.djangoapps.course_to_library_import.views.v0.serializers import ImportBlocksSerializer


class TestImportBlocksSerializer(TestCase):
    """
    Tests for the ImportBlocksSerializer.
    """

    def setUp(self):
        """
        Set up common test data.
        """
        self.valid_data = {
            'library_key': 'lib:v1:org+lib+2023',
            'usage_ids': ['block-v1:org+course+2023+type@html+block@123'],
            'course_id': 'course-v1:org+course+2023',
            'import_id': 'valid-import-id',
            'composition_level': 'vertical',
            'override': False,
        }

    @patch('cms.djangoapps.course_to_library_import.models.CourseToLibraryImport.get_ready_by_uuid')
    def test_validate_with_valid_import_id(self, mock_get_ready_by_uuid):
        """
        Test that validation passes when a valid import_id is provided.
        """
        mock_get_ready_by_uuid.return_value = {'some': 'object'}

        serializer = ImportBlocksSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())

        mock_get_ready_by_uuid.assert_called_once_with(self.valid_data['import_id'])

    @patch('cms.djangoapps.course_to_library_import.models.CourseToLibraryImport.get_ready_by_uuid')
    def test_validate_with_invalid_import_id(self, mock_get_ready_by_uuid):
        """
        Test that validation fails when an invalid import_id is provided.
        """
        mock_get_ready_by_uuid.return_value = None

        serializer = ImportBlocksSerializer(data=self.valid_data)

        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)

        self.assertEqual(
            context.exception.detail,
            {'import_id': ['Invalid import ID.']}
        )

        mock_get_ready_by_uuid.assert_called_once_with(self.valid_data['import_id'])
