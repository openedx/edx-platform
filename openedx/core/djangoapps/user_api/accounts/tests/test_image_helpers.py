"""
Tests for helpers.py
"""
import hashlib
from mock import patch
from unittest import skipUnless

from django.conf import settings
from django.test import TestCase

from ..image_helpers import get_profile_image_urls_for_user
from student.tests.factories import UserFactory

TEST_SIZES = {'full': 50, 'small': 10}


@patch.dict('openedx.core.djangoapps.user_api.accounts.image_helpers.PROFILE_IMAGE_SIZES_MAP', TEST_SIZES, clear=True)
@skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class ProfileImageUrlTestCase(TestCase):
    """
    Tests for profile image URL generation helpers.
    """
    def setUp(self):
        super(ProfileImageUrlTestCase, self).setUp()
        self.user = UserFactory()
        # Ensure that parental controls don't apply to this user
        self.user.profile.year_of_birth = 1980
        self.user.profile.has_profile_image = False
        self.user.profile.save()

    def verify_url(self, actual_url, expected_name, expected_pixels):
        """
        Verify correct url structure.
        """
        self.assertEqual(
            actual_url,
            'http://example-storage.com/profile-images/{name}_{size}.jpg'.format(
                name=expected_name, size=expected_pixels
            )
        )

    def verify_default_url(self, actual_url, expected_pixels):
        """
        Verify correct url structure for a default profile image.
        """
        self.assertEqual(
            actual_url,
            '/static/default_{size}.png'.format(size=expected_pixels)
        )

    def verify_urls(self, expected_name, actual_urls, is_default=False):
        """
        Verify correct url dictionary structure.
        """
        self.assertEqual(set(TEST_SIZES.keys()), set(actual_urls.keys()))
        for size_display_name, url in actual_urls.items():
            if is_default:
                self.verify_default_url(url, TEST_SIZES[size_display_name])
            else:
                self.verify_url(url, expected_name, TEST_SIZES[size_display_name])

    def test_get_profile_image_urls(self):
        """
        Tests `get_profile_image_urls_for_user`
        """
        self.user.profile.has_profile_image = True
        self.user.profile.save()
        expected_name = hashlib.md5('secret' + self.user.username).hexdigest()
        actual_urls = get_profile_image_urls_for_user(self.user)
        self.verify_urls(expected_name, actual_urls)

        self.user.profile.has_profile_image = False
        self.user.profile.save()
        self.verify_urls('default', get_profile_image_urls_for_user(self.user), is_default=True)
