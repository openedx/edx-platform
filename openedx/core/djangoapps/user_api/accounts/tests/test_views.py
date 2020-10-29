# -*- coding: utf-8 -*-
"""
Test cases to cover Accounts-related behaviors of the User API application
"""


import datetime
import hashlib
import json
from copy import deepcopy

import ddt
import mock
import pytz
import six
from django.conf import settings
from django.test.testcases import TransactionTestCase
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from six.moves import range

from openedx.core.djangoapps.oauth_dispatch.jwt import create_jwt_for_user
from openedx.core.djangoapps.user_api.accounts import ACCOUNT_VISIBILITY_PREF_KEY
from openedx.core.djangoapps.user_api.models import UserPreference
from openedx.core.djangoapps.user_api.preferences.api import set_user_preference
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms
from common.djangoapps.student.models import PendingEmailChange, UserProfile
from common.djangoapps.student.tests.factories import TEST_PASSWORD, UserFactory

from .. import ALL_USERS_VISIBILITY, CUSTOM_VISIBILITY, PRIVATE_VISIBILITY

TEST_PROFILE_IMAGE_UPLOADED_AT = datetime.datetime(2002, 1, 9, 15, 43, 1, tzinfo=pytz.UTC)

# this is used in one test to check the behavior of profile image url
# generation with a relative url in the config.
TEST_PROFILE_IMAGE_BACKEND = deepcopy(settings.PROFILE_IMAGE_BACKEND)
TEST_PROFILE_IMAGE_BACKEND['options']['base_url'] = '/profile-images/'

TEST_BIO_VALUE = u"Tired mother of twins"
TEST_LANGUAGE_PROFICIENCY_CODE = u"hi"


class UserAPITestCase(APITestCase):
    """
    The base class for all tests of the User API
    """

    def setUp(self):
        super(UserAPITestCase, self).setUp()

        self.anonymous_client = APIClient()
        self.different_user = UserFactory.create(password=TEST_PASSWORD)
        self.different_client = APIClient()
        self.staff_user = UserFactory(is_staff=True, password=TEST_PASSWORD)
        self.staff_client = APIClient()
        self.user = UserFactory.create(password=TEST_PASSWORD)  # will be assigned to self.client by default

    def login_client(self, api_client, user):
        """Helper method for getting the client and user and logging in. Returns client. """
        client = getattr(self, api_client)
        user = getattr(self, user)
        client.login(username=user.username, password=TEST_PASSWORD)
        return client

    def send_patch(self, client, json_data, content_type="application/merge-patch+json", expected_status=200):
        """
        Helper method for sending a patch to the server, defaulting to application/merge-patch+json content_type.
        Verifies the expected status and returns the response.
        """
        # pylint: disable=no-member
        response = client.patch(self.url, data=json.dumps(json_data), content_type=content_type)
        self.assertEqual(expected_status, response.status_code)
        return response

    def send_get(self, client, query_parameters=None, expected_status=200):
        """
        Helper method for sending a GET to the server. Verifies the expected status and returns the response.
        """
        url = self.url + '?' + query_parameters if query_parameters else self.url    # pylint: disable=no-member
        response = client.get(url)
        self.assertEqual(expected_status, response.status_code)
        return response

    # pylint: disable=no-member
    def send_put(self, client, json_data, content_type="application/json", expected_status=204):
        """
        Helper method for sending a PUT to the server. Verifies the expected status and returns the response.
        """
        response = client.put(self.url, data=json.dumps(json_data), content_type=content_type)
        self.assertEqual(expected_status, response.status_code)
        return response

    # pylint: disable=no-member
    def send_delete(self, client, expected_status=204):
        """
        Helper method for sending a DELETE to the server. Verifies the expected status and returns the response.
        """
        response = client.delete(self.url)
        self.assertEqual(expected_status, response.status_code)
        return response

    def create_mock_profile(self, user):
        """
        Helper method that creates a mock profile for the specified user
        :return:
        """
        legacy_profile = UserProfile.objects.get(id=user.id)
        legacy_profile.country = "US"
        legacy_profile.state = "MA"
        legacy_profile.level_of_education = "m"
        legacy_profile.year_of_birth = 2000
        legacy_profile.goals = "world peace"
        legacy_profile.mailing_address = "Park Ave"
        legacy_profile.gender = "f"
        legacy_profile.bio = TEST_BIO_VALUE
        legacy_profile.profile_image_uploaded_at = TEST_PROFILE_IMAGE_UPLOADED_AT
        legacy_profile.language_proficiencies.create(code=TEST_LANGUAGE_PROFICIENCY_CODE)
        legacy_profile.phone_number = "+18005555555"
        legacy_profile.save()

    def _verify_profile_image_data(self, data, has_profile_image):
        """
        Verify the profile image data in a GET response for self.user
        corresponds to whether the user has or hasn't set a profile
        image.
        """
        template = '{root}/{filename}_{{size}}.{extension}'
        if has_profile_image:
            url_root = 'http://example-storage.com/profile-images'
            filename = hashlib.md5(('secret' + self.user.username).encode('utf-8')).hexdigest()
            file_extension = 'jpg'
            template += '?v={}'.format(TEST_PROFILE_IMAGE_UPLOADED_AT.strftime("%s"))
        else:
            url_root = 'http://testserver/static'
            filename = 'default'
            file_extension = 'png'
        template = template.format(root=url_root, filename=filename, extension=file_extension)
        self.assertEqual(
            data['profile_image'],
            {
                'has_image': has_profile_image,
                'image_url_full': template.format(size=50),
                'image_url_small': template.format(size=10),
            }
        )


