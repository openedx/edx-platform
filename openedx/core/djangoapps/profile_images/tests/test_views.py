"""
"""

import os
from tempfile import NamedTemporaryFile

import ddt
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
import mock
from PIL import Image
from rest_framework.test import APITestCase, APIClient

from student.tests.factories import UserFactory

from ...user_api.accounts.api import set_has_profile_image, get_profile_image_names
from ...user_api.accounts.helpers import get_profile_image_storage
from ..images import DevMsg, generate_profile_images

TEST_PASSWORD = "test"


class ProfileImageEndpointTestCase(APITestCase):
    """
    Base class / shared infrastructure for tests of profile_image "upload" and
    "remove" endpoints.
    """

    # subclasses should override this with the name of the view under test, as
    # per the urls.py configuration.
    _view_name = None

    def setUp(self):
        super(ProfileImageEndpointTestCase, self).setUp()
        self.user = UserFactory.create(password=TEST_PASSWORD)
        self.url = reverse(self._view_name, kwargs={'username': self.user.username})
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        self.storage = get_profile_image_storage()
        # this assertion is made here as a sanity check because all tests
        # assume user.profile.has_profile_image is False by default
        self.assertFalse(self.user.profile.has_profile_image)

    def tearDown(self):
        for name in get_profile_image_names(self.user.username).values():
            self.storage.delete(name)

    def _make_image_file(self, dimensions=(320, 240), extension=".jpeg", force_size=None):
        """
        Returns a named temporary file created with the specified image type and options.

        Note the default dimensions are unequal (not a square) to ensure the center-square
        cropping logic will be exercised.
        """
        image = Image.new('RGB', dimensions, "green")
        image_file = NamedTemporaryFile(suffix=extension)
        image.save(image_file)
        if force_size is not None:
            image_file.seek(0, os.SEEK_END)
            bytes_to_pad = force_size - image_file.tell()
            # write in hunks of 256 bytes
            hunk, byte_ = bytearray([0] * 256), bytearray([0])
            num_hunks, remainder = divmod(bytes_to_pad, 256)
            for _ in xrange(num_hunks):
                image_file.write(hunk)
            for _ in xrange(remainder):
                image_file.write(byte_)
            image_file.flush()
        image_file.seek(0)
        return image_file

    def check_images(self, exist=True):
        """
        If exist is True, make sure the images physically exist in storage
        with correct sizes and formats.

        If exist is False, make sure none of the images exist.
        """
        for size, name in get_profile_image_names(self.user.username).items():
            if exist:
                self.assertTrue(self.storage.exists(name))
                img = Image.open(self.storage.path(name))
                self.assertEqual(img.size, (size, size))
                self.assertEqual(img.format, 'JPEG')
            else:
                self.assertFalse(self.storage.exists(name))

    def check_response(self, response, expected_code, expected_message=None):
        """
        Make sure the response has the expected code, and if that isn't 200,
        optionally check the correctness of a developer-facing message.
        """
        self.assertEqual(expected_code, response.status_code)
        if expected_code == 200:
            self.assertEqual({"status": "success"}, response.data)
        elif expected_message is not None:
            self.assertEqual(response.data.get('developer_message'), expected_message)

    def check_has_profile_image(self, has_profile_image=True):
        """
        Make sure the value of self.user.profile.has_profile_image is what we
        expect.
        """
        # it's necessary to reload this model from the database since save()
        # would have been called on another instance.
        profile = self.user.profile.__class__.objects.get(user=self.user)
        self.assertEqual(profile.has_profile_image, has_profile_image)


