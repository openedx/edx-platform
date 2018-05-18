# -*- coding: utf-8 -*-
"""
Test cases to cover Accounts-related behaviors of the User API application
"""
from copy import deepcopy
import datetime
import hashlib
import json
import unittest

from consent.models import DataSharingConsent
import ddt
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.testcases import TransactionTestCase
from django.test.utils import override_settings
from enterprise.models import (
    EnterpriseCustomer,
    EnterpriseCustomerUser,
    EnterpriseCourseEnrollment,
    PendingEnterpriseCustomerUser,
)
from integrated_channels.sap_success_factors.models import (
    SapSuccessFactorsLearnerDataTransmissionAudit
)
import mock
from nose.plugins.attrib import attr
from opaque_keys.edx.keys import CourseKey
import pytest
import pytz
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from six import text_type
from social_django.models import UserSocialAuth

from entitlements.models import CourseEntitlementSupportDetail
from entitlements.tests.factories import CourseEntitlementFactory
from lms.djangoapps.verify_student.tests.factories import SoftwareSecurePhotoVerificationFactory
from openedx.core.djangoapps.course_groups.models import CourseUserGroup, UnregisteredLearnerCohortAssignments
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from openedx.core.djangoapps.user_api.accounts import ACCOUNT_VISIBILITY_PREF_KEY
from openedx.core.djangoapps.user_api.accounts.signals import USER_RETIRE_MAILINGS
from openedx.core.djangoapps.user_api.models import RetirementState, UserRetirementStatus, UserPreference, UserOrgTag
from openedx.core.djangoapps.user_api.preferences.api import set_user_preference
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms
from openedx.core.lib.token_utils import JwtBuilder
from student.models import (
    CourseEnrollmentAllowed,
    PendingEmailChange,
    Registration,
    SocialLink,
    UserProfile,
    get_retired_username_by_username,
    get_retired_email_by_email,
)
from student.tests.factories import (
    TEST_PASSWORD,
    ContentTypeFactory,
    CourseEnrollmentAllowedFactory,
    PendingEmailChangeFactory,
    PermissionFactory,
    SuperuserFactory,
    UserFactory
)

from .. import ALL_USERS_VISIBILITY, PRIVATE_VISIBILITY
from ..views import AccountRetirementView, USER_PROFILE_PII
from ...tests.factories import UserOrgTagFactory

TEST_PROFILE_IMAGE_UPLOADED_AT = datetime.datetime(2002, 1, 9, 15, 43, 1, tzinfo=pytz.UTC)


# this is used in one test to check the behavior of profile image url
# generation with a relative url in the config.
TEST_PROFILE_IMAGE_BACKEND = deepcopy(settings.PROFILE_IMAGE_BACKEND)
TEST_PROFILE_IMAGE_BACKEND['options']['base_url'] = '/profile-images/'


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
        legacy_profile.level_of_education = "m"
        legacy_profile.year_of_birth = 2000
        legacy_profile.goals = "world peace"
        legacy_profile.mailing_address = "Park Ave"
        legacy_profile.gender = "f"
        legacy_profile.bio = "Tired mother of twins"
        legacy_profile.profile_image_uploaded_at = TEST_PROFILE_IMAGE_UPLOADED_AT
        legacy_profile.language_proficiencies.create(code='en')
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
@skip_unless_lms
@attr(shard=2)
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
        self._verify_get_own_username(15)

    def test_get_username_inactive(self):
        """
        Test that a logged-in client can get their
        username, even if inactive.
        """
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        self.user.is_active = False
        self.user.save()
        self._verify_get_own_username(15)

    def test_get_username_not_logged_in(self):
        """
        Test that a client (not logged in) gets a 401
        when trying to retrieve their username.
        """

        # verify that the endpoint is inaccessible when not logged in
        self._verify_get_own_username(12, expected_status=401)