@ddt.ddt
@skip_unless_lms
class TestOwnUsernameAPI(CacheIsolationTestCase, UserAPITestCase):
    """
    Unit tests for the Accounts API.
    """

    ENABLED_CACHES = ['default']

    def setUp(self):
        super(TestOwnUsernameAPI, self).setUp()

        self.url = reverse("own_username_api")

    def _verify_get_own_username(self, queries, expected_status=200):
        """
        Internal helper to perform the actual assertion
        """
        with self.assertNumQueries(queries):
            response = self.send_get(self.client, expected_status=expected_status)
        if expected_status == 200:
            data = response.data
            self.assertEqual(1, len(data))
            self.assertEqual(self.user.username, data["username"])

    def test_get_username(self):
        """
        Test that a client (logged in) can get her own username.
        """
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        self._verify_get_own_username(17)

    def test_get_username_inactive(self):
        """
        Test that a logged-in client can get their
        username, even if inactive.
        """
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        self.user.is_active = False
        self.user.save()
        self._verify_get_own_username(17)

    def test_get_username_not_logged_in(self):
        """
        Test that a client (not logged in) gets a 401
        when trying to retrieve their username.
        """

        # verify that the endpoint is inaccessible when not logged in
        self._verify_get_own_username(13, expected_status=401)


