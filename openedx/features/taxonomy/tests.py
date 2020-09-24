"""
Validate taxonomy integration.
"""

from django.test import TestCase
from mock import patch

from taxonomy.validators import CourseMetadataProviderValidator


class TaxonomyIntegrationTests(TestCase):
    """
    Validate integration of taxonomy and metadata providers.
    """

    @patch('openedx.features.taxonomy.providers.get_courses_by_uuid')
    def test_validate(self, mock_get_courses_by_uuid):
        """
        Validate that there are no integration issues.
        """
        mock_get_courses_by_uuid.return_value = [{
            'uuid': 'test-uuid',
            'key': 'test-key',
            'title': 'test-title',
            'short_description': 'test-short-description',
            'full_description': 'test-full-description',
        }]
        course_metadata_validator = CourseMetadataProviderValidator(
            ['test-uuid']
        )

        course_metadata_validator.validate()
