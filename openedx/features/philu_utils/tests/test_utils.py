"""
Test utility methods
"""
from django.core.validators import ValidationError
from django.test import TestCase
from mock import Mock

from openedx.features.philu_utils.utils import bytes_to_mb, validate_file_size


class UtilityTest(TestCase):
    """
    Unit test class to test utility methods
    """

    def test_validate_file_size_success(self):
        """Test valid file size"""
        idea_file = Mock()
        idea_file.size = 4 * 1024 * 1024

        try:
            validate_file_size(idea_file.size, max_allowed_size=4 * 1024 * 1024)
        except ValidationError:
            self.fail('Validation error raised, invalid file size')

    def test_validate_file_size_failure(self):
        """Test invalid file size"""
        image = Mock()
        image.size = 6 * 1024 * 1024

        with self.assertRaises(ValidationError):
            validate_file_size(image, max_allowed_size=4 * 1024 * 1024)

    def test_bytes_to_mb(self):
        self.assertEqual(bytes_to_mb(1024 * 1024), 1)
