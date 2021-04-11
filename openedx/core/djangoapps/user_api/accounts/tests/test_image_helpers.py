"""
Tests for helpers.py
"""


import datetime
import hashlib

from django.test import TestCase
from mock import patch
from pytz import UTC

from openedx.core.djangolib.testing.utils import skip_unless_lms
from common.djangoapps.student.tests.factories import UserFactory
from six import text_type

from ..image_helpers import get_profile_image_urls_for_user

TEST_SIZES = {'full': 50, 'small': 10}
TEST_PROFILE_IMAGE_UPLOAD_DT = datetime.datetime(2002, 1, 9, 15, 43, 1, tzinfo=UTC)


@patch.dict('django.conf.settings.PROFILE_IMAGE_SIZES_MAP', TEST_SIZES, clear=True)
@skip_unless_lms
class ProfileImageUrlTestCase(TestCase):
    """
    Tests for profile image URL generation helpers.
    """

    def setUp(self):
        super(ProfileImageUrlTestCase, self).setUp()
        self.user = UserFactory()
        # Ensure that parental controls don't apply to this user
        self.user.profile.year_of_birth = 1980
        self.user.profile.profile_image_uploaded_at = TEST_PROFILE_IMAGE_UPLOAD_DT
        self.user.profile.save()

    def verify_url(self, actual_url, expected_name, expected_pixels, expected_version):
        """
        Verify correct url structure.
        """
        self.assertEqual(
            actual_url,
            'http://example-storage.com/profile-images/{name}_{size}.jpg?v={version}'.format(
                name=expected_name, size=expected_pixels, version=expected_version
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

    def verify_urls(self, actual_urls, expected_name, is_default=False):
        """
        Verify correct url dictionary structure.
        """
        self.assertEqual(set(TEST_SIZES.keys()), set(actual_urls.keys()))
        for size_display_name, url in actual_urls.items():
            if is_default:
                self.verify_default_url(url, TEST_SIZES[size_display_name])
            else:
                self.verify_url(
                    url, expected_name, TEST_SIZES[size_display_name], TEST_PROFILE_IMAGE_UPLOAD_DT.strftime("%s")
                )

    def test_get_profile_image_urls(self):
        """
        Tests `get_profile_image_urls_for_user`
        """
        self.user.profile.profile_image_uploaded_at = TEST_PROFILE_IMAGE_UPLOAD_DT
        self.user.profile.save()
        expected_name = hashlib.md5((
            'secret' + text_type(self.user.username)).encode('utf-8')).hexdigest()
        actual_urls = get_profile_image_urls_for_user(self.user)
        self.verify_urls(actual_urls, expected_name, is_default=False)

        self.user.profile.profile_image_uploaded_at = None
        self.user.profile.save()
        self.verify_urls(get_profile_image_urls_for_user(self.user), 'default', is_default=True)