@ddt.ddt
@skip_unless_lms
@mock.patch('openedx.core.djangoapps.user_api.accounts.image_helpers._PROFILE_IMAGE_SIZES', [50, 10])
@mock.patch.dict(
    'django.conf.settings.PROFILE_IMAGE_SIZES_MAP',
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
        self.assertEqual(10, len(data))
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
        self.assertEqual(19, len(data))
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
        self.assertEqual(403 if user == "staff_user" else 404, response.status_code)

    # Note: using getattr so that the patching works even if there is no configuration.
    # This is needed when testing CMS as the patching is still executed even though the
    # suite is skipped.
    @mock.patch.dict(getattr(settings, "ACCOUNT_VISIBILITY_CONFIGURATION", {}), {"default_visibility": "all_users"})
    @pytest.mark.django111_expected_failure
    def test_get_account_different_user_visible(self):
        """
        Test that a client (logged in) can only get the shareable fields for a different user.
        This is the case when default_visibility is set to "all_users".
        """
        self.different_client.login(username=self.different_user.username, password=TEST_PASSWORD)
        self.create_mock_profile(self.user)
        with self.assertNumQueries(20):
            response = self.send_get(self.different_client)
        self._verify_full_shareable_account_response(response, account_privacy=ALL_USERS_VISIBILITY)

    # Note: using getattr so that the patching works even if there is no configuration.
    # This is needed when testing CMS as the patching is still executed even though the
    # suite is skipped.
    @mock.patch.dict(getattr(settings, "ACCOUNT_VISIBILITY_CONFIGURATION", {}), {"default_visibility": "private"})
    @pytest.mark.django111_expected_failure
    def test_get_account_different_user_private(self):
        """
        Test that a client (logged in) can only get the shareable fields for a different user.
        This is the case when default_visibility is set to "private".
        """
        self.different_client.login(username=self.different_user.username, password=TEST_PASSWORD)
        self.create_mock_profile(self.user)
        with self.assertNumQueries(20):
            response = self.send_get(self.different_client)
        self._verify_private_account_response(response, account_privacy=PRIVATE_VISIBILITY)

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
    @pytest.mark.django111_expected_failure
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
            self.assertEqual(19, len(data))
            self.assertEqual(self.user.username, data["username"])
            self.assertEqual(self.user.first_name + " " + self.user.last_name, data["name"])
            for empty_field in ("year_of_birth", "level_of_education", "mailing_address", "bio"):
                self.assertIsNone(data[empty_field])
            self.assertIsNone(data["country"])
            self.assertEqual("m", data["gender"])
            self.assertEqual("Learn a lot", data["goals"])
            self.assertEqual(self.user.email, data["email"])
            self.assertIsNotNone(data["date_joined"])
            self.assertEqual(self.user.is_active, data["is_active"])
            self._verify_profile_image_data(data, False)
            self.assertTrue(data["requires_parental_consent"])
            self.assertEqual([], data["language_proficiencies"])
            self.assertEqual(PRIVATE_VISIBILITY, data["account_privacy"])
            # Badges aren't on by default, so should not be present.
            self.assertEqual(False, data["accomplishments_shared"])

        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        verify_get_own_information(18)

        # Now make sure that the user can get the same information, even if not active
        self.user.is_active = False
        self.user.save()
        verify_get_own_information(12)

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

        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        with self.assertNumQueries(18):
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
        ("name", u"ȻħȺɍłɇs", "z   ", u"The name field must be at least 2 characters long."),
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
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        self.send_patch(self.client, {}, content_type="application/json", expected_status=415)
        self.send_patch(self.client, {}, content_type="application/xml", expected_status=415)

    def test_patch_account_empty_string(self):
        """
        Tests the behavior of patch when attempting to set fields with a select list of options to the empty string.
        Also verifies the behaviour when setting to None.
        """
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
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
    @pytest.mark.django111_expected_failure
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
            self.assertEqual(19, len(data))
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

    @mock.patch('student.views.do_email_change_request')
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


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Account APIs are only supported in LMS')
class TestAccountDeactivation(TestCase):
    """
    Tests the account deactivation endpoint.
    """

    def setUp(self):
        super(TestAccountDeactivation, self).setUp()
        self.test_user = UserFactory()
        self.url = reverse('accounts_deactivation', kwargs={'username': self.test_user.username})

    def build_jwt_headers(self, user):
        """
        Helper function for creating headers for the JWT authentication.
        """
        token = JwtBuilder(user).build_token([])
        headers = {
            'HTTP_AUTHORIZATION': 'JWT ' + token
        }
        return headers

    def assert_activation_status(self, headers, expected_status=status.HTTP_200_OK, expected_activation_status=False):
        """
        Helper function for making a request to the deactivation endpoint, and asserting the status.

        Args:
            expected_status(int): Expected request's response status.
            expected_activation_status(bool): Expected user has_usable_password attribute value.
        """
        self.assertTrue(self.test_user.has_usable_password())
        response = self.client.post(self.url, **headers)
        self.assertEqual(response.status_code, expected_status)
        self.test_user.refresh_from_db()
        self.assertEqual(self.test_user.has_usable_password(), expected_activation_status)

    def test_superuser_deactivates_user(self):
        """
        Verify a user is deactivated when a superuser posts to the deactivation endpoint.
        """
        superuser = SuperuserFactory()
        headers = self.build_jwt_headers(superuser)
        self.assert_activation_status(headers)

    def test_user_with_permission_deactivates_user(self):
        """
        Verify a user is deactivated when a user with permission posts to the deactivation endpoint.
        """
        user = UserFactory()
        permission = PermissionFactory(
            codename='can_deactivate_users',
            content_type=ContentTypeFactory(
                app_label='student'
            )
        )
        user.user_permissions.add(permission)
        headers = self.build_jwt_headers(user)
        self.assertTrue(self.test_user.has_usable_password())
        self.assert_activation_status(headers)

    def test_unauthorized_rejection(self):
        """
        Verify unauthorized users cannot deactivate accounts.
        """
        headers = self.build_jwt_headers(self.test_user)
        self.assert_activation_status(
            headers,
            expected_status=status.HTTP_403_FORBIDDEN,
            expected_activation_status=True
        )

    def test_on_jwt_headers_rejection(self):
        """
        Verify users who are not JWT authenticated are rejected.
        """
        UserFactory()
        self.assert_activation_status(
            {},
            expected_status=status.HTTP_401_UNAUTHORIZED,
            expected_activation_status=True
        )


class RetirementTestCase(TestCase):
    """
    Test case with a helper methods for retirement
    """
    @classmethod
    def setUpClass(cls):
        super(RetirementTestCase, cls).setUpClass()
        cls.setup_states()

    @staticmethod
    def setup_states():
        """
        Create basic states that mimic our current understanding of the retirement process
        """
        default_states = [
            ('PENDING', 1, False, True),
            ('LOCKING_ACCOUNT', 20, False, False),
            ('LOCKING_COMPLETE', 30, False, False),
            ('RETIRING_CREDENTIALS', 40, False, False),
            ('CREDENTIALS_COMPLETE', 50, False, False),
            ('RETIRING_ECOM', 60, False, False),
            ('ECOM_COMPLETE', 70, False, False),
            ('RETIRING_FORUMS', 80, False, False),
            ('FORUMS_COMPLETE', 90, False, False),
            ('RETIRING_EMAIL_LISTS', 100, False, False),
            ('EMAIL_LISTS_COMPLETE', 110, False, False),
            ('RETIRING_ENROLLMENTS', 120, False, False),
            ('ENROLLMENTS_COMPLETE', 130, False, False),
            ('RETIRING_NOTES', 140, False, False),
            ('NOTES_COMPLETE', 150, False, False),
            ('NOTIFYING_PARTNERS', 160, False, False),
            ('PARTNERS_NOTIFIED', 170, False, False),
            ('RETIRING_LMS', 180, False, False),
            ('LMS_COMPLETE', 190, False, False),
            ('ERRORED', 200, True, True),
            ('ABORTED', 210, True, True),
            ('COMPLETE', 220, True, True),
        ]

        for name, ex, dead, req in default_states:
            RetirementState.objects.create(
                state_name=name,
                state_execution_order=ex,
                is_dead_end_state=dead,
                required=req
            )

    def build_jwt_headers(self, user):
        """
        Helper function for creating headers for the JWT authentication.
        """
        token = JwtBuilder(user).build_token([])
        headers = {
            'HTTP_AUTHORIZATION': 'JWT ' + token
        }
        return headers

    def _create_retirement(self, state, create_datetime=None):
        """
        Helper method to create a RetirementStatus with useful defaults
        """
        if create_datetime is None:
            create_datetime = datetime.datetime.now(pytz.UTC) - datetime.timedelta(days=8)

        user = UserFactory()
        return UserRetirementStatus.objects.create(
            user=user,
            original_username=user.username,
            original_email=user.email,
            original_name=user.profile.name,
            retired_username=get_retired_username_by_username(user.username),
            retired_email=get_retired_email_by_email(user.email),
            current_state=state,
            last_state=state,
            responses="",
            created=create_datetime,
            modified=create_datetime
        )

    def _retirement_to_dict(self, retirement, all_fields=False):
        """
        Return a dict format of this model to a consistent format for serialization, removing the long text field
        `responses` for performance reasons.
        """
        retirement_dict = {
            u'id': retirement.id,
            u'user': {
                u'id': retirement.user.id,
                u'username': retirement.user.username,
                u'email': retirement.user.email,
                u'profile': {
                    u'id': retirement.user.profile.id,
                    u'name': retirement.user.profile.name
                },
            },
            u'original_username': retirement.original_username,
            u'original_email': retirement.original_email,
            u'original_name': retirement.original_name,
            u'retired_username': retirement.retired_username,
            u'retired_email': retirement.retired_email,
            u'current_state': {
                u'id': retirement.current_state.id,
                u'state_name': retirement.current_state.state_name,
                u'state_execution_order': retirement.current_state.state_execution_order,
            },
            u'last_state': {
                u'id': retirement.last_state.id,
                u'state_name': retirement.last_state.state_name,
                u'state_execution_order': retirement.last_state.state_execution_order,
            },
            u'created': retirement.created,
            u'modified': retirement.modified
        }

        if all_fields:
            retirement_dict['responses'] = retirement.responses

        return retirement_dict

    def _create_users_all_states(self):
        return [self._create_retirement(state) for state in RetirementState.objects.all()]

    def _get_non_dead_end_states(self):
        return [state for state in RetirementState.objects.filter(is_dead_end_state=False)]

    def _get_dead_end_states(self):
        return [state for state in RetirementState.objects.filter(is_dead_end_state=True)]


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Account APIs are only supported in LMS')
class TestDeactivateLogout(RetirementTestCase):
    """
    Tests the account deactivation/logout endpoint.
    """
    def setUp(self):
        super(TestDeactivateLogout, self).setUp()
        self.test_password = 'password'
        self.test_user = UserFactory(password=self.test_password)
        UserSocialAuth.objects.create(
            user=self.test_user,
            provider='some_provider_name',
            uid='xyz@gmail.com'
        )
        UserSocialAuth.objects.create(
            user=self.test_user,
            provider='some_other_provider_name',
            uid='xyz@gmail.com'
        )

        Registration().register(self.test_user)

        self.url = reverse('deactivate_logout')

    def build_post(self, password):
        return {'password': password}

    @mock.patch('openedx.core.djangolib.oauth2_retirement_utils')
    def test_user_can_deactivate_self(self, retirement_utils_mock):
        """
        Verify a user calling the deactivation endpoint logs out the user, deletes all their SSO tokens,
        and creates a user retirement row.
        """
        self.client.login(username=self.test_user.username, password=self.test_password)
        headers = self.build_jwt_headers(self.test_user)
        response = self.client.post(self.url, self.build_post(self.test_password), **headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # make sure the user model is as expected
        updated_user = User.objects.get(id=self.test_user.id)
        self.assertEqual(get_retired_email_by_email(self.test_user.email), updated_user.email)
        self.assertFalse(updated_user.has_usable_password())
        self.assertEqual(list(UserSocialAuth.objects.filter(user=self.test_user)), [])
        self.assertEqual(list(Registration.objects.filter(user=self.test_user)), [])
        self.assertEqual(len(UserRetirementStatus.objects.filter(user_id=self.test_user.id)), 1)
        # these retirement utils are tested elsewhere; just make sure we called them
        retirement_utils_mock.retire_dop_oauth2_models.assertCalledWith(self.test_user)
        retirement_utils_mock.retire_dot_oauth2_models.assertCalledWith(self.test_user)
        # make sure the user cannot log in
        self.assertFalse(self.client.login(username=self.test_user.username, password=self.test_password))

    def test_password_mismatch(self):
        """
        Verify that the user submitting a mismatched password results in
        a rejection.
        """
        self.client.login(username=self.test_user.username, password=self.test_password)
        headers = self.build_jwt_headers(self.test_user)
        response = self.client.post(self.url, self.build_post(self.test_password + "xxxx"), **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_called_twice(self):
        """
        Verify a user calling the deactivation endpoint a second time results in a "forbidden"
        error, as the user will be logged out.
        """
        self.client.login(username=self.test_user.username, password=self.test_password)
        headers = self.build_jwt_headers(self.test_user)
        response = self.client.post(self.url, self.build_post(self.test_password), **headers)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.client.login(username=self.test_user.username, password=self.test_password)
        headers = self.build_jwt_headers(self.test_user)
        response = self.client.post(self.url, self.build_post(self.test_password), **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Account APIs are only supported in LMS')
class TestAccountRetireMailings(RetirementTestCase):
    """
    Tests the account retire mailings endpoint.
    """
    def setUp(self):
        super(TestAccountRetireMailings, self).setUp()
        self.test_superuser = SuperuserFactory()
        self.test_service_user = UserFactory()

        # Should be created in parent setUpClass
        retiring_email_lists = RetirementState.objects.get(state_name='RETIRING_EMAIL_LISTS')

        self.retirement = self._create_retirement(retiring_email_lists)
        self.test_user = self.retirement.user

        UserOrgTag.objects.create(user=self.test_user, key='email-optin', org="foo", value="True")
        UserOrgTag.objects.create(user=self.test_user, key='email-optin', org="bar", value="True")

        self.url = reverse('accounts_retire_mailings')

    def build_jwt_headers(self, user):
        """
        Helper function for creating headers for the JWT authentication.
        """
        token = JwtBuilder(user).build_token([])
        headers = {
            'HTTP_AUTHORIZATION': 'JWT ' + token
        }
        return headers

    def build_post(self, user):
        return {'username': user.username}

    def assert_status_and_tag_count(self, headers, expected_status=status.HTTP_204_NO_CONTENT, expected_tag_count=2,
                                    expected_tag_value="False", expected_content=None):
        """
        Helper function for making a request to the retire subscriptions endpoint, and asserting the status.
        """
        response = self.client.post(self.url, self.build_post(self.test_user), **headers)

        self.assertEqual(response.status_code, expected_status)

        # Check that the expected number of tags with the correct value exist
        tag_count = UserOrgTag.objects.filter(user=self.test_user, value=expected_tag_value).count()
        self.assertEqual(tag_count, expected_tag_count)

        if expected_content:
            self.assertEqual(response.content.strip('"'), expected_content)

    def test_superuser_retires_user_subscriptions(self):
        """
        Verify a user's subscriptions are retired when a superuser posts to the retire subscriptions endpoint.
        """
        headers = self.build_jwt_headers(self.test_superuser)
        self.assert_status_and_tag_count(headers)

    def test_superuser_retires_user_subscriptions_no_orgtags(self):
        """
        Verify the call succeeds when the user doesn't have any org tags.
        """
        UserOrgTag.objects.all().delete()
        headers = self.build_jwt_headers(self.test_superuser)
        self.assert_status_and_tag_count(headers, expected_tag_count=0)

    def test_unauthorized_rejection(self):
        """
        Verify unauthorized users cannot retire subscriptions.
        """
        headers = self.build_jwt_headers(self.test_user)

        # User should still have 2 "True" subscriptions.
        self.assert_status_and_tag_count(headers, expected_status=status.HTTP_403_FORBIDDEN, expected_tag_value="True")

    def test_signal_failure(self):
        """
        Verify that if a signal fails the transaction is rolled back and a proper error message is returned.
        """
        headers = self.build_jwt_headers(self.test_superuser)

        mock_handler = mock.MagicMock()
        mock_handler.side_effect = Exception("Tango")

        try:
            USER_RETIRE_MAILINGS.connect(mock_handler)

            # User should still have 2 "True" subscriptions.
            self.assert_status_and_tag_count(
                headers,
                expected_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                expected_tag_value="True",
                expected_content="Tango"
            )
        finally:
            USER_RETIRE_MAILINGS.disconnect(mock_handler)


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Account APIs are only supported in LMS')
class TestAccountRetirementList(RetirementTestCase):
    """
    Tests the account retirement endpoint.
    """

    def setUp(self):
        super(TestAccountRetirementList, self).setUp()
        self.test_superuser = SuperuserFactory()
        self.headers = self.build_jwt_headers(self.test_superuser)
        self.url = reverse('accounts_retirement_queue')
        self.maxDiff = None

    def assert_status_and_user_list(
            self,
            expected_data,
            expected_status=status.HTTP_200_OK,
            states_to_request=None,
            cool_off_days=7
    ):
        """
        Helper function for making a request to the retire subscriptions endpoint, asserting the status, and
        optionally asserting data returned.
        """
        if states_to_request is None:
            # These are just a couple of random states that should be used in any implementation
            states_to_request = ['PENDING', 'LOCKING_ACCOUNT']
        else:
            # Can pass in RetirementState objects or strings here
            try:
                states_to_request = [s.state_name for s in states_to_request]
            except AttributeError:
                states_to_request = states_to_request

        data = {'cool_off_days': cool_off_days, 'states': states_to_request}
        response = self.client.get(self.url, data, **self.headers)
        self.assertEqual(response.status_code, expected_status)
        response_data = response.json()

        if expected_data:
            # These datetimes won't match up due to serialization, but they're inherited fields tested elsewhere
            for data in (response_data, expected_data):
                for retirement in data:
                    del retirement['created']
                    del retirement['modified']

            self.assertItemsEqual(response_data, expected_data)

    def test_empty(self):
        """
        Verify that an empty array is returned if no users are awaiting retirement
        """
        self.assert_status_and_user_list([])

    def test_users_exist_none_in_correct_status(self):
        """
        Verify that users in dead end states are not returned
        """
        for state in self._get_dead_end_states():
            self._create_retirement(state)
        self.assert_status_and_user_list([], states_to_request=self._get_non_dead_end_states())

    def test_users_retrieved_in_multiple_states(self):
        """
        Verify that if multiple states are requested, learners in each state are returned.
        """
        multiple_states = ['PENDING', 'FORUMS_COMPLETE']
        for state in multiple_states:
            self._create_retirement(RetirementState.objects.get(state_name=state))
        data = {'cool_off_days': 0, 'states': multiple_states}
        response = self.client.get(self.url, data, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_users_exist(self):
        """
        Verify users in different states are returned with correct data or filtered out
        """
        self.maxDiff = None
        retirement_values = []
        states_to_request = []

        dead_end_states = self._get_dead_end_states()

        for retirement in self._create_users_all_states():
            if retirement.current_state not in dead_end_states:
                states_to_request.append(retirement.current_state)
                retirement_values.append(self._retirement_to_dict(retirement))

        self.assert_status_and_user_list(retirement_values, states_to_request=self._get_non_dead_end_states())

    def test_date_filter(self):
        """
        Verifies the functionality of the `cool_off_days` parameter by creating 1 retirement per day for
        10 days. Then requests different 1-10 `cool_off_days` to confirm the correct retirements are returned.
        """
        retirements = []
        days_back_to_test = 10

        # Create a retirement per day for the last 10 days, from oldest date to newest. We want these all created
        # before we start checking, thus the two loops.
        # retirements = [2018-04-10..., 2018-04-09..., 2018-04-08...]
        pending_state = RetirementState.objects.get(state_name='PENDING')
        for days_back in range(1, days_back_to_test, -1):
            create_datetime = datetime.datetime.now(pytz.UTC) - datetime.timedelta(days=days_back)
            retirements.append(self._create_retirement(state=pending_state, create_datetime=create_datetime))

        # Confirm we get the correct number and data back for each day we add to cool off days
        # For each day we add to `cool_off_days` we expect to get one fewer retirement.
        for cool_off_days in range(1, days_back_to_test):
            # Start with 9 days back
            req_days_back = days_back_to_test - cool_off_days

            retirement_dicts = [self._retirement_to_dict(ret) for ret in retirements[:cool_off_days]]

            self.assert_status_and_user_list(
                retirement_dicts,
                cool_off_days=req_days_back
            )

    def test_bad_cool_off_days(self):
        """
        Check some bad inputs to make sure we get back the expected status
        """
        self.assert_status_and_user_list(None, expected_status=status.HTTP_400_BAD_REQUEST, cool_off_days=-1)
        self.assert_status_and_user_list(None, expected_status=status.HTTP_400_BAD_REQUEST, cool_off_days='ABCDERTP')

    def test_bad_states(self):
        """
        Check some bad inputs to make sure we get back the expected status
        """
        self.assert_status_and_user_list(
            None,
            expected_status=status.HTTP_400_BAD_REQUEST,
            states_to_request=['TUNA', 'TACO'])
        self.assert_status_and_user_list(None, expected_status=status.HTTP_400_BAD_REQUEST, states_to_request=[])

    def test_missing_params(self):
        """
        All params are required, make sure that is enforced
        """
        response = self.client.get(self.url, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.get(self.url, {}, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.get(self.url, {'cool_off_days': 7}, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        RetirementState.objects.get(state_name='PENDING')
        response = self.client.get(self.url, {'states': ['PENDING']}, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Account APIs are only supported in LMS')
class TestAccountRetirementRetrieve(RetirementTestCase):
    """
    Tests the account retirement retrieval endpoint.
    """
    def setUp(self):
        super(TestAccountRetirementRetrieve, self).setUp()
        self.test_user = UserFactory()
        self.test_superuser = SuperuserFactory()
        self.url = reverse('accounts_retirement_retrieve', kwargs={'username': self.test_user.username})
        self.headers = self.build_jwt_headers(self.test_superuser)
        self.maxDiff = None

    def assert_status_and_user_data(self, expected_data, expected_status=status.HTTP_200_OK, username_to_find=None):
        """
        Helper function for making a request to the retire subscriptions endpoint, asserting the status,
        and optionally asserting the expected data.
        """
        if username_to_find is not None:
            self.url = reverse('accounts_retirement_retrieve', kwargs={'username': username_to_find})

        response = self.client.get(self.url, **self.headers)
        self.assertEqual(response.status_code, expected_status)

        if expected_data is not None:
            response_data = response.json()

            # These won't match up due to serialization, but they're inherited fields tested elsewhere
            for data in (expected_data, response_data):
                del data['created']
                del data['modified']

            self.assertDictEqual(response_data, expected_data)
            return response_data

    def test_no_retirement(self):
        """
        Confirm we get a 404 if a retirement for the user can be found
        """
        self.assert_status_and_user_data(None, status.HTTP_404_NOT_FOUND)

    def test_retirements_all_states(self):
        """
        Create a bunch of retirements and confirm we get back the correct data for each
        """
        retirements = []

        for state in RetirementState.objects.all():
            retirements.append(self._create_retirement(state))

        for retirement in retirements:
            values = self._retirement_to_dict(retirement)
            self.assert_status_and_user_data(values, username_to_find=values['user']['username'])

    def test_retrieve_by_old_username(self):
        """
        Simulate retrieving a retirement by the old username, after the name has been changed to the hashed one
        """
        pending_state = RetirementState.objects.get(state_name='PENDING')
        retirement = self._create_retirement(pending_state)
        original_username = retirement.user.username

        hashed_username = get_retired_username_by_username(original_username)

        retirement.user.username = hashed_username
        retirement.user.save()

        values = self._retirement_to_dict(retirement)
        self.assert_status_and_user_data(values, username_to_find=original_username)


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Account APIs are only supported in LMS')
class TestAccountRetirementUpdate(RetirementTestCase):
    """
    Tests the account retirement endpoint.
    """
    def setUp(self):
        super(TestAccountRetirementUpdate, self).setUp()
        self.pending_state = RetirementState.objects.get(state_name='PENDING')
        self.locking_state = RetirementState.objects.get(state_name='LOCKING_ACCOUNT')

        self.retirement = self._create_retirement(self.pending_state)
        self.test_user = self.retirement.user
        self.test_superuser = SuperuserFactory()
        self.headers = self.build_jwt_headers(self.test_superuser)
        self.headers['content_type'] = "application/json"
        self.url = reverse('accounts_retirement_update')

    def update_and_assert_status(self, data, expected_status=status.HTTP_204_NO_CONTENT):
        """
        Helper function for making a request to the retire subscriptions endpoint, and asserting the status.
        """
        if 'username' not in data:
            data['username'] = self.test_user.username

        response = self.client.patch(self.url, json.dumps(data), **self.headers)
        self.assertEqual(response.status_code, expected_status)

    def test_single_update(self):
        """
        Basic test to confirm changing state works and saves the given response
        """
        data = {'new_state': 'LOCKING_ACCOUNT', 'response': 'this should succeed'}
        self.update_and_assert_status(data)

        # Refresh the retirment object and confirm the messages and state are correct
        retirement = UserRetirementStatus.objects.get(id=self.retirement.id)
        self.assertEqual(retirement.current_state, RetirementState.objects.get(state_name='LOCKING_ACCOUNT'))
        self.assertEqual(retirement.last_state, RetirementState.objects.get(state_name='PENDING'))
        self.assertIn('this should succeed', retirement.responses)

    def test_move_through_process(self):
        """
        Simulate moving a retirement through the process and confirm they end up in the
        correct state, with all relevant response messages logged.
        """
        fake_retire_process = [
            {'new_state': 'LOCKING_ACCOUNT', 'response': 'accountlockstart'},
            {'new_state': 'LOCKING_COMPLETE', 'response': 'accountlockcomplete'},
            {'new_state': 'RETIRING_CREDENTIALS', 'response': 'retiringcredentials'},
            {'new_state': 'CREDENTIALS_COMPLETE', 'response': 'credentialsretired'},
            {'new_state': 'COMPLETE', 'response': 'accountretirementcomplete'},
        ]

        for update_data in fake_retire_process:
            self.update_and_assert_status(update_data)

        # Refresh the retirment object and confirm the messages and state are correct
        retirement = UserRetirementStatus.objects.get(id=self.retirement.id)
        self.assertEqual(retirement.current_state, RetirementState.objects.get(state_name='COMPLETE'))
        self.assertEqual(retirement.last_state, RetirementState.objects.get(state_name='CREDENTIALS_COMPLETE'))
        self.assertIn('accountlockstart', retirement.responses)
        self.assertIn('accountlockcomplete', retirement.responses)
        self.assertIn('retiringcredentials', retirement.responses)
        self.assertIn('credentialsretired', retirement.responses)
        self.assertIn('accountretirementcomplete', retirement.responses)

    def test_unknown_state(self):
        """
        Test that trying to set to an unknown state fails with a 400
        """
        data = {'new_state': 'BOGUS_STATE', 'response': 'this should fail'}
        self.update_and_assert_status(data, status.HTTP_400_BAD_REQUEST)

    def test_bad_vars(self):
        """
        Test various ways of sending the wrong variables to make sure they all fail correctly
        """
        # No `new_state`
        data = {'response': 'this should fail'}
        self.update_and_assert_status(data, status.HTTP_400_BAD_REQUEST)

        # No `response`
        data = {'new_state': 'COMPLETE'}
        self.update_and_assert_status(data, status.HTTP_400_BAD_REQUEST)

        # Unknown `new_state`
        data = {'new_state': 'BOGUS_STATE', 'response': 'this should fail'}
        self.update_and_assert_status(data, status.HTTP_400_BAD_REQUEST)

        # No `new_state` or `response`
        data = {}
        self.update_and_assert_status(data, status.HTTP_400_BAD_REQUEST)

        # Unexpected param `should_not_exist`
        data = {'should_not_exist': 'bad', 'new_state': 'COMPLETE', 'response': 'this should fail'}
        self.update_and_assert_status(data, status.HTTP_400_BAD_REQUEST)

    def test_no_retirement(self):
        """
        Confirm that trying to operate on a non-existent retirement for an existing user 404s
        """
        # Delete the only retirement, created in setUp
        UserRetirementStatus.objects.all().delete()
        data = {'new_state': 'LOCKING_ACCOUNT', 'response': 'this should fail'}
        self.update_and_assert_status(data, status.HTTP_404_NOT_FOUND)

    def test_no_user(self):
        """
        Confirm that trying to operate on a non-existent user 404s
        """
        data = {'new_state': 'LOCKING_ACCOUNT', 'response': 'this should fail', 'username': 'does not exist'}
        self.update_and_assert_status(data, status.HTTP_404_NOT_FOUND)

    def test_move_from_dead_end(self):
        """
        Confirm that trying to move from a dead end state to any other state fails
        """
        retirement = UserRetirementStatus.objects.get(id=self.retirement.id)
        retirement.current_state = RetirementState.objects.filter(is_dead_end_state=True)[0]
        retirement.save()

        data = {'new_state': 'LOCKING_ACCOUNT', 'response': 'this should fail'}
        self.update_and_assert_status(data, status.HTTP_400_BAD_REQUEST)

    def test_move_backward(self):
        """
        Confirm that trying to move to an earlier step in the process fails
        """
        retirement = UserRetirementStatus.objects.get(id=self.retirement.id)
        retirement.current_state = RetirementState.objects.get(state_name='COMPLETE')
        retirement.save()

        data = {'new_state': 'PENDING', 'response': 'this should fail'}
        self.update_and_assert_status(data, status.HTTP_400_BAD_REQUEST)

    def test_move_same(self):
        """
        Confirm that trying to move to the same step in the process fails
        """
        # Should already be in 'PENDING'
        data = {'new_state': 'PENDING', 'response': 'this should fail'}
        self.update_and_assert_status(data, status.HTTP_400_BAD_REQUEST)


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Account APIs are only supported in LMS')
class TestAccountRetirementPost(RetirementTestCase):
    """
    Tests the account retirement endpoint.
    """
    def setUp(self):
        super(TestAccountRetirementPost, self).setUp()

        self.test_user = UserFactory()
        self.test_superuser = SuperuserFactory()
        self.original_username = self.test_user.username
        self.original_email = self.test_user.email
        self.retired_username = get_retired_username_by_username(self.original_username)
        self.retired_email = get_retired_email_by_email(self.original_email)

        retirement_state = RetirementState.objects.get(state_name='RETIRING_LMS')
        self.retirement_status = UserRetirementStatus.create_retirement(self.test_user)
        self.retirement_status.current_state = retirement_state
        self.retirement_status.last_state = retirement_state
        self.retirement_status.save()

        SocialLink.objects.create(
            user_profile=self.test_user.profile,
            platform='Facebook',
            social_link='www.facebook.com'
        ).save()

        self.cache_key = UserProfile.country_cache_key_name(self.test_user.id)
        cache.set(self.cache_key, 'Timor-leste')

        # Enterprise model setup
        self.course_id = 'course-v1:edX+DemoX.1+2T2017'
        self.enterprise_customer = EnterpriseCustomer.objects.create(
            name='test_enterprise_customer',
            site=SiteFactory.create()
        )
        self.enterprise_user = EnterpriseCustomerUser.objects.create(
            enterprise_customer=self.enterprise_customer,
            user_id=self.test_user.id,
        )
        self.enterprise_enrollment = EnterpriseCourseEnrollment.objects.create(
            enterprise_customer_user=self.enterprise_user,
            course_id=self.course_id
        )
        self.pending_enterprise_user = PendingEnterpriseCustomerUser.objects.create(
            enterprise_customer_id=self.enterprise_user.enterprise_customer_id,
            user_email=self.test_user.email
        )
        self.sapsf_audit = SapSuccessFactorsLearnerDataTransmissionAudit.objects.create(
            sapsf_user_id=self.test_user.id,
            enterprise_course_enrollment_id=self.enterprise_enrollment.id,
            completed_timestamp=1,
        )
        self.consent = DataSharingConsent.objects.create(
            username=self.test_user.username,
            enterprise_customer=self.enterprise_customer,
        )

        # Entitlement model setup
        self.entitlement = CourseEntitlementFactory.create(user=self.test_user)
        self.entitlement_support_detail = CourseEntitlementSupportDetail.objects.create(
            entitlement=self.entitlement,
            support_user=UserFactory(),
            comments='A comment containing potential PII.'
        )

        # Misc. setup
        self.photo_verification = SoftwareSecurePhotoVerificationFactory.create(user=self.test_user)
        PendingEmailChangeFactory.create(user=self.test_user)
        UserOrgTagFactory.create(user=self.test_user, key='foo', value='bar')
        UserOrgTagFactory.create(user=self.test_user, key='cat', value='dog')

        CourseEnrollmentAllowedFactory.create(email=self.original_email)

        self.course_key = CourseKey.from_string('course-v1:edX+DemoX+Demo_Course')
        self.cohort = CourseUserGroup.objects.create(
            name="TestCohort",
            course_id=self.course_key,
            group_type=CourseUserGroup.COHORT
        )
        self.cohort_assignment = UnregisteredLearnerCohortAssignments.objects.create(
            course_user_group=self.cohort,
            course_id=self.course_key,
            email=self.original_email
        )

        # setup for doing POST from test client
        self.headers = self.build_jwt_headers(self.test_superuser)
        self.headers['content_type'] = "application/json"
        self.url = reverse('accounts_retire')

    def post_and_assert_status(self, data, expected_status=status.HTTP_204_NO_CONTENT):
        """
        Helper function for making a request to the retire subscriptions endpoint, and asserting the status.
        """
        response = self.client.post(self.url, json.dumps(data), **self.headers)
        self.assertEqual(response.status_code, expected_status)
        return response

    def test_user_profile_pii_has_expected_values(self):
        expected_user_profile_pii = {
            'name': '',
            'meta': '',
            'location': '',
            'year_of_birth': None,
            'gender': None,
            'mailing_address': None,
            'city': None,
            'country': None,
            'bio': None,
        }
        self.assertEqual(expected_user_profile_pii, USER_PROFILE_PII)

    def test_retire_user_where_user_does_not_exist(self):
        path = 'openedx.core.djangoapps.user_api.accounts.views.is_username_retired'
        with mock.patch(path, return_value=False) as mock_retired_username:
            data = {'username': 'not_a_user'}
            response = self.post_and_assert_status(data, status.HTTP_404_NOT_FOUND)
            self.assertFalse(response.content)
            mock_retired_username.assert_called_once_with('not_a_user')

    def test_retire_user_server_error_is_raised(self):
        path = 'openedx.core.djangoapps.user_api.models.UserRetirementStatus.get_retirement_for_retirement_action'
        with mock.patch(path, side_effect=Exception('Unexpected Exception')) as mock_get_retirement:
            data = {'username': self.test_user.username}
            response = self.post_and_assert_status(data, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertEqual('Unexpected Exception', text_type(response.json()))
            mock_get_retirement.assert_called_once_with(self.original_username)

    def test_retire_user_where_user_already_retired(self):
        path = 'openedx.core.djangoapps.user_api.accounts.views.is_username_retired'
        with mock.patch(path, return_value=True) as mock_is_username_retired:
            data = {'username': self.test_user.username}
            response = self.post_and_assert_status(data, status.HTTP_404_NOT_FOUND)
            self.assertFalse(response.content)
            mock_is_username_retired.assert_called_once_with(self.original_username)

    def test_retire_user_where_username_not_provided(self):
        response = self.post_and_assert_status({}, status.HTTP_404_NOT_FOUND)
        expected_response_message = {'message': text_type('The user was not specified.')}
        self.assertEqual(expected_response_message, response.json())

    @mock.patch('openedx.core.djangoapps.user_api.accounts.views.get_profile_image_names')
    @mock.patch('openedx.core.djangoapps.user_api.accounts.views.remove_profile_images')
    def test_retire_user(self, mock_remove_profile_images, mock_get_profile_image_names):
        data = {'username': self.original_username}
        self.post_and_assert_status(data)

        self.test_user.refresh_from_db()
        self.test_user.profile.refresh_from_db()  # pylint: disable=no-member

        expected_user_values = {
            'first_name': '',
            'last_name': '',
            'is_active': False,
            'username': self.retired_username,
        }
        for field, expected_value in expected_user_values.iteritems():
            self.assertEqual(expected_value, getattr(self.test_user, field))

        for field, expected_value in USER_PROFILE_PII.iteritems():
            self.assertEqual(expected_value, getattr(self.test_user.profile, field))

        self.assertIsNone(self.test_user.profile.profile_image_uploaded_at)
        mock_get_profile_image_names.assert_called_once_with(self.original_username)
        mock_remove_profile_images.assert_called_once_with(
            mock_get_profile_image_names.return_value
        )

        self.assertFalse(
            SocialLink.objects.filter(user_profile=self.test_user.profile).exists()
        )

        self.assertIsNone(cache.get(self.cache_key))

        self._data_sharing_consent_assertions()
        self._sapsf_audit_assertions()
        self._pending_enterprise_customer_user_assertions()
        self._entitlement_support_detail_assertions()

        self._photo_verification_assertions()
        self.assertFalse(PendingEmailChange.objects.filter(user=self.test_user).exists())
        self.assertFalse(UserOrgTag.objects.filter(user=self.test_user).exists())

        self.assertFalse(CourseEnrollmentAllowed.objects.filter(email=self.original_email).exists())
        self.assertFalse(UnregisteredLearnerCohortAssignments.objects.filter(email=self.original_email).exists())

    def test_deletes_pii_from_user_profile(self):
        for model_field, value_to_assign in USER_PROFILE_PII.iteritems():
            if value_to_assign == '':
                value = 'foo'
            else:
                value = mock.Mock()
            setattr(self.test_user.profile, model_field, value)

        AccountRetirementView.clear_pii_from_userprofile(self.test_user)

        for model_field, value_to_assign in USER_PROFILE_PII.iteritems():
            self.assertEqual(value_to_assign, getattr(self.test_user.profile, model_field))

        social_links = SocialLink.objects.filter(
            user_profile=self.test_user.profile
        )
        self.assertFalse(social_links.exists())

    @mock.patch('openedx.core.djangoapps.user_api.accounts.views.get_profile_image_names')
    @mock.patch('openedx.core.djangoapps.user_api.accounts.views.remove_profile_images')
    def test_removes_user_profile_images(
        self, mock_remove_profile_images, mock_get_profile_image_names
    ):
        test_datetime = datetime.datetime(2018, 1, 1)
        self.test_user.profile.profile_image_uploaded_at = test_datetime

        AccountRetirementView.delete_users_profile_images(self.test_user)

        self.test_user.profile.refresh_from_db()  # pylint: disable=no-member

        self.assertIsNone(self.test_user.profile.profile_image_uploaded_at)
        mock_get_profile_image_names.assert_called_once_with(self.test_user.username)
        mock_remove_profile_images.assert_called_once_with(
            mock_get_profile_image_names.return_value
        )

    def test_can_delete_user_profiles_country_cache(self):
        AccountRetirementView.delete_users_country_cache(self.test_user)
        self.assertIsNone(cache.get(self.cache_key))

    def test_can_retire_users_datasharingconsent(self):
        AccountRetirementView.retire_users_data_sharing_consent(self.test_user.username, self.retired_username)
        self._data_sharing_consent_assertions()

    def _data_sharing_consent_assertions(self):
        """
        Helper method for asserting that ``DataSharingConsent`` objects are retired.
        """
        self.consent.refresh_from_db()
        self.assertEqual(self.retired_username, self.consent.username)
        test_users_data_sharing_consent = DataSharingConsent.objects.filter(
            username=self.original_username
        )
        self.assertFalse(test_users_data_sharing_consent.exists())

    def test_can_retire_users_sap_success_factors_audits(self):
        AccountRetirementView.retire_sapsf_data_transmission(self.test_user)
        self._sapsf_audit_assertions()

    def _sapsf_audit_assertions(self):
        """
        Helper method for asserting that ``SapSuccessFactorsLearnerDataTransmissionAudit`` objects are retired.
        """
        self.sapsf_audit.refresh_from_db()
        self.assertEqual('', self.sapsf_audit.sapsf_user_id)
        audits_for_original_user_id = SapSuccessFactorsLearnerDataTransmissionAudit.objects.filter(
            sapsf_user_id=self.test_user.id,
        )
        self.assertFalse(audits_for_original_user_id.exists())

    def test_can_retire_user_from_pendingenterprisecustomeruser(self):
        AccountRetirementView.retire_user_from_pending_enterprise_customer_user(self.test_user, self.retired_email)
        self._pending_enterprise_customer_user_assertions()

    def _pending_enterprise_customer_user_assertions(self):
        """
        Helper method for asserting that ``PendingEnterpriseCustomerUser`` objects are retired.
        """
        self.pending_enterprise_user.refresh_from_db()
        self.assertEqual(self.retired_email, self.pending_enterprise_user.user_email)
        pending_enterprise_users = PendingEnterpriseCustomerUser.objects.filter(
            user_email=self.original_email
        )
        self.assertFalse(pending_enterprise_users.exists())

    def test_course_entitlement_support_detail_comments_are_retired(self):
        AccountRetirementView.retire_entitlement_support_detail(self.test_user)
        self._entitlement_support_detail_assertions()

    def _entitlement_support_detail_assertions(self):
        """
        Helper method for asserting that ``CourseEntitleSupportDetail`` objects are retired.
        """
        self.entitlement_support_detail.refresh_from_db()
        self.assertEqual('', self.entitlement_support_detail.comments)

    def _photo_verification_assertions(self):
        """
        Helper method for asserting that ``SoftwareSecurePhotoVerification`` objects are retired.
        """
        self.photo_verification.refresh_from_db()
        self.assertEqual(self.test_user, self.photo_verification.user)
        for field in ('name', 'face_image_url', 'photo_id_image_url', 'photo_id_key'):
            self.assertEqual('', getattr(self.photo_verification, field))
