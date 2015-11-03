"""
Tests for the Badges app models.
"""
from django.core.exceptions import ValidationError
from django.core.files.images import ImageFile
from django.test import TestCase
from nose.plugins.attrib import attr

from badges.models import CourseCompleteImageConfiguration
from certificates.tests.test_models import TEST_DATA_ROOT


@attr('shard_1')
class BadgeImageConfigurationTest(TestCase):
    """
    Test the validation features of BadgeImageConfiguration.
    """
    def get_image(self, name):
        """
        Get one of the test images from the test data directory.
        """
        return ImageFile(open(TEST_DATA_ROOT / 'badges' / name + '.png'))

    def create_clean(self, file_obj):
        """
        Shortcut to create a BadgeImageConfiguration with a specific file.
        """
        CourseCompleteImageConfiguration(mode='honor', icon=file_obj).full_clean()

    def test_good_image(self):
        """
        Verify that saving a valid badge image is no problem.
        """
        good = self.get_image('good')
        CourseCompleteImageConfiguration(mode='honor', icon=good).full_clean()

    def test_unbalanced_image(self):
        """
        Verify that setting an image with an uneven width and height raises an error.
        """
        unbalanced = ImageFile(self.get_image('unbalanced'))
        self.assertRaises(ValidationError, self.create_clean, unbalanced)

    def test_large_image(self):
        """
        Verify that setting an image that is too big raises an error.
        """
        large = self.get_image('large')
        self.assertRaises(ValidationError, self.create_clean, large)

    def test_no_double_default(self):
        """
        Verify that creating two configurations as default is not permitted.
        """
        CourseCompleteImageConfiguration(mode='test', icon=self.get_image('good'), default=True).save()
        self.assertRaises(
            ValidationError,
            CourseCompleteImageConfiguration(mode='test2', icon=self.get_image('good'), default=True).full_clean
        )