@ddt.ddt
class ProfileImageUploadTestCase(ProfileImageEndpointTestCase):
    """
    Tests for the profile_image upload endpoint.
    """

    _view_name = "profile_image_upload"

    def test_anonymous_access(self):
        """
        Test that an anonymous client (not logged in) cannot call GET or POST.
        """
        anonymous_client = APIClient()
        for request in (anonymous_client.get, anonymous_client.post):
            response = request(self.url)
            self.assertEqual(401, response.status_code)

    def test_upload_self(self):
        """
        Test that an authenticated user can POST to their own upload endpoint.
        """
        response = self.client.post(self.url, {'file': self._make_image_file()}, format='multipart')
        self.check_response(response, 200)
        self.check_images()
        self.check_has_profile_image()

    def test_upload_other(self):
        """
        Test that an authenticated user cannot POST to another user's upload endpoint.
        """
        different_user = UserFactory.create(password=TEST_PASSWORD)
        different_client = APIClient()
        different_client.login(username=different_user.username, password=TEST_PASSWORD)
        response = different_client.post(self.url, {'file': self._make_image_file()}, format='multipart')
        self.check_response(response, 403)
        self.check_images(False)
        self.check_has_profile_image(False)

    def test_upload_staff(self):
        """
        Test that an authenticated staff user can POST to another user's upload endpoint.
        """
        staff_user = UserFactory(is_staff=True, password=TEST_PASSWORD)
        staff_client = APIClient()
        staff_client.login(username=staff_user.username, password=TEST_PASSWORD)
        response = staff_client.post(self.url, {'file': self._make_image_file()}, format='multipart')
        self.check_response(response, 200)
        self.check_images()
        self.check_has_profile_image()

    def test_upload_missing_file(self):
        """
        Test that omitting the file entirely from the POST results in HTTP 400.
        """
        response = self.client.post(self.url, {}, format='multipart')
        self.check_response(response, 400)
        self.check_images(False)
        self.check_has_profile_image(False)

    def test_upload_not_a_file(self):
        """
        Test that sending unexpected data that isn't a file results in HTTP 400.
        """
        response = self.client.post(self.url, {'file': 'not a file'}, format='multipart')
        self.check_response(response, 400)
        self.check_images(False)
        self.check_has_profile_image(False)

    @ddt.data((1024, False), (1025, True))
    @ddt.unpack
    @override_settings(PROFILE_IMAGE_MAX_BYTES=1024)
    def test_upload_file_too_large(self, upload_size, should_fail):
        """
        """
        image_file = self._make_image_file(dimensions=(1, 1), extension=".png", force_size=upload_size)
        response = self.client.post(self.url, {'file': image_file}, format='multipart')
        if should_fail:
            self.check_response(response, 400, DevMsg.FILE_TOO_LARGE)
        else:
            self.check_response(response, 200)
        self.check_images(not should_fail)
        self.check_has_profile_image(not should_fail)

    @ddt.data((99, True), (100, False))
    @ddt.unpack
    @override_settings(PROFILE_IMAGE_MIN_BYTES=100)
    def test_upload_file_too_small(self, upload_size, should_fail):
        """
        """
        image_file = self._make_image_file(dimensions=(1, 1), extension=".png", force_size=upload_size)
        response = self.client.post(self.url, {'file': image_file}, format='multipart')
        if should_fail:
            self.check_response(response, 400, DevMsg.FILE_TOO_SMALL)
        else:
            self.check_response(response, 200)
        self.check_images(not should_fail)
        self.check_has_profile_image(not should_fail)

    def test_upload_bad_extension(self):
        """
        """
        response = self.client.post(self.url, {'file': self._make_image_file(extension=".bmp")}, format='multipart')
        self.check_response(response, 400, DevMsg.FILE_BAD_TYPE)
        self.check_images(False)
        self.check_has_profile_image(False)

    # ext / header mismatch
    def test_upload_wrong_extension(self):
        """
        """
        # make a bmp, rename it to jpeg
        bmp_file = self._make_image_file(extension=".bmp")
        fake_jpeg_file = NamedTemporaryFile(suffix=".jpeg")
        fake_jpeg_file.write(bmp_file.read())
        fake_jpeg_file.seek(0)
        response = self.client.post(self.url, {'file': fake_jpeg_file}, format='multipart')
        self.check_response(response, 400, DevMsg.FILE_BAD_EXT)
        self.check_images(False)
        self.check_has_profile_image(False)

    # content-type / header mismatch
    @mock.patch('django.test.client.mimetypes')
    def test_upload_bad_content_type(self, mock_mimetypes):
        """
        """
        mock_mimetypes.guess_type.return_value = ['image/gif']
        response = self.client.post(self.url, {'file': self._make_image_file(extension=".jpeg")}, format='multipart')
        self.check_response(response, 400, DevMsg.FILE_BAD_MIMETYPE)
        self.check_images(False)
        self.check_has_profile_image(False)

    @ddt.data(
        (1, 1), (10, 10), (100, 100), (1000, 1000),
        (1, 10), (10, 100), (100, 1000), (1000, 999)
    )
    def test_resize(self, size):
        """
        use a variety of input image sizes to ensure that the output pictures
        are all properly scaled
        """
        response = self.client.post(self.url, {'file': self._make_image_file(size)}, format='multipart')
        self.check_response(response, 200)
        self.check_images()


class ProfileImageRemoveTestCase(ProfileImageEndpointTestCase):
    """
    Tests for the profile_image remove endpoint.
    """

    _view_name = "profile_image_remove"

    def setUp(self):
        super(ProfileImageRemoveTestCase, self).setUp()
        generate_profile_images(self._make_image_file(), get_profile_image_names(self.user.username))
        self.check_images()
        set_has_profile_image(self.user.username, True)

    def test_anonymous_access(self):
        """
        Test that an anonymous client (not logged in) cannot call GET or POST.
        """
        anonymous_client = APIClient()
        for request in (anonymous_client.get, anonymous_client.post):
            response = request(self.url)
            self.assertEqual(401, response.status_code)

    def test_remove_self(self):
        """
        Test that an authenticated user can POST to remove their own profile
        images.
        """
        response = self.client.post(self.url)
        self.check_response(response, 200)
        self.check_images(False)
        self.check_has_profile_image(False)

    def test_remove_other(self):
        """
        Test that an authenticated user cannot POST to remove another user's
        profile images.
        """
        different_user = UserFactory.create(password=TEST_PASSWORD)
        different_client = APIClient()
        different_client.login(username=different_user.username, password=TEST_PASSWORD)
        response = different_client.post(self.url)
        self.check_response(response, 403)
        self.check_images(True)  # thumbnails should remain intact.
        self.check_has_profile_image(True)

    def test_remove_staff(self):
        """
        Test that an authenticated staff user can POST to remove another user's
        profile images.
        """
        staff_user = UserFactory(is_staff=True, password=TEST_PASSWORD)
        staff_client = APIClient()
        staff_client.login(username=staff_user.username, password=TEST_PASSWORD)
        response = self.client.post(self.url)
        self.check_response(response, 200)
        self.check_images(False)
        self.check_has_profile_image(False)
