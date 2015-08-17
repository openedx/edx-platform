"""
Test cases for the HTTP endpoints of the profile image api.
"""
from contextlib import closing
import datetime
from pytz import UTC
import unittest

from django.conf import settings
from django.core.urlresolvers import reverse
import mock
from mock import patch
from PIL import Image
from rest_framework.test import APITestCase, APIClient

from student.tests.factories import UserFactory
from student.tests.tests import UserSettingsEventTestMixin

from ...user_api.accounts.image_helpers import (
    set_has_profile_image,
    get_profile_image_names,
    get_profile_image_storage,
)
from ..images import create_profile_images, ImageValidationError
from ..views import LOG_MESSAGE_CREATE, LOG_MESSAGE_DELETE
from .helpers import make_image_file

TEST_PASSWORD = "test"
TEST_UPLOAD_DT = datetime.datetime(2002, 1, 9, 15, 43, 01, tzinfo=UTC)
TEST_UPLOAD_DT2 = datetime.datetime(2003, 1, 9, 15, 43, 01, tzinfo=UTC)


class ProfileImageEndpointTestCase(UserSettingsEventTestMixin, APITestCase):
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
        # Ensure that parental controls don't apply to this user
        self.user.profile.year_of_birth = 1980
        self.user.profile.save()
        self.url = reverse(self._view_name, kwargs={'username': self.user.username})
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        self.storage = get_profile_image_storage()
        self.table = 'auth_userprofile'
        # this assertion is made here as a sanity check because all tests
        # assume user.profile.has_profile_image is False by default
        self.assertFalse(self.user.profile.has_profile_image)

        # Reset the mock event tracker so that we're not considering the
        # initial profile creation events.
        self.reset_tracker()

    def tearDown(self):
        super(ProfileImageEndpointTestCase, self).tearDown()
        for name in get_profile_image_names(self.user.username).values():
            self.storage.delete(name)

    def check_images(self, exist=True):
        """
        If exist is True, make sure the images physically exist in storage
        with correct sizes and formats.

        If exist is False, make sure none of the images exist.
        """
        for size, name in get_profile_image_names(self.user.username).items():
            if exist:
                self.assertTrue(self.storage.exists(name))
                with closing(Image.open(self.storage.path(name))) as img:
                    self.assertEqual(img.size, (size, size))
                    self.assertEqual(img.format, 'JPEG')
            else:
                self.assertFalse(self.storage.exists(name))

    def check_response(self, response, expected_code, expected_developer_message=None, expected_user_message=None):
        """
        Make sure the response has the expected code, and if that isn't 204,
        optionally check the correctness of a developer-facing message.
        """
        self.assertEqual(expected_code, response.status_code)
        if expected_code == 204:
            self.assertIsNone(response.data)
        else:
            if expected_developer_message is not None:
                self.assertEqual(response.data.get('developer_message'), expected_developer_message)
            if expected_user_message is not None:
                self.assertEqual(response.data.get('user_message'), expected_user_message)

    def check_has_profile_image(self, has_profile_image=True):
        """
        Make sure the value of self.user.profile.has_profile_image is what we
        expect.
        """
        # it's necessary to reload this model from the database since save()
        # would have been called on another instance.
        profile = self.user.profile.__class__.objects.get(user=self.user)
        self.assertEqual(profile.has_profile_image, has_profile_image)


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Profile Image API is only supported in LMS')
@mock.patch('openedx.core.djangoapps.profile_images.views.log')
class ProfileImageUploadTestCase(ProfileImageEndpointTestCase):
    """
    Tests for the profile_image upload endpoint.
    """
    _view_name = "profile_image_upload"

    def check_upload_event_emitted(self, old=None, new=TEST_UPLOAD_DT):
        """
        Make sure we emit a UserProfile event corresponding to the
        profile_image_uploaded_at field changing.
        """
        self.assert_user_setting_event_emitted(
            setting='profile_image_uploaded_at', old=old, new=new
        )

    def test_unsupported_methods(self, mock_log):
        """
        Test that GET, PUT, PATCH, and DELETE are not supported.
        """
        self.assertEqual(405, self.client.get(self.url).status_code)
        self.assertEqual(405, self.client.put(self.url).status_code)
        self.assertEqual(405, self.client.patch(self.url).status_code)
        self.assertEqual(405, self.client.delete(self.url).status_code)
        self.assertFalse(mock_log.info.called)
        self.assert_no_events_were_emitted()

    def test_anonymous_access(self, mock_log):
        """
        Test that an anonymous client (not logged in) cannot POST.
        """
        anonymous_client = APIClient()
        response = anonymous_client.post(self.url)
        self.assertEqual(401, response.status_code)
        self.assertFalse(mock_log.info.called)
        self.assert_no_events_were_emitted()

    @patch('openedx.core.djangoapps.profile_images.views._make_upload_dt', side_effect=[TEST_UPLOAD_DT, TEST_UPLOAD_DT2])
    def test_upload_self(self, mock_make_image_version, mock_log):  # pylint: disable=unused-argument
        """
        Test that an authenticated user can POST to their own upload endpoint.
        """
        with make_image_file() as image_file:
            response = self.client.post(self.url, {'file': image_file}, format='multipart')
            self.check_response(response, 204)
            self.check_images()
            self.check_has_profile_image()
        mock_log.info.assert_called_once_with(
            LOG_MESSAGE_CREATE,
            {'image_names': get_profile_image_names(self.user.username).values(), 'user_id': self.user.id}
        )
        self.check_upload_event_emitted()

        # Try another upload and make sure that a second event is emitted.
        with make_image_file() as image_file:
            response = self.client.post(self.url, {'file': image_file}, format='multipart')
            self.check_response(response, 204)

        self.check_upload_event_emitted(old=TEST_UPLOAD_DT, new=TEST_UPLOAD_DT2)

    def test_upload_other(self, mock_log):
        """
        Test that an authenticated user cannot POST to another user's upload endpoint.
        """
        different_user = UserFactory.create(password=TEST_PASSWORD)
        # Ignore UserProfileFactory creation events.
        self.reset_tracker()
        different_client = APIClient()
        different_client.login(username=different_user.username, password=TEST_PASSWORD)
        with make_image_file() as image_file:
            response = different_client.post(self.url, {'file': image_file}, format='multipart')
            self.check_response(response, 404)
            self.check_images(False)
            self.check_has_profile_image(False)
        self.assertFalse(mock_log.info.called)
        self.assert_no_events_were_emitted()

    def test_upload_staff(self, mock_log):
        """
        Test that an authenticated staff cannot POST to another user's upload endpoint.
        """
        staff_user = UserFactory(is_staff=True, password=TEST_PASSWORD)
        # Ignore UserProfileFactory creation events.
        self.reset_tracker()
        staff_client = APIClient()
        staff_client.login(username=staff_user.username, password=TEST_PASSWORD)
        with make_image_file() as image_file:
            response = staff_client.post(self.url, {'file': image_file}, format='multipart')
            self.check_response(response, 403)
            self.check_images(False)
            self.check_has_profile_image(False)
        self.assertFalse(mock_log.info.called)
        self.assert_no_events_were_emitted()

    def test_upload_missing_file(self, mock_log):
        """
        Test that omitting the file entirely from the POST results in HTTP 400.
        """
        response = self.client.post(self.url, {}, format='multipart')
        self.check_response(
            response, 400,
            expected_developer_message=u"No file provided for profile image",
            expected_user_message=u"No file provided for profile image",
        )
        self.check_images(False)
        self.check_has_profile_image(False)
        self.assertFalse(mock_log.info.called)
        self.assert_no_events_were_emitted()

    def test_upload_not_a_file(self, mock_log):
        """
        Test that sending unexpected data that isn't a file results in HTTP
        400.
        """
        response = self.client.post(self.url, {'file': 'not a file'}, format='multipart')
        self.check_response(
            response, 400,
            expected_developer_message=u"No file provided for profile image",
            expected_user_message=u"No file provided for profile image",
        )
        self.check_images(False)
        self.check_has_profile_image(False)
        self.assertFalse(mock_log.info.called)
        self.assert_no_events_were_emitted()

    def test_upload_validation(self, mock_log):
        """
        Test that when upload validation fails, the proper HTTP response and
        messages are returned.
        """
        with make_image_file() as image_file:
            with mock.patch(
                'openedx.core.djangoapps.profile_images.views.validate_uploaded_image',
                side_effect=ImageValidationError(u"test error message")
            ):
                response = self.client.post(self.url, {'file': image_file}, format='multipart')
                self.check_response(
                    response, 400,
                    expected_developer_message=u"test error message",
                    expected_user_message=u"test error message",
                )
                self.check_images(False)
                self.check_has_profile_image(False)
        self.assertFalse(mock_log.info.called)
        self.assert_no_events_were_emitted()

    @patch('PIL.Image.open')
    def test_upload_failure(self, image_open, mock_log):
        """
        Test that when upload validation fails, the proper HTTP response and
        messages are returned.
        """
        image_open.side_effect = [Exception(u"whoops"), None]
        with make_image_file() as image_file:
            with self.assertRaises(Exception):
                self.client.post(self.url, {'file': image_file}, format='multipart')
            self.check_images(False)
            self.check_has_profile_image(False)
        self.assertFalse(mock_log.info.called)
        self.assert_no_events_were_emitted()


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Profile Image API is only supported in LMS')
@mock.patch('openedx.core.djangoapps.profile_images.views.log')
class ProfileImageRemoveTestCase(ProfileImageEndpointTestCase):
    """
    Tests for the profile_image remove endpoint.
    """
    _view_name = "profile_image_remove"

    def setUp(self):
        super(ProfileImageRemoveTestCase, self).setUp()
        with make_image_file() as image_file:
            create_profile_images(image_file, get_profile_image_names(self.user.username))
            self.check_images()
            set_has_profile_image(self.user.username, True, TEST_UPLOAD_DT)
            # Ignore previous event
            self.reset_tracker()

    def check_remove_event_emitted(self):
        """
        Make sure we emit a UserProfile event corresponding to the
        profile_image_uploaded_at field changing.
        """
        self.assert_user_setting_event_emitted(
            setting='profile_image_uploaded_at', old=TEST_UPLOAD_DT, new=None
        )

    def test_unsupported_methods(self, mock_log):
        """
        Test that GET, PUT, PATCH, and DELETE are not supported.
        """
        self.assertEqual(405, self.client.get(self.url).status_code)
        self.assertEqual(405, self.client.put(self.url).status_code)
        self.assertEqual(405, self.client.patch(self.url).status_code)
        self.assertEqual(405, self.client.delete(self.url).status_code)
        self.assertFalse(mock_log.info.called)
        self.assert_no_events_were_emitted()

    def test_anonymous_access(self, mock_log):
        """
        Test that an anonymous client (not logged in) cannot call GET or POST.
        """
        anonymous_client = APIClient()
        for request in (anonymous_client.get, anonymous_client.post):
            response = request(self.url)
            self.assertEqual(401, response.status_code)
        self.assertFalse(mock_log.info.called)
        self.assert_no_events_were_emitted()

    def test_remove_self(self, mock_log):
        """
        Test that an authenticated user can POST to remove their own profile
        images.
        """
        response = self.client.post(self.url)
        self.check_response(response, 204)
        self.check_images(False)
        self.check_has_profile_image(False)
        mock_log.info.assert_called_once_with(
            LOG_MESSAGE_DELETE,
            {'image_names': get_profile_image_names(self.user.username).values(), 'user_id': self.user.id}
        )
        self.check_remove_event_emitted()

    def test_remove_other(self, mock_log):
        """
        Test that an authenticated user cannot POST to remove another user's
        profile images.
        """
        different_user = UserFactory.create(password=TEST_PASSWORD)
        # Ignore UserProfileFactory creation events.
        self.reset_tracker()
        different_client = APIClient()
        different_client.login(username=different_user.username, password=TEST_PASSWORD)
        response = different_client.post(self.url)
        self.check_response(response, 404)
        self.check_images(True)  # thumbnails should remain intact.
        self.check_has_profile_image(True)
        self.assertFalse(mock_log.info.called)
        self.assert_no_events_were_emitted()

    def test_remove_staff(self, mock_log):
        """
        Test that an authenticated staff user can POST to remove another user's
        profile images.
        """
        staff_user = UserFactory(is_staff=True, password=TEST_PASSWORD)
        staff_client = APIClient()
        staff_client.login(username=staff_user.username, password=TEST_PASSWORD)
        response = self.client.post(self.url)
        self.check_response(response, 204)
        self.check_images(False)
        self.check_has_profile_image(False)
        mock_log.info.assert_called_once_with(
            LOG_MESSAGE_DELETE,
            {'image_names': get_profile_image_names(self.user.username).values(), 'user_id': self.user.id}
        )
        self.check_remove_event_emitted()

    @patch('student.models.UserProfile.save')
    def test_remove_failure(self, user_profile_save, mock_log):
        """
        Test that when upload validation fails, the proper HTTP response and
        messages are returned.
        """
        user_profile_save.side_effect = [Exception(u"whoops"), None]
        with self.assertRaises(Exception):
            self.client.post(self.url)
        self.check_images(True)  # thumbnails should remain intact.
        self.check_has_profile_image(True)
        self.assertFalse(mock_log.info.called)
        self.assert_no_events_were_emitted()
