"""
Tests for helpers.py
"""
from ddt import ddt, data
import hashlib
from mock import patch
from unittest import skipUnless

from django.conf import settings
from django.test import TestCase

from student.tests.factories import UserFactory

from ...models import UserProfile
from ..helpers import get_profile_image_url_for_user


@ddt
@patch('openedx.core.djangoapps.user_api.accounts.helpers._PROFILE_IMAGE_SIZES', [50, 10])
@patch.dict(
    'openedx.core.djangoapps.user_api.accounts.helpers.PROFILE_IMAGE_SIZES_MAP', {'full': 50, 'small': 10}, clear=True
)
@skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class ProfileImageUrlTestCase(TestCase):
    """
    Tests for `get_profile_image_url_for_user`.
    """
    def setUp(self):
        super(ProfileImageUrlTestCase, self).setUp()
        self.user = UserFactory()

        # Ensure that parental controls don't apply to this user
        self.user.profile.year_of_birth = 1980
        self.user.profile.save()

    def verify_url(self, user, pixels, filename):
        """
        Helper method to verify that we're correctly generating profile
        image URLs.
        """
        self.assertEqual(
            get_profile_image_url_for_user(user, pixels),
            'http://example-storage.com/profile_images/{filename}_{pixels}.jpg'.format(filename=filename, pixels=pixels)
        )

    @data(10, 50)
    def test_profile_image_urls(self, pixels):
        """
        Verify we get the URL to the default image if the user does not
        have a profile image.
        """
        # By default new users will have no profile image.
        self.verify_url(self.user, pixels, 'default')
        # A user can add an image, then remove it.  We should get the
        # default image URL in that case.
        self.user.profile.has_profile_image = True
        self.user.profile.save()
        self.verify_url(self.user, pixels, hashlib.md5('secret' + self.user.username).hexdigest())
        self.user.profile.has_profile_image = False
        self.user.profile.save()
        self.verify_url(self.user, pixels, 'default')

    @data(1, 5000)
    def test_unsupported_sizes(self, image_size):
        """
        Verify that we cannot ask for image sizes which are unsupported.
        """
        with self.assertRaises(ValueError):
            get_profile_image_url_for_user(self.user, image_size)