@ddt.ddt
@skip_unless_lms
@mock.patch('openedx.core.djangoapps.user_api.accounts.image_helpers._PROFILE_IMAGE_SIZES', [50, 10])
@mock.patch.dict(
    'django.conf.settings.PROFILE_IMAGE_SIZES_MAP',
    {'full': 50, 'small': 10},
    clear=True
)
class TestAccountsAPI(CacheIsolationTestCase, UserAPITestCase):
    """
    Unit tests for the Accounts API.
    """

    ENABLED_CACHES = ['default']

    def setUp(self):
        super(TestAccountsAPI, self).setUp()

        self.url = reverse("accounts_api", kwargs={'username': self.user.username})

    def _set_user_age_to_10_years(self, user):
        """
        Sets the given user's age to 10.
        Returns the calculated year of birth.
        """
        legacy_profile = UserProfile.objects.get(id=user.id)
        current_year = datetime.datetime.now().year
        year_of_birth = current_year - 10
        legacy_profile.year_of_birth = year_of_birth
        legacy_profile.save()
        return year_of_birth

    def _verify_full_shareable_account_response(self, response, account_privacy=None, badges_enabled=False):
        """
        Verify that the shareable fields from the account are returned
        """
        data = response.data
        self.assertEqual(12, len(data))

        # public fields (3)
        self.assertEqual(account_privacy, data["account_privacy"])
        self._verify_profile_image_data(data, True)
        self.assertEqual(self.user.username, data["username"])

        # additional shareable fields (8)
        self.assertEqual(TEST_BIO_VALUE, data["bio"])
        self.assertEqual("US", data["country"])
        self.assertIsNotNone(data["date_joined"])
        self.assertEqual([{"code": TEST_LANGUAGE_PROFICIENCY_CODE}], data["language_proficiencies"])
        self.assertEqual("m", data["level_of_education"])
        self.assertIsNotNone(data["social_links"])
        self.assertIsNone(data["time_zone"])
        self.assertEqual(badges_enabled, data['accomplishments_shared'])

    def _verify_private_account_response(self, response, requires_parental_consent=False):
        """
        Verify that only the public fields are returned if a user does not want to share account fields
        """
        data = response.data
        self.assertEqual(3, len(data))
        self.assertEqual(PRIVATE_VISIBILITY, data["account_privacy"])
        self._verify_profile_image_data(data, not requires_parental_consent)
        self.assertEqual(self.user.username, data["username"])

    def _verify_full_account_response(self, response, requires_parental_consent=False, year_of_birth=2000):
        """
        Verify that all account fields are returned (even those that are not shareable).
        """
        data = response.data
        self.assertEqual(25, len(data))

        # public fields (3)
        expected_account_privacy = (
            PRIVATE_VISIBILITY if requires_parental_consent else
            UserPreference.get_value(self.user, 'account_privacy')
        )
        self.assertEqual(expected_account_privacy, data["account_privacy"])
        self._verify_profile_image_data(data, not requires_parental_consent)
        self.assertEqual(self.user.username, data["username"])

        # additional shareable fields (8)
        self.assertEqual(TEST_BIO_VALUE, data["bio"])
        self.assertEqual("US", data["country"])
        self.assertIsNotNone(data["date_joined"])
        self.assertEqual([{"code": TEST_LANGUAGE_PROFICIENCY_CODE}], data["language_proficiencies"])
        self.assertEqual("m", data["level_of_education"])
        self.assertIsNotNone(data["social_links"])
        self.assertEqual(UserPreference.get_value(self.user, 'time_zone'), data["time_zone"])
        self.assertIsNotNone(data["accomplishments_shared"])
        self.assertEqual(self.user.first_name + " " + self.user.last_name, data["name"])

        # additional admin fields (10)
        self.assertEqual(self.user.email, data["email"])
        self.assertIsNotNone(data["extended_profile"])
        self.assertEqual("MA", data["state"])
        self.assertEqual("f", data["gender"])
        self.assertEqual("world peace", data["goals"])
        self.assertTrue(data["is_active"])
        self.assertEqual("Park Ave", data['mailing_address'])
        self.assertEqual(requires_parental_consent, data["requires_parental_consent"])
        self.assertIsNone(data["secondary_email"])
        self.assertIsNone(data["secondary_email_enabled"])
        self.assertEqual(year_of_birth, data["year_of_birth"])

    def test_anonymous_access(self):
        """
        Test that an anonymous client (not logged in) cannot call GET or PATCH.
        """
        self.send_get(self.anonymous_client, expected_status=401)
        self.send_patch(self.anonymous_client, {}, expected_status=401)

    def test_unsupported_methods(self):
        """
        Test that DELETE, POST, and PUT are not supported.
        """
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        self.assertEqual(405, self.client.put(self.url).status_code)
        self.assertEqual(405, self.client.post(self.url).status_code)
        self.assertEqual(405, self.client.delete(self.url).status_code)

    @ddt.data(
        ("client", "user"),
        ("staff_client", "staff_user"),
    )
    @ddt.unpack
    def test_get_account_unknown_user(self, api_client, user):
        """
        Test that requesting a user who does not exist returns a 404.
        """
        client = self.login_client(api_client, user)
        response = client.get(reverse("accounts_api", kwargs={'username': "does_not_exist"}))
        self.assertEqual(404, response.status_code)

    @ddt.data(
        ("client", "user"),
        ("staff_client", "staff_user"),
    )
    @ddt.unpack
    def test_get_account_by_email(self, api_client, user):
        """
        Test that requesting a user email search works.
        """
        client = self.login_client(api_client, user)
        self.create_mock_profile(self.user)
        set_user_preference(self.user, ACCOUNT_VISIBILITY_PREF_KEY, PRIVATE_VISIBILITY)

        response = self.send_get(client, query_parameters='email={}'.format(self.user.email))
        self._verify_full_account_response(response)

    # Note: using getattr so that the patching works even if there is no configuration.
    # This is needed when testing CMS as the patching is still executed even though the
    # suite is skipped.
    @mock.patch.dict(getattr(settings, "ACCOUNT_VISIBILITY_CONFIGURATION", {}), {"default_visibility": "all_users"})
    def test_get_account_different_user_visible(self):
        """
        Test that a client (logged in) can only get the shareable fields for a different user.
        This is the case when default_visibility is set to "all_users".
        """
        self.different_client.login(username=self.different_user.username, password=TEST_PASSWORD)
        self.create_mock_profile(self.user)
        with self.assertNumQueries(24):
            response = self.send_get(self.different_client)
        self._verify_full_shareable_account_response(response, account_privacy=ALL_USERS_VISIBILITY)

    # Note: using getattr so that the patching works even if there is no configuration.
    # This is needed when testing CMS as the patching is still executed even though the
    # suite is skipped.
    @mock.patch.dict(getattr(settings, "ACCOUNT_VISIBILITY_CONFIGURATION", {}), {"default_visibility": "private"})
    def test_get_account_different_user_private(self):
        """
        Test that a client (logged in) can only get the shareable fields for a different user.
        This is the case when default_visibility is set to "private".
        """
        self.different_client.login(username=self.different_user.username, password=TEST_PASSWORD)
        self.create_mock_profile(self.user)
        with self.assertNumQueries(24):
            response = self.send_get(self.different_client)
        self._verify_private_account_response(response)

    @mock.patch.dict(settings.FEATURES, {'ENABLE_OPENBADGES': True})
    @ddt.data(
        ("client", "user", PRIVATE_VISIBILITY),
        ("different_client", "different_user", PRIVATE_VISIBILITY),
        ("staff_client", "staff_user", PRIVATE_VISIBILITY),
        ("client", "user", ALL_USERS_VISIBILITY),
        ("different_client", "different_user", ALL_USERS_VISIBILITY),
        ("staff_client", "staff_user", ALL_USERS_VISIBILITY),
    )
    @ddt.unpack
    def test_get_account_private_visibility(self, api_client, requesting_username, preference_visibility):
        """
        Test the return from GET based on user visibility setting.
        """
        def verify_fields_visible_to_all_users(response):
            """
            Confirms that private fields are private, and public/shareable fields are public/shareable
            """
            if preference_visibility == PRIVATE_VISIBILITY:
                self._verify_private_account_response(response)
            else:
                self._verify_full_shareable_account_response(response, ALL_USERS_VISIBILITY, badges_enabled=True)

        client = self.login_client(api_client, requesting_username)

        # Update user account visibility setting.
        set_user_preference(self.user, ACCOUNT_VISIBILITY_PREF_KEY, preference_visibility)
        self.create_mock_profile(self.user)
        response = self.send_get(client)

        if requesting_username == "different_user":
            verify_fields_visible_to_all_users(response)
        else:
            self._verify_full_account_response(response)

        # Verify how the view parameter changes the fields that are returned.
        response = self.send_get(client, query_parameters='view=shared')
        verify_fields_visible_to_all_users(response)

        response = self.send_get(client, query_parameters='view=shared&email={}'.format(self.user.email))
        verify_fields_visible_to_all_users(response)

    @ddt.data(
        ("client", "user"),
        ("staff_client", "staff_user"),
        ("different_client", "different_user"),
    )
    @ddt.unpack
    def test_custom_visibility_over_age(self, api_client, requesting_username):
        self.create_mock_profile(self.user)
        # set user's custom visibility preferences
        set_user_preference(self.user, ACCOUNT_VISIBILITY_PREF_KEY, CUSTOM_VISIBILITY)
        shared_fields = ("bio", "language_proficiencies", "name")
        for field_name in shared_fields:
            set_user_preference(self.user, "visibility.{}".format(field_name), ALL_USERS_VISIBILITY)

        # make API request
        client = self.login_client(api_client, requesting_username)
        response = self.send_get(client)

        # verify response
        if requesting_username == "different_user":
            data = response.data
            self.assertEqual(6, len(data))

            # public fields
            self.assertEqual(self.user.username, data["username"])
            self.assertEqual(UserPreference.get_value(self.user, 'account_privacy'), data["account_privacy"])
            self._verify_profile_image_data(data, has_profile_image=True)

            # custom shared fields
            self.assertEqual(TEST_BIO_VALUE, data["bio"])
            self.assertEqual([{"code": TEST_LANGUAGE_PROFICIENCY_CODE}], data["language_proficiencies"])
            self.assertEqual(self.user.first_name + " " + self.user.last_name, data["name"])
        else:
            self._verify_full_account_response(response)

    @ddt.data(
        ("client", "user"),
        ("staff_client", "staff_user"),
        ("different_client", "different_user"),
    )
    @ddt.unpack
    def test_custom_visibility_under_age(self, api_client, requesting_username):
        self.create_mock_profile(self.user)
        year_of_birth = self._set_user_age_to_10_years(self.user)

        # set user's custom visibility preferences
        set_user_preference(self.user, ACCOUNT_VISIBILITY_PREF_KEY, CUSTOM_VISIBILITY)
        shared_fields = ("bio", "language_proficiencies")
        for field_name in shared_fields:
            set_user_preference(self.user, "visibility.{}".format(field_name), ALL_USERS_VISIBILITY)

        # make API request
        client = self.login_client(api_client, requesting_username)
        response = self.send_get(client)

        # verify response
        if requesting_username == "different_user":
            self._verify_private_account_response(response, requires_parental_consent=True)
        else:
            self._verify_full_account_response(
                response,
                requires_parental_consent=True,
                year_of_birth=year_of_birth,
            )

    def test_get_account_default(self):
        """
        Test that a client (logged in) can get her own account information (using default legacy profile information,
        as created by the test UserFactory).
        """

        def verify_get_own_information(queries):
            """
            Internal helper to perform the actual assertions
            """
            with self.assertNumQueries(queries):
                response = self.send_get(self.client)
            data = response.data
            self.assertEqual(25, len(data))
            self.assertEqual(self.user.username, data["username"])
            self.assertEqual(self.user.first_name + " " + self.user.last_name, data["name"])
            for empty_field in ("year_of_birth", "level_of_education", "mailing_address", "bio"):
                self.assertIsNone(data[empty_field])
            self.assertIsNone(data["country"])
            self.assertIsNone(data["state"])
            self.assertEqual("m", data["gender"])
            self.assertEqual("Learn a lot", data["goals"])
            self.assertEqual(self.user.email, data["email"])
            self.assertIsNotNone(data["date_joined"])
            self.assertEqual(self.user.is_active, data["is_active"])
            self._verify_profile_image_data(data, False)
            self.assertTrue(data["requires_parental_consent"])
            self.assertEqual([], data["language_proficiencies"])
            self.assertEqual(PRIVATE_VISIBILITY, data["account_privacy"])
            self.assertIsNone(data["time_zone"])
            # Badges aren't on by default, so should not be present.
            self.assertEqual(False, data["accomplishments_shared"])

        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        verify_get_own_information(22)

        # Now make sure that the user can get the same information, even if not active
        self.user.is_active = False
        self.user.save()
        verify_get_own_information(14)

    def test_get_account_empty_string(self):
        """
        Test the conversion of empty strings to None for certain fields.
        """
        legacy_profile = UserProfile.objects.get(id=self.user.id)
        legacy_profile.country = ""
        legacy_profile.state = ""
        legacy_profile.level_of_education = ""
        legacy_profile.gender = ""
        legacy_profile.bio = ""
        legacy_profile.save()

        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        with self.assertNumQueries(22):
            response = self.send_get(self.client)
        for empty_field in ("level_of_education", "gender", "country", "state", "bio",):
            self.assertIsNone(response.data[empty_field])

    @ddt.data(
        ("different_client", "different_user"),
        ("staff_client", "staff_user"),
    )
    @ddt.unpack
    def test_patch_account_disallowed_user(self, api_client, user):
        """
        Test that a client cannot call PATCH on a different client's user account (even with
        is_staff access).
        """
        client = self.login_client(api_client, user)
        self.send_patch(client, {}, expected_status=403)

    @ddt.data(
        ("client", "user"),
        ("staff_client", "staff_user"),
    )
    @ddt.unpack
    def test_patch_account_unknown_user(self, api_client, user):
        """
        Test that trying to update a user who does not exist returns a 403.
        """
        client = self.login_client(api_client, user)
        response = client.patch(
            reverse("accounts_api", kwargs={'username': "does_not_exist"}),
            data=json.dumps({}), content_type="application/merge-patch+json"
        )
        self.assertEqual(403, response.status_code)

    @ddt.data(
        ("gender", "f", "not a gender", u'"not a gender" is not a valid choice.'),
        ("level_of_education", "none", u"ȻħȺɍłɇs", u'"ȻħȺɍłɇs" is not a valid choice.'),
        ("country", "GB", "XY", u'"XY" is not a valid choice.'),
        ("state", "MA", "PY", u'"PY" is not a valid choice.'),
        ("year_of_birth", 2009, "not_an_int", u"A valid integer is required."),
        ("name", "bob", "z" * 256, u"Ensure this field has no more than 255 characters."),
        ("name", u"ȻħȺɍłɇs", "   ", u"The name field must be at least 1 character long."),
        ("goals", "Smell the roses"),
        ("mailing_address", "Sesame Street"),
        # Note that we store the raw data, so it is up to client to escape the HTML.
        (
            "bio", u"<html>Lacrosse-playing superhero 壓是進界推日不復女</html>",
            "z" * 301, u"The about me field must be at most 300 characters long."
        ),
        ("account_privacy", ALL_USERS_VISIBILITY),
        ("account_privacy", PRIVATE_VISIBILITY),
        # Note that email is tested below, as it is not immediately updated.
        # Note that language_proficiencies is tested below as there are multiple error and success conditions.
    )
    @ddt.unpack
    def test_patch_account(self, field, value, fails_validation_value=None, developer_validation_message=None):
        """
        Test the behavior of patch, when using the correct content_type.
        """
        client = self.login_client("client", "user")

        if field == 'account_privacy':
            # Ensure the user has birth year set, and is over 13, so
            # account_privacy behaves normally
            legacy_profile = UserProfile.objects.get(id=self.user.id)
            legacy_profile.year_of_birth = 2000
            legacy_profile.save()

        response = self.send_patch(client, {field: value})
        self.assertEqual(value, response.data[field])

        if fails_validation_value:
            error_response = self.send_patch(client, {field: fails_validation_value}, expected_status=400)
            expected_user_message = u'This value is invalid.'
            if field == 'bio':
                expected_user_message = u"The about me field must be at most 300 characters long."

            self.assertEqual(
                expected_user_message,
                error_response.data["field_errors"][field]["user_message"]
            )

            self.assertEqual(
                u"Value '{value}' is not valid for field '{field}': {messages}".format(
                    value=fails_validation_value, field=field, messages=[developer_validation_message]
                ),
                error_response.data["field_errors"][field]["developer_message"]
            )
        elif field != "account_privacy":
            # If there are no values that would fail validation, then empty string should be supported;
            # except for account_privacy, which cannot be an empty string.
            response = self.send_patch(client, {field: ""})
            self.assertEqual("", response.data[field])

    def test_patch_inactive_user(self):
        """ Verify that a user can patch her own account, even if inactive. """
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        self.user.is_active = False
        self.user.save()
        response = self.send_patch(self.client, {"goals": "to not activate account"})
        self.assertEqual("to not activate account", response.data["goals"])

    @ddt.unpack
    def test_patch_account_noneditable(self):
        """
        Tests the behavior of patch when a read-only field is attempted to be edited.
        """
        client = self.login_client("client", "user")

        def verify_error_response(field_name, data):
            """
            Internal helper to check the error messages returned
            """
            self.assertEqual(
                "This field is not editable via this API", data["field_errors"][field_name]["developer_message"]
            )
            self.assertEqual(
                u"The '{0}' field cannot be edited.".format(field_name),
                data["field_errors"][field_name]["user_message"]
            )

        for field_name in ["username", "date_joined", "is_active", "profile_image", "requires_parental_consent"]:
            response = self.send_patch(client, {field_name: "will_error", "gender": "o"}, expected_status=400)
            verify_error_response(field_name, response.data)

        # Make sure that gender did not change.
        response = self.send_get(client)
        self.assertEqual("m", response.data["gender"])

        # Test error message with multiple read-only items
        response = self.send_patch(client, {"username": "will_error", "date_joined": "xx"}, expected_status=400)
        self.assertEqual(2, len(response.data["field_errors"]))
        verify_error_response("username", response.data)
        verify_error_response("date_joined", response.data)

    def test_patch_bad_content_type(self):
        """
        Test the behavior of patch when an incorrect content_type is specified.
        """
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        self.send_patch(self.client, {}, content_type="application/json", expected_status=415)
        self.send_patch(self.client, {}, content_type="application/xml", expected_status=415)

    def test_patch_account_empty_string(self):
        """
        Tests the behavior of patch when attempting to set fields with a select list of options to the empty string.
        Also verifies the behaviour when setting to None.
        """
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        for field_name in ["gender", "level_of_education", "country", "state"]:
            response = self.send_patch(self.client, {field_name: ""})
            # Although throwing a 400 might be reasonable, the default DRF behavior with ModelSerializer
            # is to convert to None, which also seems acceptable (and is difficult to override).
            self.assertIsNone(response.data[field_name])

            # Verify that the behavior is the same for sending None.
            response = self.send_patch(self.client, {field_name: ""})
            self.assertIsNone(response.data[field_name])

    def test_patch_name_metadata(self):
        """
        Test the metadata stored when changing the name field.
        """
        def get_name_change_info(expected_entries):
            """
            Internal method to encapsulate the retrieval of old names used
            """
            legacy_profile = UserProfile.objects.get(id=self.user.id)
            name_change_info = legacy_profile.get_meta()["old_names"]
            self.assertEqual(expected_entries, len(name_change_info))
            return name_change_info

        def verify_change_info(change_info, old_name, requester, new_name):
            """
            Internal method to validate name changes
            """
            self.assertEqual(3, len(change_info))
            self.assertEqual(old_name, change_info[0])
            self.assertEqual(u"Name change requested through account API by {}".format(requester), change_info[1])
            self.assertIsNotNone(change_info[2])
            # Verify the new name was also stored.
            get_response = self.send_get(self.client)
            self.assertEqual(new_name, get_response.data["name"])

        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        legacy_profile = UserProfile.objects.get(id=self.user.id)
        self.assertEqual({}, legacy_profile.get_meta())
        old_name = legacy_profile.name

        # First change the name as the user and verify meta information.
        self.send_patch(self.client, {"name": "Mickey Mouse"})
        name_change_info = get_name_change_info(1)
        verify_change_info(name_change_info[0], old_name, self.user.username, "Mickey Mouse")

        # Now change the name again and verify meta information.
        self.send_patch(self.client, {"name": "Donald Duck"})
        name_change_info = get_name_change_info(2)
        verify_change_info(name_change_info[0], old_name, self.user.username, "Donald Duck",)
        verify_change_info(name_change_info[1], "Mickey Mouse", self.user.username, "Donald Duck")

    @mock.patch.dict(
        'django.conf.settings.PROFILE_IMAGE_SIZES_MAP',
        {'full': 50, 'medium': 30, 'small': 10},
        clear=True
    )
    def test_patch_email(self):
        """
        Test that the user can request an email change through the accounts API.
        Full testing of the helper method used (do_email_change_request) exists in the package with the code.
        Here just do minimal smoke testing.
        """
        client = self.login_client("client", "user")
        old_email = self.user.email
        new_email = "newemail@example.com"
        response = self.send_patch(client, {"email": new_email, "goals": "change my email"})

        # Since request is multi-step, the email won't change on GET immediately (though goals will update).
        self.assertEqual(old_email, response.data["email"])
        self.assertEqual("change my email", response.data["goals"])

        # Now call the method that will be invoked with the user clicks the activation key in the received email.
        # First we must get the activation key that was sent.
        pending_change = PendingEmailChange.objects.filter(user=self.user)
        self.assertEqual(1, len(pending_change))
        activation_key = pending_change[0].activation_key
        confirm_change_url = reverse(
            "confirm_email_change", kwargs={'key': activation_key}
        )
        response = self.client.post(confirm_change_url)
        self.assertEqual(200, response.status_code)
        get_response = self.send_get(client)
        self.assertEqual(new_email, get_response.data["email"])

    @ddt.data(
        ("not_an_email",),
        ("",),
        (None,),
    )
    @ddt.unpack
    def test_patch_invalid_email(self, bad_email):
        """
        Test a few error cases for email validation (full test coverage lives with do_email_change_request).
        """
        client = self.login_client("client", "user")

        # Try changing to an invalid email to make sure error messages are appropriately returned.
        error_response = self.send_patch(client, {"email": bad_email}, expected_status=400)
        field_errors = error_response.data["field_errors"]
        self.assertEqual(
            "Error thrown from validate_new_email: 'Valid e-mail address required.'",
            field_errors["email"]["developer_message"]
        )
        self.assertEqual("Valid e-mail address required.", field_errors["email"]["user_message"])

    @mock.patch('common.djangoapps.student.views.management.do_email_change_request')
    def test_patch_duplicate_email(self, do_email_change_request):
        """
        Test that same success response will be sent to user even if the given email already used.
        """
        existing_email = "same@example.com"
        UserFactory.create(email=existing_email)

        client = self.login_client("client", "user")

        # Try changing to an existing email to make sure no error messages returned.
        response = self.send_patch(client, {"email": existing_email})
        self.assertEqual(200, response.status_code)

        # Verify that no actual request made for email change
        self.assertFalse(do_email_change_request.called)

    def test_patch_language_proficiencies(self):
        """
        Verify that patching the language_proficiencies field of the user
        profile completely overwrites the previous value.
        """
        client = self.login_client("client", "user")

        # Patching language_proficiencies exercises the
        # `LanguageProficiencySerializer.get_identity` method, which compares
        # identifies language proficiencies based on their language code rather
        # than django model id.
        for proficiencies in ([{"code": "en"}, {"code": "fr"}, {"code": "es"}], [{"code": "fr"}], [{"code": "aa"}], []):
            response = self.send_patch(client, {"language_proficiencies": proficiencies})
            six.assertCountEqual(self, response.data["language_proficiencies"], proficiencies)

    @ddt.data(
        (
            u"not_a_list",
            {u'non_field_errors': [u'Expected a list of items but got type "unicode".']}
        ),
        (
            [u"not_a_JSON_object"],
            [{u'non_field_errors': [u'Invalid data. Expected a dictionary, but got unicode.']}]
        ),
        (
            [{}],
            [{'code': [u'This field is required.']}]
        ),
        (
            [{u"code": u"invalid_language_code"}],
            [{'code': [u'"invalid_language_code" is not a valid choice.']}]
        ),
        (
            [{u"code": u"kw"}, {u"code": u"el"}, {u"code": u"kw"}],
            [u'The language_proficiencies field must consist of unique languages.']
        ),
    )
    @ddt.unpack
    def test_patch_invalid_language_proficiencies(self, patch_value, expected_error_message):
        """
        Verify we handle error cases when patching the language_proficiencies
        field.
        """
        if six.PY3:
            expected_error_message = six.text_type(expected_error_message).replace('unicode', 'str')

        client = self.login_client("client", "user")
        response = self.send_patch(client, {"language_proficiencies": patch_value}, expected_status=400)
        self.assertEqual(
            response.data["field_errors"]["language_proficiencies"]["developer_message"],
            u"Value '{patch_value}' is not valid for field 'language_proficiencies': {error_message}".format(
                patch_value=patch_value,
                error_message=expected_error_message
            )
        )

    @mock.patch('openedx.core.djangoapps.user_api.accounts.serializers.AccountUserSerializer.save')
    def test_patch_serializer_save_fails(self, serializer_save):
        """
        Test that AccountUpdateErrors are passed through to the response.
        """
        serializer_save.side_effect = [Exception("bummer"), None]
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        error_response = self.send_patch(self.client, {"goals": "save an account field"}, expected_status=400)
        self.assertEqual(
            "Error thrown when saving account updates: 'bummer'",
            error_response.data["developer_message"]
        )
        self.assertIsNone(error_response.data["user_message"])

    @override_settings(PROFILE_IMAGE_BACKEND=TEST_PROFILE_IMAGE_BACKEND)
    def test_convert_relative_profile_url(self):
        """
        Test that when TEST_PROFILE_IMAGE_BACKEND['base_url'] begins
        with a '/', the API generates the full URL to profile images based on
        the URL of the request.
        """
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        response = self.send_get(self.client)
        self.assertEqual(
            response.data["profile_image"],
            {
                "has_image": False,
                "image_url_full": "http://testserver/static/default_50.png",
                "image_url_small": "http://testserver/static/default_10.png"
            }
        )

    @ddt.data(
        ("client", "user", True),
        ("different_client", "different_user", False),
        ("staff_client", "staff_user", True),
    )
    @ddt.unpack
    def test_parental_consent(self, api_client, requesting_username, has_full_access):
        """
        Verifies that under thirteens never return a public profile.
        """
        client = self.login_client(api_client, requesting_username)

        year_of_birth = self._set_user_age_to_10_years(self.user)
        set_user_preference(self.user, ACCOUNT_VISIBILITY_PREF_KEY, ALL_USERS_VISIBILITY)

        # Verify that the default view is still private (except for clients with full access)
        response = self.send_get(client)
        if has_full_access:
            data = response.data
            self.assertEqual(25, len(data))
            self.assertEqual(self.user.username, data["username"])
            self.assertEqual(self.user.first_name + " " + self.user.last_name, data["name"])
            self.assertEqual(self.user.email, data["email"])
            self.assertEqual(year_of_birth, data["year_of_birth"])
            for empty_field in ("country", "level_of_education", "mailing_address", "bio", "state",):
                self.assertIsNone(data[empty_field])
            self.assertEqual("m", data["gender"])
            self.assertEqual("Learn a lot", data["goals"])
            self.assertTrue(data["is_active"])
            self.assertIsNotNone(data["date_joined"])
            self._verify_profile_image_data(data, False)
            self.assertTrue(data["requires_parental_consent"])
            self.assertEqual(PRIVATE_VISIBILITY, data["account_privacy"])
        else:
            self._verify_private_account_response(response, requires_parental_consent=True)

        # Verify that the shared view is still private
        response = self.send_get(client, query_parameters='view=shared')
        self._verify_private_account_response(response, requires_parental_consent=True)


