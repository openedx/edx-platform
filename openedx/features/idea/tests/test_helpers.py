from django.core.validators import ValidationError
from django.test import TestCase
from mock import Mock

from openedx.features.idea.helpers import validate_image_dimensions

from ..constants import IDEA_IMAGE_HEIGHT, IDEA_IMAGE_WIDTH


class IdeaHelpersTest(TestCase):

    def test_validate_image_dimensions_success(self):
        """Test valid image dimension"""
        image = Mock()
        image.width = IDEA_IMAGE_WIDTH
        image.height = IDEA_IMAGE_HEIGHT

        try:
            validate_image_dimensions(image)
        except ValidationError:
            self.fail('Validation error raised, invalid dimensions')

    def test_validate_image_dimensions_failure(self):
        """Test invalid image dimensions"""
        image = Mock()

        # invalid width only
        with self.assertRaises(ValidationError):
            image.width = 100
            image.height = IDEA_IMAGE_HEIGHT
            validate_image_dimensions(image)

        # invalid height only
        with self.assertRaises(ValidationError):
            image.width = IDEA_IMAGE_WIDTH
            image.height = 100
            validate_image_dimensions(image)

        # invalid width and height
        with self.assertRaises(ValidationError):
            image.width = 100
            image.height = 200
            validate_image_dimensions(image)
