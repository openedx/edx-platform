# -*- coding: utf-8 -*-
"""
Test cases to cover Accounts-related behaviors of the User API application
"""
from collections import OrderedDict
from copy import deepcopy
import datetime
import ddt
import hashlib
import json

from mock import patch
from nose.plugins.attrib import attr
from pytz import UTC
import unittest

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.testcases import TransactionTestCase
from django.test.utils import override_settings
from rest_framework.test import APITestCase, APIClient
from openedx.core.djangoapps.user_api.models import UserPreference

from student.tests.factories import UserFactory
from student.models import UserProfile, LanguageProficiency, PendingEmailChange
from openedx.core.djangoapps.user_api.accounts import ACCOUNT_VISIBILITY_PREF_KEY
from openedx.core.djangoapps.user_api.preferences.api import set_user_preference
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from .. import PRIVATE_VISIBILITY, ALL_USERS_VISIBILITY

TEST_PROFILE_IMAGE_UPLOADED_AT = datetime.datetime(2002, 1, 9, 15, 43, 01, tzinfo=UTC)


# this is used in one test to check the behavior of profile image url
# generation with a relative url in the config.
TEST_PROFILE_IMAGE_BACKEND = deepcopy(settings.PROFILE_IMAGE_BACKEND)
TEST_PROFILE_IMAGE_BACKEND['options']['base_url'] = '/profile-images/'


class UserAPITestCase(APITestCase):
    """
    The base class for all tests of the User API
    """
    test_password = "test"

    def setUp(self):
        super(UserAPITestCase, self).setUp()

        self.anonymous_client = APIClient()
        self.different_user = UserFactory.create(password=self.test_password)
        self.different_client = APIClient()
        self.staff_user = UserFactory(is_staff=True, password=self.test_password)
        self.staff_client = APIClient()
        self.user = UserFactory.create(password=self.test_password)  # will be assigned to self.client by default

    def login_client(self, api_client, user):
        """Helper method for getting the client and user and logging in. Returns client. """
        client = getattr(self, api_client)
        user = getattr(self, user)
        client.login(username=user.username, password=self.test_password)
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

    def send_put(self, client, json_data, content_type="application/json", expected_status=204):
        """
        Helper method for sending a PUT to the server. Verifies the expected status and returns the response.
        """
        response = client.put(self.url, data=json.dumps(json_data), content_type=content_type)
        self.assertEqual(expected_status, response.status_code)
        return response

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
        legacy_profile.level_of_education = "m"
        legacy_profile.year_of_birth = 2000
        legacy_profile.goals = "world peace"
        legacy_profile.mailing_address = "Park Ave"
        legacy_profile.gender = "f"
        legacy_profile.bio = "Tired mother of twins"
        legacy_profile.profile_image_uploaded_at = TEST_PROFILE_IMAGE_UPLOADED_AT
        legacy_profile.language_proficiencies.add(LanguageProficiency(code='en'))
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
            filename = hashlib.md5('secret' + self.user.username).hexdigest()
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
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Account APIs are only supported in LMS')
@patch('openedx.core.djangoapps.user_api.accounts.image_helpers._PROFILE_IMAGE_SIZES', [50, 10])
@patch.dict(
    'openedx.core.djangoapps.user_api.accounts.image_helpers.PROFILE_IMAGE_SIZES_MAP',
    {'full': 50, 'small': 10},
    clear=True
)
@attr(shard=2)
class TestAccountAPI(CacheIsolationTestCase, UserAPITestCase):
    """
    Unit tests for the Accounts API.
    """

    ENABLED_CACHES = ['default']

    def setUp(self):
        super(TestAccountAPI, self).setUp()

        self.url = reverse("account_api")

    def test_get_username_default(self):
        """
        Test that a client (logged in) can get her own username.
        """
        def verify_get_own_username(queries, expected_status=200):
            """
            Internal helper to perform the actual assertion
            """
            with self.assertNumQueries(queries):
                response = self.send_get(self.client, expected_status=expected_status)
            if expected_status == 200:
                data = response.data
                self.assertEqual(1, len(data))
                self.assertEqual(self.user.username, data["username"])

        # verify that the endpoint is inaccessible when not logged in
        verify_get_own_username(12, expected_status=401)
        self.client.login(username=self.user.username, password=self.test_password)
        verify_get_own_username(9)

        # Now make sure that the user can get the same information, even if not active
        self.user.is_active = False
        self.user.save()
        verify_get_own_username(9)