@skip_unless_lms
class TestAccountAPITransactions(TransactionTestCase):
    """
    Tests the transactional behavior of the account API
    """

    def setUp(self):
        super(TestAccountAPITransactions, self).setUp()
        self.client = APIClient()
        self.user = UserFactory.create(password=TEST_PASSWORD)
        self.url = reverse("accounts_api", kwargs={'username': self.user.username})

    @mock.patch('common.djangoapps.student.views.do_email_change_request')
    def test_update_account_settings_rollback(self, mock_email_change):
        """
        Verify that updating account settings is transactional when a failure happens.
        """
        # Send a PATCH request with updates to both profile information and email.
        # Throw an error from the method that is used to process the email change request
        # (this is the last thing done in the api method). Verify that the profile did not change.
        mock_email_change.side_effect = [ValueError, "mock value error thrown"]
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        old_email = self.user.email

        json_data = {"email": "foo@bar.com", "gender": "o"}
        response = self.client.patch(self.url, data=json.dumps(json_data), content_type="application/merge-patch+json")
        self.assertEqual(400, response.status_code)

        # Verify that GET returns the original preferences
        response = self.client.get(self.url)
        data = response.data
        self.assertEqual(old_email, data["email"])
        self.assertEqual(u"m", data["gender"])


@ddt.ddt
@mock.patch('django.conf.settings.USERNAME_REPLACEMENT_WORKER', 'test_replace_username_service_worker')
class UsernameReplacementViewTests(APITestCase):
    """ Tests UsernameReplacementView """
    SERVICE_USERNAME = 'test_replace_username_service_worker'

    def setUp(self):
        super(UsernameReplacementViewTests, self).setUp()
        self.service_user = UserFactory(username=self.SERVICE_USERNAME)
        self.url = reverse("username_replacement")

    def build_jwt_headers(self, user):
        """
        Helper function for creating headers for the JWT authentication.
        """
        token = create_jwt_for_user(user)
        headers = {'HTTP_AUTHORIZATION': u'JWT {}'.format(token)}
        return headers

    def call_api(self, user, data):
        """ Helper function to call API with data """
        data = json.dumps(data)
        headers = self.build_jwt_headers(user)
        return self.client.post(self.url, data, content_type='application/json', **headers)

    def test_auth(self):
        """ Verify the endpoint only works with the service worker """
        data = {
            "username_mappings": [
                {"test_username_1": "test_new_username_1"},
                {"test_username_2": "test_new_username_2"}
            ]
        }

        # Test unauthenticated
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)

        # Test non-service worker
        random_user = UserFactory()
        response = self.call_api(random_user, data)
        self.assertEqual(response.status_code, 403)

        # Test service worker
        response = self.call_api(self.service_user, data)
        self.assertEqual(response.status_code, 200)

    @ddt.data(
        [{}, {}],
        {},
        [{"test_key": "test_value", "test_key_2": "test_value_2"}]
    )
    def test_bad_schema(self, mapping_data):
        """ Verify the endpoint rejects bad data schema """
        data = {
            "username_mappings": mapping_data
        }
        response = self.call_api(self.service_user, data)
        self.assertEqual(response.status_code, 400)

    def test_existing_and_non_existing_users(self):
        """ Tests a mix of existing and non existing users """
        random_users = [UserFactory() for _ in range(5)]
        fake_usernames = ["myname_" + str(x) for x in range(5)]
        existing_users = [{user.username: user.username + '_new'} for user in random_users]
        non_existing_users = [{username: username + '_new'} for username in fake_usernames]
        data = {
            "username_mappings": existing_users + non_existing_users
        }
        expected_response = {
            'failed_replacements': [],
            'successful_replacements': existing_users + non_existing_users
        }
        response = self.call_api(self.service_user, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected_response)