@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Account APIs are only supported in LMS')
@patch('openedx.core.djangoapps.user_api.accounts.image_helpers._PROFILE_IMAGE_SIZES', [50, 10])
@patch.dict(
    'openedx.core.djangoapps.user_api.accounts.image_helpers.PROFILE_IMAGE_SIZES_MAP',
    {'full': 50, 'small': 10},
    clear=True
)
@attr(shard=2)
class TestAccountsAPI(CacheIsolationTestCase, UserAPITestCase):
    """
    Unit tests for the Accounts API.
    """

    ENABLED_CACHES = ['default']

    def setUp(self):
        super(TestAccountsAPI, self).setUp()

        self.url = reverse("accounts_api", kwargs={'username': self.user.username})

    def _verify_full_shareable_account_response(self, response, account_privacy=None, badges_enabled=False):
        """
        Verify that the shareable fields from the account are returned
        """
        data = response.data
        self.assertEqual(8, len(data))
        self.assertEqual(self.user.username, data["username"])
        self.assertEqual("US", data["country"])
        self._verify_profile_image_data(data, True)
        self.assertIsNone(data["time_zone"])
        self.assertEqual([{"code": "en"}], data["language_proficiencies"])
        self.assertEqual("Tired mother of twins", data["bio"])
        self.assertEqual(account_privacy, data["account_privacy"])
        self.assertEqual(badges_enabled, data['accomplishments_shared'])

    def _verify_private_account_response(self, response, requires_parental_consent=False, account_privacy=None):
        """
        Verify that only the public fields are returned if a user does not want to share account fields
        """
        data = response.data
        self.assertEqual(3, len(data))
        self.assertEqual(self.user.username, data["username"])
        self._verify_profile_image_data(data, not requires_parental_consent)
        self.assertEqual(account_privacy, data["account_privacy"])

    def _verify_full_account_response(self, response, requires_parental_consent=False):
        """
        Verify that all account fields are returned (even those that are not shareable).
        """
        data = response.data
        self.assertEqual(17, len(data))
        self.assertEqual(self.user.username, data["username"])
        self.assertEqual(self.user.first_name + " " + self.user.last_name, data["name"])
        self.assertEqual("US", data["country"])
        self.assertEqual("f", data["gender"])
        self.assertEqual(2000, data["year_of_birth"])
        self.assertEqual("m", data["level_of_education"])
        self.assertEqual("world peace", data["goals"])
        self.assertEqual("Park Ave", data['mailing_address'])
        self.assertEqual(self.user.email, data["email"])
        self.assertTrue(data["is_active"])
        self.assertIsNotNone(data["date_joined"])
        self.assertEqual("Tired mother of twins", data["bio"])
        self._verify_profile_image_data(data, not requires_parental_consent)
        self.assertEquals(requires_parental_consent, data["requires_parental_consent"])
        self.assertEqual([{"code": "en"}], data["language_proficiencies"])
        self.assertEqual(UserPreference.get_value(self.user, 'account_privacy'), data["account_privacy"])

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
        self.client.login(username=self.user.username, password=self.test_password)
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
        self.assertEqual(403 if user == "staff_user" else 404, response.status_code)

    # Note: using getattr so that the patching works even if there is no configuration.
    # This is needed when testing CMS as the patching is still executed even though the
    # suite is skipped.
    @patch.dict(getattr(settings, "ACCOUNT_VISIBILITY_CONFIGURATION", {}), {"default_visibility": "all_users"})
    def test_get_account_different_user_visible(self):
        """
        Test that a client (logged in) can only get the shareable fields for a different user.
        This is the case when default_visibility is set to "all_users".
        """
        self.different_client.login(username=self.different_user.username, password=self.test_password)
        self.create_mock_profile(self.user)
        with self.assertNumQueries(19):
            response = self.send_get(self.different_client)
        self._verify_full_shareable_account_response(response, account_privacy=ALL_USERS_VISIBILITY)

    # Note: using getattr so that the patching works even if there is no configuration.
    # This is needed when testing CMS as the patching is still executed even though the
    # suite is skipped.
    @patch.dict(getattr(settings, "ACCOUNT_VISIBILITY_CONFIGURATION", {}), {"default_visibility": "private"})
    def test_get_account_different_user_private(self):
        """
        Test that a client (logged in) can only get the shareable fields for a different user.
        This is the case when default_visibility is set to "private".
        """
        self.different_client.login(username=self.different_user.username, password=self.test_password)
        self.create_mock_profile(self.user)
        with self.assertNumQueries(19):
            response = self.send_get(self.different_client)
        self._verify_private_account_response(response, account_privacy=PRIVATE_VISIBILITY)

    @patch.dict(settings.FEATURES, {'ENABLE_OPENBADGES': True})
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
                self._verify_private_account_response(response, account_privacy=PRIVATE_VISIBILITY)
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

    def test_get_account_empty_string(self):
        """
        Test the conversion of empty strings to None for certain fields.
        """
        legacy_profile = UserProfile.objects.get(id=self.user.id)
        legacy_profile.country = ""
        legacy_profile.level_of_education = ""
        legacy_profile.gender = ""
        legacy_profile.bio = ""
        legacy_profile.save()

        self.client.login(username=self.user.username, password=self.test_password)
        with self.assertNumQueries(17):
            response = self.send_get(self.client)
        for empty_field in ("level_of_education", "gender", "country", "bio"):
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
        self.send_patch(client, {}, expected_status=403 if user == "staff_user" else 404)

    @ddt.data(
        ("client", "user"),
        ("staff_client", "staff_user"),
    )
    @ddt.unpack
    def test_patch_account_unknown_user(self, api_client, user):
        """
        Test that trying to update a user who does not exist returns a 404.
        """
        client = self.login_client(api_client, user)
        response = client.patch(
            reverse("accounts_api", kwargs={'username': "does_not_exist"}),
            data=json.dumps({}), content_type="application/merge-patch+json"
        )
        self.assertEqual(404, response.status_code)

    @ddt.data(
        ("gender", "f", "not a gender", u'"not a gender" is not a valid choice.'),
        ("level_of_education", "none", u"ȻħȺɍłɇs", u'"ȻħȺɍłɇs" is not a valid choice.'),
        ("country", "GB", "XY", u'"XY" is not a valid choice.'),
        ("year_of_birth", 2009, "not_an_int", u"A valid integer is required."),
        ("name", "bob", "z" * 256, u"Ensure this value has at most 255 characters (it has 256)."),
        ("name", u"ȻħȺɍłɇs", "z   ", "The name field must be at least 2 characters long."),
        ("goals", "Smell the roses"),
        ("mailing_address", "Sesame Street"),
        # Note that we store the raw data, so it is up to client to escape the HTML.
        (
            "bio", u"<html>Lacrosse-playing superhero 壓是進界推日不復女</html>",
            "z" * 3001, u"Ensure this value has at most 3000 characters (it has 3001)."
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
            self.assertEqual(
                u'This value is invalid.',
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
        self.client.login(username=self.user.username, password=self.test_password)
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
                "The '{0}' field cannot be edited.".format(field_name), data["field_errors"][field_name]["user_message"]
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
        self.client.login(username=self.user.username, password=self.test_password)
        self.send_patch(self.client, {}, content_type="application/json", expected_status=415)
        self.send_patch(self.client, {}, content_type="application/xml", expected_status=415)

    def test_patch_account_empty_string(self):
        """
        Tests the behavior of patch when attempting to set fields with a select list of options to the empty string.
        Also verifies the behaviour when setting to None.
        """
        self.client.login(username=self.user.username, password=self.test_password)
        for field_name in ["gender", "level_of_education", "country"]:
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
            self.assertEqual("Name change requested through account API by {}".format(requester), change_info[1])
            self.assertIsNotNone(change_info[2])
            # Verify the new name was also stored.
            get_response = self.send_get(self.client)
            self.assertEqual(new_name, get_response.data["name"])

        self.client.login(username=self.user.username, password=self.test_password)
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

    @patch.dict(
        'openedx.core.djangoapps.user_api.accounts.image_helpers.PROFILE_IMAGE_SIZES_MAP',
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
            "student.views.confirm_email_change", kwargs={'key': activation_key}
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
            self.assertItemsEqual(response.data["language_proficiencies"], proficiencies)

    @ddt.data(
        (u"not_a_list", {u'non_field_errors': [u'Expected a list of items but got type "unicode".']}),
        ([u"not_a_JSON_object"], [{u'non_field_errors': [u'Invalid data. Expected a dictionary, but got unicode.']}]),
        ([{}], [OrderedDict([('code', [u'This field is required.'])])]),
        (
            [{u"code": u"invalid_language_code"}],
            [OrderedDict([('code', [u'"invalid_language_code" is not a valid choice.'])])]
        ),
        (
            [{u"code": u"kw"}, {u"code": u"el"}, {u"code": u"kw"}],
            ['The language_proficiencies field must consist of unique languages']
        ),
    )
    @ddt.unpack
    def test_patch_invalid_language_proficiencies(self, patch_value, expected_error_message):
        """
        Verify we handle error cases when patching the language_proficiencies
        field.
        """
        client = self.login_client("client", "user")
        response = self.send_patch(client, {"language_proficiencies": patch_value}, expected_status=400)
        self.assertEqual(
            response.data["field_errors"]["language_proficiencies"]["developer_message"],
            u"Value '{patch_value}' is not valid for field 'language_proficiencies': {error_message}".format(
                patch_value=patch_value,
                error_message=expected_error_message
            )
        )

    @patch('openedx.core.djangoapps.user_api.accounts.serializers.AccountUserSerializer.save')
    def test_patch_serializer_save_fails(self, serializer_save):
        """
        Test that AccountUpdateErrors are passed through to the response.
        """
        serializer_save.side_effect = [Exception("bummer"), None]
        self.client.login(username=self.user.username, password=self.test_password)
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
        self.client.login(username=self.user.username, password=self.test_password)
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

        # Set the user to be ten years old with a public profile
        legacy_profile = UserProfile.objects.get(id=self.user.id)
        current_year = datetime.datetime.now().year
        legacy_profile.year_of_birth = current_year - 10
        legacy_profile.save()
        set_user_preference(self.user, ACCOUNT_VISIBILITY_PREF_KEY, ALL_USERS_VISIBILITY)

        # Verify that the default view is still private (except for clients with full access)
        response = self.send_get(client)
        if has_full_access:
            data = response.data
            self.assertEqual(17, len(data))
            self.assertEqual(self.user.username, data["username"])
            self.assertEqual(self.user.first_name + " " + self.user.last_name, data["name"])
            self.assertEqual(self.user.email, data["email"])
            self.assertEqual(current_year - 10, data["year_of_birth"])
            for empty_field in ("country", "level_of_education", "mailing_address", "bio"):
                self.assertIsNone(data[empty_field])
            self.assertEqual("m", data["gender"])
            self.assertEqual("Learn a lot", data["goals"])
            self.assertTrue(data["is_active"])
            self.assertIsNotNone(data["date_joined"])
            self._verify_profile_image_data(data, False)
            self.assertTrue(data["requires_parental_consent"])
            self.assertEqual(PRIVATE_VISIBILITY, data["account_privacy"])
        else:
            self._verify_private_account_response(
                response, requires_parental_consent=True, account_privacy=PRIVATE_VISIBILITY
            )

        # Verify that the shared view is still private
        response = self.send_get(client, query_parameters='view=shared')
        self._verify_private_account_response(
            response, requires_parental_consent=True, account_privacy=PRIVATE_VISIBILITY
        )


@attr(shard=2)
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestAccountAPITransactions(TransactionTestCase):
    """
    Tests the transactional behavior of the account API
    """
    test_password = "test"

    def setUp(self):
        super(TestAccountAPITransactions, self).setUp()
        self.client = APIClient()
        self.user = UserFactory.create(password=self.test_password)
        self.url = reverse("accounts_api", kwargs={'username': self.user.username})

    @patch('student.views.do_email_change_request')
    def test_update_account_settings_rollback(self, mock_email_change):
        """
        Verify that updating account settings is transactional when a failure happens.
        """
        # Send a PATCH request with updates to both profile information and email.
        # Throw an error from the method that is used to process the email change request
        # (this is the last thing done in the api method). Verify that the profile did not change.
        mock_email_change.side_effect = [ValueError, "mock value error thrown"]
        self.client.login(username=self.user.username, password=self.test_password)
        old_email = self.user.email

        json_data = {"email": "foo@bar.com", "gender": "o"}
        response = self.client.patch(self.url, data=json.dumps(json_data), content_type="application/merge-patch+json")
        self.assertEqual(400, response.status_code)

        # Verify that GET returns the original preferences
        response = self.client.get(self.url)
        data = response.data
        self.assertEqual(old_email, data["email"])
        self.assertEqual(u"m", data["gender"])
