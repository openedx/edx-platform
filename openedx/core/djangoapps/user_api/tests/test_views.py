"""Tests for the user API at the HTTP request level. """

import datetime
import json
from unittest import skipUnless

import ddt
import httpretty
import mock
from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.urls import reverse
from django.test.client import RequestFactory
from django.test.testcases import TransactionTestCase
from django.test.utils import override_settings
from opaque_keys.edx.keys import CourseKey
from pytz import common_timezones_set, UTC
from six import text_type
from social_django.models import UserSocialAuth, Partial

from django_comment_common import models
from openedx.core.djangoapps.user_api.accounts.tests.test_retirement_views import RetirementTestCase
from openedx.core.djangoapps.user_api.models import UserRetirementStatus
from openedx.core.djangoapps.site_configuration.helpers import get_value
from openedx.core.lib.api.test_utils import ApiTestCase, TEST_API_KEY
from openedx.core.lib.time_zone_utils import get_display_time_zone
from openedx.core.djangoapps.site_configuration.tests.test_util import with_site_configuration
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms
from student.tests.factories import UserFactory
from student.models import get_retired_email_by_email
from third_party_auth.tests.testutil import simulate_running_pipeline, ThirdPartyAuthTestMixin
from third_party_auth.tests.utils import (
    ThirdPartyOAuthTestMixin, ThirdPartyOAuthTestMixinFacebook, ThirdPartyOAuthTestMixinGoogle
)
from util.password_policy_validators import password_max_length, password_min_length
from .test_helpers import TestCaseForm
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from ..accounts import (
    NAME_MAX_LENGTH, EMAIL_MIN_LENGTH, EMAIL_MAX_LENGTH,
    USERNAME_MIN_LENGTH, USERNAME_MAX_LENGTH, USERNAME_BAD_LENGTH_MSG
)
from ..accounts.api import get_account_settings
from ..models import UserOrgTag
from ..tests.factories import UserPreferenceFactory
from ..tests.test_constants import SORTED_COUNTRIES

USER_LIST_URI = "/user_api/v1/users/"
USER_PREFERENCE_LIST_URI = "/user_api/v1/user_prefs/"
ROLE_LIST_URI = "/user_api/v1/forum_roles/Moderator/users/"


class UserAPITestCase(ApiTestCase):
    """
    Parent test case for User API workflow coverage
    """
    LIST_URI = USER_LIST_URI

    def get_uri_for_user(self, target_user):
        """Given a user object, get the URI for the corresponding resource"""
        users = self.get_json(USER_LIST_URI)["results"]
        for user in users:
            if user["id"] == target_user.id:
                return user["url"]
        self.fail()

    def get_uri_for_pref(self, target_pref):
        """Given a user preference object, get the URI for the corresponding resource"""
        prefs = self.get_json(USER_PREFERENCE_LIST_URI)["results"]
        for pref in prefs:
            if pref["user"]["id"] == target_pref.user.id and pref["key"] == target_pref.key:
                return pref["url"]
        self.fail()

    def assertUserIsValid(self, user):
        """Assert that the given user result is valid"""
        self.assertItemsEqual(user.keys(), ["email", "id", "name", "username", "preferences", "url"])
        self.assertItemsEqual(
            user["preferences"].items(),
            [(pref.key, pref.value) for pref in self.prefs if pref.user.id == user["id"]]
        )
        self.assertSelfReferential(user)

    def assertPrefIsValid(self, pref):
        """
        Assert that the given preference is acknowledged by the system
        """
        self.assertItemsEqual(pref.keys(), ["user", "key", "value", "url"])
        self.assertSelfReferential(pref)
        self.assertUserIsValid(pref["user"])


class EmptyUserTestCase(UserAPITestCase):
    """
    Test that the endpoint supports empty user result sets
    """
    def test_get_list_empty(self):
        result = self.get_json(self.LIST_URI)
        self.assertEqual(result["count"], 0)
        self.assertIsNone(result["next"])
        self.assertIsNone(result["previous"])
        self.assertEqual(result["results"], [])


class EmptyRoleTestCase(UserAPITestCase):
    """Test that the endpoint supports empty result sets"""
    course_id = CourseKey.from_string("org/course/run")
    LIST_URI = ROLE_LIST_URI + "?course_id=" + unicode(course_id)

    def test_get_list_empty(self):
        """Test that the endpoint properly returns empty result sets"""
        result = self.get_json(self.LIST_URI)
        self.assertEqual(result["count"], 0)
        self.assertIsNone(result["next"])
        self.assertIsNone(result["previous"])
        self.assertEqual(result["results"], [])


class UserApiTestCase(UserAPITestCase):
    """
    Generalized test case class for specific implementations below
    """
    def setUp(self):
        super(UserApiTestCase, self).setUp()
        self.users = [
            UserFactory.create(
                email="test{0}@test.org".format(i),
                profile__name="Test {0}".format(i)
            )
            for i in range(5)
        ]
        self.prefs = [
            UserPreferenceFactory.create(user=self.users[0], key="key0"),
            UserPreferenceFactory.create(user=self.users[0], key="key1"),
            UserPreferenceFactory.create(user=self.users[1], key="key0")
        ]


class RoleTestCase(UserApiTestCase):
    """
    Test cases covering Role-related views and their behaviors
    """
    course_id = CourseKey.from_string("org/course/run")
    LIST_URI = ROLE_LIST_URI + "?course_id=" + unicode(course_id)

    def setUp(self):
        super(RoleTestCase, self).setUp()
        (role, _) = models.Role.objects.get_or_create(
            name=models.FORUM_ROLE_MODERATOR,
            course_id=self.course_id
        )
        for user in self.users:
            user.roles.add(role)

    def test_options_list(self):
        self.assertAllowedMethods(self.LIST_URI, ["OPTIONS", "GET", "HEAD"])

    def test_post_list_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.request_with_auth("post", self.LIST_URI))

    def test_put_list_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.request_with_auth("put", self.LIST_URI))

    def test_patch_list_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.request_with_auth("patch", self.LIST_URI))

    def test_delete_list_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.request_with_auth("delete", self.LIST_URI))

    def test_list_unauthorized(self):
        self.assertHttpForbidden(self.client.get(self.LIST_URI))

    @override_settings(DEBUG=True)
    @override_settings(EDX_API_KEY=None)
    def test_debug_auth(self):
        self.assertHttpForbidden(self.client.get(self.LIST_URI))

    @override_settings(DEBUG=False)
    @override_settings(EDX_API_KEY=TEST_API_KEY)
    def test_basic_auth(self):
        # ensure that having basic auth headers in the mix does not break anything
        self.assertHttpOK(
            self.request_with_auth("get", self.LIST_URI,
                                   **self.basic_auth("someuser", "somepass")))
        self.assertHttpForbidden(
            self.client.get(self.LIST_URI, **self.basic_auth("someuser", "somepass")))

    def test_get_list_nonempty(self):
        result = self.get_json(self.LIST_URI)
        users = result["results"]
        self.assertEqual(result["count"], len(self.users))
        self.assertEqual(len(users), len(self.users))
        self.assertIsNone(result["next"])
        self.assertIsNone(result["previous"])
        for user in users:
            self.assertUserIsValid(user)

    def test_required_parameter(self):
        response = self.request_with_auth("get", ROLE_LIST_URI)
        self.assertHttpBadRequest(response)

    def test_get_list_pagination(self):
        first_page = self.get_json(self.LIST_URI, data={
            "page_size": 3,
            "course_id": text_type(self.course_id),
        })
        self.assertEqual(first_page["count"], 5)
        first_page_next_uri = first_page["next"]
        self.assertIsNone(first_page["previous"])
        first_page_users = first_page["results"]
        self.assertEqual(len(first_page_users), 3)

        second_page = self.get_json(first_page_next_uri)
        self.assertEqual(second_page["count"], 5)
        self.assertIsNone(second_page["next"])
        second_page_prev_uri = second_page["previous"]
        second_page_users = second_page["results"]
        self.assertEqual(len(second_page_users), 2)

        self.assertEqual(self.get_json(second_page_prev_uri), first_page)

        for user in first_page_users + second_page_users:
            self.assertUserIsValid(user)
        all_user_uris = [user["url"] for user in first_page_users + second_page_users]
        self.assertEqual(len(set(all_user_uris)), 5)


class UserViewSetTest(UserApiTestCase):
    """
    Test cases covering the User DRF view set class and its various behaviors
    """
    LIST_URI = USER_LIST_URI

    def setUp(self):
        super(UserViewSetTest, self).setUp()
        self.detail_uri = self.get_uri_for_user(self.users[0])

    # List view tests

    def test_options_list(self):
        self.assertAllowedMethods(self.LIST_URI, ["OPTIONS", "GET", "HEAD"])

    def test_post_list_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.request_with_auth("post", self.LIST_URI))

    def test_put_list_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.request_with_auth("put", self.LIST_URI))

    def test_patch_list_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.request_with_auth("patch", self.LIST_URI))

    def test_delete_list_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.request_with_auth("delete", self.LIST_URI))

    def test_list_unauthorized(self):
        self.assertHttpForbidden(self.client.get(self.LIST_URI))

    @override_settings(DEBUG=True)
    @override_settings(EDX_API_KEY=None)
    def test_debug_auth(self):
        self.assertHttpForbidden(self.client.get(self.LIST_URI))

    @override_settings(DEBUG=False)
    @override_settings(EDX_API_KEY=TEST_API_KEY)
    def test_basic_auth(self):
        # ensure that having basic auth headers in the mix does not break anything
        self.assertHttpOK(
            self.request_with_auth("get", self.LIST_URI,
                                   **self.basic_auth('someuser', 'somepass')))
        self.assertHttpForbidden(
            self.client.get(self.LIST_URI, **self.basic_auth('someuser', 'somepass')))

    def test_get_list_nonempty(self):
        result = self.get_json(self.LIST_URI)
        self.assertEqual(result["count"], 5)
        self.assertIsNone(result["next"])
        self.assertIsNone(result["previous"])
        users = result["results"]
        self.assertEqual(len(users), 5)
        for user in users:
            self.assertUserIsValid(user)

    def test_get_list_pagination(self):
        first_page = self.get_json(self.LIST_URI, data={"page_size": 3})
        self.assertEqual(first_page["count"], 5)
        first_page_next_uri = first_page["next"]
        self.assertIsNone(first_page["previous"])
        first_page_users = first_page["results"]
        self.assertEqual(len(first_page_users), 3)

        second_page = self.get_json(first_page_next_uri)
        self.assertEqual(second_page["count"], 5)
        self.assertIsNone(second_page["next"])
        second_page_prev_uri = second_page["previous"]
        second_page_users = second_page["results"]
        self.assertEqual(len(second_page_users), 2)

        self.assertEqual(self.get_json(second_page_prev_uri), first_page)

        for user in first_page_users + second_page_users:
            self.assertUserIsValid(user)
        all_user_uris = [user["url"] for user in first_page_users + second_page_users]
        self.assertEqual(len(set(all_user_uris)), 5)

    # Detail view tests

    def test_options_detail(self):
        self.assertAllowedMethods(self.detail_uri, ["OPTIONS", "GET", "HEAD"])

    def test_post_detail_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.request_with_auth("post", self.detail_uri))

    def test_put_detail_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.request_with_auth("put", self.detail_uri))

    def test_patch_detail_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.request_with_auth("patch", self.detail_uri))

    def test_delete_detail_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.request_with_auth("delete", self.detail_uri))

    def test_get_detail_unauthorized(self):
        self.assertHttpForbidden(self.client.get(self.detail_uri))

    def test_get_detail(self):
        user = self.users[1]
        uri = self.get_uri_for_user(user)
        self.assertEqual(
            self.get_json(uri),
            {
                "email": user.email,
                "id": user.id,
                "name": user.profile.name,
                "username": user.username,
                "preferences": dict([
                    (user_pref.key, user_pref.value)
                    for user_pref in self.prefs
                    if user_pref.user == user
                ]),
                "url": uri
            }
        )


class UserPreferenceViewSetTest(CacheIsolationTestCase, UserApiTestCase):
    """
    Test cases covering the User Preference DRF view class and its various behaviors
    """
    LIST_URI = USER_PREFERENCE_LIST_URI

    ENABLED_CACHES = ['default']

    def setUp(self):
        super(UserPreferenceViewSetTest, self).setUp()
        self.detail_uri = self.get_uri_for_pref(self.prefs[0])

    # List view tests

    def test_options_list(self):
        self.assertAllowedMethods(self.LIST_URI, ["OPTIONS", "GET", "HEAD"])

    def test_put_list_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.request_with_auth("put", self.LIST_URI))

    def test_patch_list_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.request_with_auth("patch", self.LIST_URI))

    def test_delete_list_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.request_with_auth("delete", self.LIST_URI))

    def test_list_unauthorized(self):
        self.assertHttpForbidden(self.client.get(self.LIST_URI))

    @override_settings(DEBUG=True)
    @override_settings(EDX_API_KEY=None)
    def test_debug_auth(self):
        self.assertHttpForbidden(self.client.get(self.LIST_URI))

    def test_get_list_nonempty(self):
        result = self.get_json(self.LIST_URI)
        self.assertEqual(result["count"], 3)
        self.assertIsNone(result["next"])
        self.assertIsNone(result["previous"])
        prefs = result["results"]
        self.assertEqual(len(prefs), 3)
        for pref in prefs:
            self.assertPrefIsValid(pref)

    def test_get_list_filter_key_empty(self):
        result = self.get_json(self.LIST_URI, data={"key": "non-existent"})
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["results"], [])

    def test_get_list_filter_key_nonempty(self):
        result = self.get_json(self.LIST_URI, data={"key": "key0"})
        self.assertEqual(result["count"], 2)
        prefs = result["results"]
        self.assertEqual(len(prefs), 2)
        for pref in prefs:
            self.assertPrefIsValid(pref)
            self.assertEqual(pref["key"], "key0")

    def test_get_list_filter_user_empty(self):
        def test_id(user_id):
            result = self.get_json(self.LIST_URI, data={"user": user_id})
            self.assertEqual(result["count"], 0)
            self.assertEqual(result["results"], [])
        test_id(self.users[2].id)
        # TODO: If the given id does not match a user, then the filter is a no-op
        # test_id(42)
        # test_id("asdf")

    def test_get_list_filter_user_nonempty(self):
        user_id = self.users[0].id
        result = self.get_json(self.LIST_URI, data={"user": user_id})
        self.assertEqual(result["count"], 2)
        prefs = result["results"]
        self.assertEqual(len(prefs), 2)
        for pref in prefs:
            self.assertPrefIsValid(pref)
            self.assertEqual(pref["user"]["id"], user_id)

    def test_get_list_pagination(self):
        first_page = self.get_json(self.LIST_URI, data={"page_size": 2})
        self.assertEqual(first_page["count"], 3)
        first_page_next_uri = first_page["next"]
        self.assertIsNone(first_page["previous"])
        first_page_prefs = first_page["results"]
        self.assertEqual(len(first_page_prefs), 2)

        second_page = self.get_json(first_page_next_uri)
        self.assertEqual(second_page["count"], 3)
        self.assertIsNone(second_page["next"])
        second_page_prev_uri = second_page["previous"]
        second_page_prefs = second_page["results"]
        self.assertEqual(len(second_page_prefs), 1)

        self.assertEqual(self.get_json(second_page_prev_uri), first_page)

        for pref in first_page_prefs + second_page_prefs:
            self.assertPrefIsValid(pref)
        all_pref_uris = [pref["url"] for pref in first_page_prefs + second_page_prefs]
        self.assertEqual(len(set(all_pref_uris)), 3)

    # Detail view tests

    def test_options_detail(self):
        self.assertAllowedMethods(self.detail_uri, ["OPTIONS", "GET", "HEAD"])

    def test_post_detail_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.request_with_auth("post", self.detail_uri))

    def test_put_detail_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.request_with_auth("put", self.detail_uri))

    def test_patch_detail_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.request_with_auth("patch", self.detail_uri))

    def test_delete_detail_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.request_with_auth("delete", self.detail_uri))

    def test_detail_unauthorized(self):
        self.assertHttpForbidden(self.client.get(self.detail_uri))

    def test_get_detail(self):
        pref = self.prefs[1]
        uri = self.get_uri_for_pref(pref)
        self.assertEqual(
            self.get_json(uri),
            {
                "user": {
                    "email": pref.user.email,
                    "id": pref.user.id,
                    "name": pref.user.profile.name,
                    "username": pref.user.username,
                    "preferences": dict([
                        (user_pref.key, user_pref.value)
                        for user_pref in self.prefs
                        if user_pref.user == pref.user
                    ]),
                    "url": self.get_uri_for_user(pref.user),
                },
                "key": pref.key,
                "value": pref.value,
                "url": uri,
            }
        )


class PreferenceUsersListViewTest(UserApiTestCase):
    """
    Test cases covering the list viewing behavior for user preferences
    """
    LIST_URI = "/user_api/v1/preferences/key0/users/"

    def test_options(self):
        self.assertAllowedMethods(self.LIST_URI, ["OPTIONS", "GET", "HEAD"])

    def test_put_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.request_with_auth("put", self.LIST_URI))

    def test_patch_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.request_with_auth("patch", self.LIST_URI))

    def test_delete_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.request_with_auth("delete", self.LIST_URI))

    def test_unauthorized(self):
        self.assertHttpForbidden(self.client.get(self.LIST_URI))

    @override_settings(DEBUG=True)
    @override_settings(EDX_API_KEY=None)
    def test_debug_auth(self):
        self.assertHttpForbidden(self.client.get(self.LIST_URI))

    def test_get_basic(self):
        result = self.get_json(self.LIST_URI)
        self.assertEqual(result["count"], 2)
        self.assertIsNone(result["next"])
        self.assertIsNone(result["previous"])
        users = result["results"]
        self.assertEqual(len(users), 2)
        for user in users:
            self.assertUserIsValid(user)

    def test_get_pagination(self):
        first_page = self.get_json(self.LIST_URI, data={"page_size": 1})
        self.assertEqual(first_page["count"], 2)
        first_page_next_uri = first_page["next"]
        self.assertIsNone(first_page["previous"])
        first_page_users = first_page["results"]
        self.assertEqual(len(first_page_users), 1)

        second_page = self.get_json(first_page_next_uri)
        self.assertEqual(second_page["count"], 2)
        self.assertIsNone(second_page["next"])
        second_page_prev_uri = second_page["previous"]
        second_page_users = second_page["results"]
        self.assertEqual(len(second_page_users), 1)

        self.assertEqual(self.get_json(second_page_prev_uri), first_page)

        for user in first_page_users + second_page_users:
            self.assertUserIsValid(user)
        all_user_uris = [user["url"] for user in first_page_users + second_page_users]
        self.assertEqual(len(set(all_user_uris)), 2)


@ddt.ddt
@skip_unless_lms
class LoginSessionViewTest(UserAPITestCase):
    """Tests for the login end-points of the user API. """

    USERNAME = "bob"
    EMAIL = "bob@example.com"
    PASSWORD = "password"

    def setUp(self):
        super(LoginSessionViewTest, self).setUp()
        self.url = reverse("user_api_login_session")

    @ddt.data("get", "post")
    def test_auth_disabled(self, method):
        self.assertAuthDisabled(method, self.url)

    def test_allowed_methods(self):
        self.assertAllowedMethods(self.url, ["GET", "POST", "HEAD", "OPTIONS"])

    def test_put_not_allowed(self):
        response = self.client.put(self.url)
        self.assertHttpMethodNotAllowed(response)

    def test_delete_not_allowed(self):
        response = self.client.delete(self.url)
        self.assertHttpMethodNotAllowed(response)

    def test_patch_not_allowed(self):
        response = self.client.patch(self.url)
        self.assertHttpMethodNotAllowed(response)

    def test_login_form(self):
        # Retrieve the login form
        response = self.client.get(self.url, content_type="application/json")
        self.assertHttpOK(response)

        # Verify that the form description matches what we expect
        form_desc = json.loads(response.content)
        self.assertEqual(form_desc["method"], "post")
        self.assertEqual(form_desc["submit_url"], self.url)
        self.assertEqual(form_desc["fields"], [
            {
                "name": "email",
                "defaultValue": "",
                "type": "email",
                "required": True,
                "label": "Email",
                "placeholder": "username@domain.com",
                "instructions": u"The email address you used to register with {platform_name}".format(
                    platform_name=settings.PLATFORM_NAME
                ),
                "restrictions": {
                    "min_length": EMAIL_MIN_LENGTH,
                    "max_length": EMAIL_MAX_LENGTH
                },
                "errorMessages": {},
                "supplementalText": "",
                "supplementalLink": "",
            },
            {
                "name": "password",
                "defaultValue": "",
                "type": "password",
                "required": True,
                "label": "Password",
                "placeholder": "",
                "instructions": "",
                "restrictions": {
                    "max_length": password_max_length(),
                },
                "errorMessages": {},
                "supplementalText": "",
                "supplementalLink": "",
            },
            {
                "name": "remember",
                "defaultValue": False,
                "type": "checkbox",
                "required": False,
                "label": "Remember me",
                "placeholder": "",
                "instructions": "",
                "restrictions": {},
                "errorMessages": {},
                "supplementalText": "",
                "supplementalLink": "",
            },
        ])

    def test_login(self):
        # Create a test user
        UserFactory.create(username=self.USERNAME, email=self.EMAIL, password=self.PASSWORD)

        # Login
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "password": self.PASSWORD,
        })
        self.assertHttpOK(response)

        # Verify that we logged in successfully by accessing
        # a page that requires authentication.
        response = self.client.get(reverse("dashboard"))
        self.assertHttpOK(response)

    @ddt.data(
        (json.dumps(True), False),
        (json.dumps(False), True),
        (None, True),
    )
    @ddt.unpack
    def test_login_remember_me(self, remember_value, expire_at_browser_close):
        # Create a test user
        UserFactory.create(username=self.USERNAME, email=self.EMAIL, password=self.PASSWORD)

        # Login and remember me
        data = {
            "email": self.EMAIL,
            "password": self.PASSWORD,
        }

        if remember_value is not None:
            data["remember"] = remember_value

        response = self.client.post(self.url, data)
        self.assertHttpOK(response)

        # Verify that the session expiration was set correctly
        self.assertEqual(
            self.client.session.get_expire_at_browser_close(),
            expire_at_browser_close
        )

    def test_invalid_credentials(self):
        # Create a test user
        UserFactory.create(username=self.USERNAME, email=self.EMAIL, password=self.PASSWORD)

        # Invalid password
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "password": "invalid"
        })
        self.assertHttpForbidden(response)

        # Invalid email address
        response = self.client.post(self.url, {
            "email": "invalid@example.com",
            "password": self.PASSWORD,
        })
        self.assertHttpForbidden(response)

    def test_missing_login_params(self):
        # Create a test user
        UserFactory.create(username=self.USERNAME, email=self.EMAIL, password=self.PASSWORD)

        # Missing password
        response = self.client.post(self.url, {
            "email": self.EMAIL,
        })
        self.assertHttpBadRequest(response)

        # Missing email
        response = self.client.post(self.url, {
            "password": self.PASSWORD,
        })
        self.assertHttpBadRequest(response)

        # Missing both email and password
        response = self.client.post(self.url, {})


@ddt.ddt
@skip_unless_lms
class PasswordResetViewTest(UserAPITestCase):
    """Tests of the user API's password reset endpoint. """

    def setUp(self):
        super(PasswordResetViewTest, self).setUp()
        self.url = reverse("user_api_password_reset")

    @ddt.data("get", "post")
    def test_auth_disabled(self, method):
        self.assertAuthDisabled(method, self.url)

    def test_allowed_methods(self):
        self.assertAllowedMethods(self.url, ["GET", "HEAD", "OPTIONS"])

    def test_put_not_allowed(self):
        response = self.client.put(self.url)
        self.assertHttpMethodNotAllowed(response)

    def test_delete_not_allowed(self):
        response = self.client.delete(self.url)
        self.assertHttpMethodNotAllowed(response)

    def test_patch_not_allowed(self):
        response = self.client.patch(self.url)
        self.assertHttpMethodNotAllowed(response)

    def test_password_reset_form(self):
        # Retrieve the password reset form
        response = self.client.get(self.url, content_type="application/json")
        self.assertHttpOK(response)

        # Verify that the form description matches what we expect
        form_desc = json.loads(response.content)
        self.assertEqual(form_desc["method"], "post")
        self.assertEqual(form_desc["submit_url"], reverse("password_change_request"))
        self.assertEqual(form_desc["fields"], [
            {
                "name": "email",
                "defaultValue": "",
                "type": "email",
                "required": True,
                "label": "Email",
                "placeholder": "username@domain.com",
                "instructions": u"The email address you used to register with {platform_name}".format(
                    platform_name=settings.PLATFORM_NAME
                ),
                "restrictions": {
                    "min_length": EMAIL_MIN_LENGTH,
                    "max_length": EMAIL_MAX_LENGTH
                },
                "errorMessages": {},
                "supplementalText": "",
                "supplementalLink": "",
            }
        ])


@ddt.ddt
@skip_unless_lms
class RegistrationViewValidationErrorTest(ThirdPartyAuthTestMixin, UserAPITestCase, RetirementTestCase):
    """
    Tests for catching duplicate email and username validation errors within
    the registration end-points of the User API.
    """

    maxDiff = None

    USERNAME = "bob"
    EMAIL = "bob@example.com"
    PASSWORD = "password"
    NAME = "Bob Smith"
    EDUCATION = "m"
    YEAR_OF_BIRTH = "1998"
    ADDRESS = "123 Fake Street"
    CITY = "Springfield"
    COUNTRY = "us"
    GOALS = "Learn all the things!"

    def setUp(self):
        super(RegistrationViewValidationErrorTest, self).setUp()
        self.url = reverse("user_api_registration")

    def _retireRequestUser(self):
        """
        Very basic user retirement initiation, logic copied form DeactivateLogoutView.  This only lands the user in
        PENDING, simulating a retirement request only.
        """
        user = User.objects.get(username=self.USERNAME)
        UserRetirementStatus.create_retirement(user)
        user.email = get_retired_email_by_email(user.email)
        user.set_unusable_password()
        user.save()

    @mock.patch('openedx.core.djangoapps.user_api.views.check_account_exists')
    def test_register_retired_email_validation_error(self, dummy_check_account_exists):
        dummy_check_account_exists.return_value = []
        # Register the first user
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertHttpOK(response)

        # Initiate retirement for the above user:
        self._retireRequestUser()

        # Try to create a second user with the same email address as the retired user
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": "Someone Else",
            "username": "someone_else",
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertEqual(response.status_code, 400)
        response_json = json.loads(response.content)
        self.assertEqual(
            response_json,
            {
                "email": [{
                    "user_message": (
                        "It looks like {} belongs to an existing account. "
                        "Try again with a different email address."
                    ).format(
                        self.EMAIL
                    )
                }]
            }
        )

    def test_register_retired_email_validation_error_no_bypass_check_account_exists(self):
        """
        This test is the same as above, except it doesn't bypass check_account_exists.  Not bypassing this function
        results in the same error message, but a 409 status code rather than 400.
        """
        # Register the first user
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertHttpOK(response)

        # Initiate retirement for the above user:
        self._retireRequestUser()

        # Try to create a second user with the same email address as the retired user
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": "Someone Else",
            "username": "someone_else",
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertEqual(response.status_code, 409)
        response_json = json.loads(response.content)
        self.assertEqual(
            response_json,
            {
                "email": [{
                    "user_message": (
                        "It looks like {} belongs to an existing account. "
                        "Try again with a different email address."
                    ).format(
                        self.EMAIL
                    )
                }]
            }
        )

    @mock.patch('openedx.core.djangoapps.user_api.views.check_account_exists')
    def test_register_duplicate_email_validation_error(self, dummy_check_account_exists):
        dummy_check_account_exists.return_value = []
        # Register the first user
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertHttpOK(response)

        # Try to create a second user with the same email address
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": "Someone Else",
            "username": "someone_else",
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertEqual(response.status_code, 400)
        response_json = json.loads(response.content)
        self.assertEqual(
            response_json,
            {
                "email": [{
                    "user_message": (
                        "It looks like {} belongs to an existing account. "
                        "Try again with a different email address."
                    ).format(
                        self.EMAIL
                    )
                }]
            }
        )

    @mock.patch('openedx.core.djangoapps.user_api.views.check_account_exists')
    def test_register_duplicate_username_account_validation_error(self, dummy_check_account_exists):
        dummy_check_account_exists.return_value = []
        # Register the first user
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertHttpOK(response)

        # Try to create a second user with the same username
        response = self.client.post(self.url, {
            "email": "someone+else@example.com",
            "name": "Someone Else",
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertEqual(response.status_code, 409)
        response_json = json.loads(response.content)
        self.assertEqual(
            response_json,
            {
                u"username": [{
                    u"user_message": (
                        u"An account with the Public Username '{}' already exists."
                    ).format(
                        self.USERNAME
                    )
                }]
            }
        )

    @mock.patch('openedx.core.djangoapps.user_api.views.check_account_exists')
    def test_register_duplicate_username_and_email_validation_errors(self, dummy_check_account_exists):
        dummy_check_account_exists.return_value = []
        # Register the first user
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertHttpOK(response)

        # Try to create a second user with the same username
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": "Someone Else",
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertEqual(response.status_code, 400)
        response_json = json.loads(response.content)
        self.assertEqual(
            response_json,
            {
                "email": [{
                    "user_message": (
                        "It looks like {} belongs to an existing account. "
                        "Try again with a different email address."
                    ).format(
                        self.EMAIL
                    )
                }]
            }
        )


@ddt.ddt
@skip_unless_lms
class RegistrationViewTest(ThirdPartyAuthTestMixin, UserAPITestCase):
    """Tests for the registration end-points of the User API. """

    maxDiff = None

    USERNAME = "bob"
    EMAIL = "bob@example.com"
    PASSWORD = "password"
    NAME = "Bob Smith"
    EDUCATION = "m"
    YEAR_OF_BIRTH = "1998"
    ADDRESS = "123 Fake Street"
    CITY = "Springfield"
    COUNTRY = "us"
    GOALS = "Learn all the things!"
    PROFESSION_OPTIONS = [
        {
            "name": u'--',
            "value": u'',
            "default": True

        },
        {
            "value": u'software engineer',
            "name": u'Software Engineer',
            "default": False
        },
        {
            "value": u'teacher',
            "name": u'Teacher',
            "default": False
        },
        {
            "value": u'other',
            "name": u'Other',
            "default": False
        }
    ]
    SPECIALTY_OPTIONS = [
        {
            "name": u'--',
            "value": u'',
            "default": True

        },
        {
            "value": "aerospace",
            "name": "Aerospace",
            "default": False
        },
        {
            "value": u'early education',
            "name": u'Early Education',
            "default": False
        },
        {
            "value": u'n/a',
            "name": u'N/A',
            "default": False
        }
    ]
    link_template = "<a href='/honor' target='_blank'>{link_label}</a>"

    def setUp(self):
        super(RegistrationViewTest, self).setUp()
        self.url = reverse("user_api_registration")

    @ddt.data("get", "post")
    def test_auth_disabled(self, method):
        self.assertAuthDisabled(method, self.url)

    def test_allowed_methods(self):
        self.assertAllowedMethods(self.url, ["GET", "POST", "HEAD", "OPTIONS"])

    def test_put_not_allowed(self):
        response = self.client.put(self.url)
        self.assertHttpMethodNotAllowed(response)

    def test_delete_not_allowed(self):
        response = self.client.delete(self.url)
        self.assertHttpMethodNotAllowed(response)

    def test_patch_not_allowed(self):
        response = self.client.patch(self.url)
        self.assertHttpMethodNotAllowed(response)

    def test_register_form_default_fields(self):
        no_extra_fields_setting = {}

        self._assert_reg_field(
            no_extra_fields_setting,
            {
                u"name": u"email",
                u"type": u"email",
                u"required": True,
                u"label": u"Email",
                u"instructions": u"This is what you will use to login.",
                u"restrictions": {
                    "min_length": EMAIL_MIN_LENGTH,
                    "max_length": EMAIL_MAX_LENGTH
                },
            }
        )

        self._assert_reg_field(
            no_extra_fields_setting,
            {
                u"name": u"name",
                u"type": u"text",
                u"required": True,
                u"label": u"Full Name",
                u"instructions": u"This name will be used on any certificates that you earn.",
                u"restrictions": {
                    "max_length": 255
                },
            }
        )

        self._assert_reg_field(
            no_extra_fields_setting,
            {
                u"name": u"username",
                u"type": u"text",
                u"required": True,
                u"label": u"Public Username",
                u"instructions": u"The name that will identify you in your courses. "
                                 u"It cannot be changed later.",
                u"restrictions": {
                    "min_length": USERNAME_MIN_LENGTH,
                    "max_length": USERNAME_MAX_LENGTH
                },
            }
        )

        self._assert_reg_field(
            no_extra_fields_setting,
            {
                u"placeholder": "",
                u"name": u"password",
                u"type": u"password",
                u"required": True,
                u"label": u"Password",
                u"instructions": u'Your password must contain at least {} characters.'.format(password_min_length()),
                u"restrictions": {
                    'min_length': password_min_length(),
                    'max_length': password_max_length(),
                },
            }
        )

    @override_settings(PASSWORD_COMPLEXITY={'NON ASCII': 1, 'UPPER': 3})
    def test_register_form_password_complexity(self):
        no_extra_fields_setting = {}

        # Without enabling password policy
        self._assert_reg_field(
            no_extra_fields_setting,
            {
                u'name': u'password',
                u'label': u'Password',
                u'instructions': u'Your password must contain at least {} characters.'.format(password_min_length()),
                u'restrictions': {
                    'min_length': password_min_length(),
                    'max_length': password_max_length(),
                },
            }
        )

        # Now with an enabled password policy
        with mock.patch.dict(settings.FEATURES, {'ENFORCE_PASSWORD_POLICY': True}):
            msg = u'Your password must contain at least {} characters, including '\
                  u'3 uppercase letters & 1 symbol.'.format(password_min_length())
            self._assert_reg_field(
                no_extra_fields_setting,
                {
                    u'name': u'password',
                    u'label': u'Password',
                    u'instructions': msg,
                    u'restrictions': {
                        'min_length': password_min_length(),
                        'max_length': password_max_length(),
                        'non_ascii': 1,
                        'upper': 3,
                    },
                }
            )

    @override_settings(REGISTRATION_EXTENSION_FORM='openedx.core.djangoapps.user_api.tests.test_helpers.TestCaseForm')
    def test_extension_form_fields(self):
        no_extra_fields_setting = {}

        # Verify other fields didn't disappear for some reason.
        self._assert_reg_field(
            no_extra_fields_setting,
            {
                u"name": u"email",
                u"type": u"email",
                u"required": True,
                u"label": u"Email",
                u"instructions": u"This is what you will use to login.",
                u"restrictions": {
                    "min_length": EMAIL_MIN_LENGTH,
                    "max_length": EMAIL_MAX_LENGTH
                },
            }
        )

        self._assert_reg_field(
            no_extra_fields_setting,
            {
                u"name": u"favorite_editor",
                u"type": u"select",
                u"required": False,
                u"label": u"Favorite Editor",
                u"placeholder": u"cat",
                u"defaultValue": u"vim",
                u"errorMessages": {
                    u'required': u'This field is required.',
                    u'invalid_choice': u'Select a valid choice. %(value)s is not one of the available choices.',
                }
            }
        )

        self._assert_reg_field(
            no_extra_fields_setting,
            {
                u"name": u"favorite_movie",
                u"type": u"text",
                u"required": True,
                u"label": u"Fav Flick",
                u"placeholder": None,
                u"defaultValue": None,
                u"errorMessages": {
                    u'required': u'Please tell us your favorite movie.',
                    u'invalid': u"We're pretty sure you made that movie up."
                },
                u"restrictions": {
                    "min_length": TestCaseForm.MOVIE_MIN_LEN,
                    "max_length": TestCaseForm.MOVIE_MAX_LEN,
                }
            }
        )

    @ddt.data(
        ('pk', 'PK', 'Bob123', 'Bob123'),
        ('Pk', 'PK', None, ''),
        ('pK', 'PK', 'Bob123@edx.org', 'Bob123_edx_org'),
        ('PK', 'PK', 'Bob123123123123123123123123123123123123', 'Bob123123123123123123123123123'),
        ('us', 'US', 'Bob-1231231&23123+1231(2312312312@3123123123', 'Bob-1231231_23123_1231_2312312'),
    )
    @ddt.unpack
    def test_register_form_third_party_auth_running_google(
            self,
            input_country_code,
            expected_country_code,
            input_username,
            expected_username):
        no_extra_fields_setting = {}
        country_options = (
            [
                {
                    "name": "--",
                    "value": "",
                    "default": False
                }
            ] + [
                {
                    "value": country_code,
                    "name": unicode(country_name),
                    "default": True if country_code == expected_country_code else False
                }
                for country_code, country_name in SORTED_COUNTRIES
            ]
        )

        provider = self.configure_google_provider(enabled=True)
        with simulate_running_pipeline(
            "openedx.core.djangoapps.user_api.api.third_party_auth.pipeline", "google-oauth2",
            email="bob@example.com",
            fullname="Bob",
            username=input_username,
            country=input_country_code
        ):
            self._assert_password_field_hidden(no_extra_fields_setting)
            self._assert_social_auth_provider_present(no_extra_fields_setting, provider)

            # Email should be filled in
            self._assert_reg_field(
                no_extra_fields_setting,
                {
                    u"name": u"email",
                    u"defaultValue": u"bob@example.com",
                    u"type": u"email",
                    u"required": True,
                    u"label": u"Email",
                    u"instructions": u"This is what you will use to login.",
                    u"restrictions": {
                        "min_length": EMAIL_MIN_LENGTH,
                        "max_length": EMAIL_MAX_LENGTH
                    },
                }
            )

            # Full Name should be filled in
            self._assert_reg_field(
                no_extra_fields_setting,
                {
                    u"name": u"name",
                    u"defaultValue": u"Bob",
                    u"type": u"text",
                    u"required": True,
                    u"label": u"Full Name",
                    u"instructions": u"This name will be used on any certificates that you earn.",
                    u"restrictions": {
                        "max_length": NAME_MAX_LENGTH,
                    }
                }
            )

            # Username should be filled in
            self._assert_reg_field(
                no_extra_fields_setting,
                {
                    u"name": u"username",
                    u"defaultValue": expected_username,
                    u"type": u"text",
                    u"required": True,
                    u"label": u"Public Username",
                    u"instructions": u"The name that will identify you in your courses. "
                                     u"It cannot be changed later.",
                    u"restrictions": {
                        "min_length": USERNAME_MIN_LENGTH,
                        "max_length": USERNAME_MAX_LENGTH
                    }
                }
            )

            # Country should be filled in.
            self._assert_reg_field(
                {u"country": u"required"},
                {
                    u"label": u"Country or Region of Residence",
                    u"name": u"country",
                    u"defaultValue": expected_country_code,
                    u"type": u"select",
                    u"required": True,
                    u"options": country_options,
                    u"instructions": u"The country or region where you live.",
                    u"errorMessages": {
                        u"required": u"Select your country or region of residence."
                    },
                }
            )

    def test_register_form_level_of_education(self):
        self._assert_reg_field(
            {"level_of_education": "optional"},
            {
                "name": "level_of_education",
                "type": "select",
                "required": False,
                "label": "Highest level of education completed",
                "options": [
                    {"value": "", "name": "--", "default": True},
                    {"value": "p", "name": "Doctorate", "default": False},
                    {"value": "m", "name": "Master's or professional degree", "default": False},
                    {"value": "b", "name": "Bachelor's degree", "default": False},
                    {"value": "a", "name": "Associate degree", "default": False},
                    {"value": "hs", "name": "Secondary/high school", "default": False},
                    {"value": "jhs", "name": "Junior secondary/junior high/middle school", "default": False},
                    {"value": "el", "name": "Elementary/primary school", "default": False},
                    {"value": "none", "name": "No formal education", "default": False},
                    {"value": "other", "name": "Other education", "default": False},
                ],
                "errorMessages": {
                    "required": "Select the highest level of education you have completed."
                }
            }
        )

    @mock.patch('openedx.core.djangoapps.user_api.api._')
    def test_register_form_level_of_education_translations(self, fake_gettext):
        fake_gettext.side_effect = lambda text: text + ' TRANSLATED'

        self._assert_reg_field(
            {"level_of_education": "optional"},
            {
                "name": "level_of_education",
                "type": "select",
                "required": False,
                "label": "Highest level of education completed TRANSLATED",
                "options": [
                    {"value": "", "name": "--", "default": True},
                    {"value": "p", "name": "Doctorate TRANSLATED", "default": False},
                    {"value": "m", "name": "Master's or professional degree TRANSLATED", "default": False},
                    {"value": "b", "name": "Bachelor's degree TRANSLATED", "default": False},
                    {"value": "a", "name": "Associate degree TRANSLATED", "default": False},
                    {"value": "hs", "name": "Secondary/high school TRANSLATED", "default": False},
                    {"value": "jhs", "name": "Junior secondary/junior high/middle school TRANSLATED", "default": False},
                    {"value": "el", "name": "Elementary/primary school TRANSLATED", "default": False},
                    {"value": "none", "name": "No formal education TRANSLATED", "default": False},
                    {"value": "other", "name": "Other education TRANSLATED", "default": False},
                ],
                "errorMessages": {
                    "required": "Select the highest level of education you have completed."
                }
            }
        )

    def test_register_form_gender(self):
        self._assert_reg_field(
            {"gender": "optional"},
            {
                "name": "gender",
                "type": "select",
                "required": False,
                "label": "Gender",
                "options": [
                    {"value": "", "name": "--", "default": True},
                    {"value": "m", "name": "Male", "default": False},
                    {"value": "f", "name": "Female", "default": False},
                    {"value": "o", "name": "Other/Prefer Not to Say", "default": False},
                ],
            }
        )

    @mock.patch('openedx.core.djangoapps.user_api.api._')
    def test_register_form_gender_translations(self, fake_gettext):
        fake_gettext.side_effect = lambda text: text + ' TRANSLATED'

        self._assert_reg_field(
            {"gender": "optional"},
            {
                "name": "gender",
                "type": "select",
                "required": False,
                "label": "Gender TRANSLATED",
                "options": [
                    {"value": "", "name": "--", "default": True},
                    {"value": "m", "name": "Male TRANSLATED", "default": False},
                    {"value": "f", "name": "Female TRANSLATED", "default": False},
                    {"value": "o", "name": "Other/Prefer Not to Say TRANSLATED", "default": False},
                ],
            }
        )

    def test_register_form_year_of_birth(self):
        this_year = datetime.datetime.now(UTC).year
        year_options = (
            [
                {
                    "value": "",
                    "name": "--",
                    "default": True
                }
            ] + [
                {
                    "value": unicode(year),
                    "name": unicode(year),
                    "default": False
                }
                for year in range(this_year, this_year - 120, -1)
            ]
        )
        self._assert_reg_field(
            {"year_of_birth": "optional"},
            {
                "name": "year_of_birth",
                "type": "select",
                "required": False,
                "label": "Year of birth",
                "options": year_options,
            }
        )

    def test_register_form_profession_without_profession_options(self):
        self._assert_reg_field(
            {"profession": "required"},
            {
                "name": "profession",
                "type": "text",
                "required": True,
                "label": "Profession",
                "errorMessages": {
                    "required": "Enter your profession."
                }
            }
        )

    @with_site_configuration(configuration={"EXTRA_FIELD_OPTIONS": {"profession": ["Software Engineer", "Teacher", "Other"]}})
    def test_register_form_profession_with_profession_options(self):
        self._assert_reg_field(
            {"profession": "required"},
            {
                "name": "profession",
                "type": "select",
                "required": True,
                "label": "Profession",
                "options": self.PROFESSION_OPTIONS,
                "errorMessages": {
                    "required": "Select your profession."
                },
            }
        )

    def test_register_form_specialty_without_specialty_options(self):
        self._assert_reg_field(
            {"specialty": "required"},
            {
                "name": "specialty",
                "type": "text",
                "required": True,
                "label": "Specialty",
                "errorMessages": {
                    "required": "Enter your specialty."
                }
            }
        )

    @with_site_configuration(configuration={"EXTRA_FIELD_OPTIONS": {"specialty": ["Aerospace", "Early Education", "N/A"]}})
    def test_register_form_specialty_with_specialty_options(self):
        self._assert_reg_field(
            {"specialty": "required"},
            {
                "name": "specialty",
                "type": "select",
                "required": True,
                "label": "Specialty",
                "options": self.SPECIALTY_OPTIONS,
                "errorMessages": {
                    "required": "Select your specialty."
                },
            }
        )

    def test_registration_form_mailing_address(self):
        self._assert_reg_field(
            {"mailing_address": "optional"},
            {
                "name": "mailing_address",
                "type": "textarea",
                "required": False,
                "label": "Mailing address",
                "errorMessages": {
                    "required": "Enter your mailing address."
                }
            }
        )

    def test_registration_form_goals(self):
        self._assert_reg_field(
            {"goals": "optional"},
            {
                "name": "goals",
                "type": "textarea",
                "required": False,
                "label": u"Tell us why you're interested in {platform_name}".format(
                    platform_name=settings.PLATFORM_NAME
                ),
                "errorMessages": {
                    "required": "Tell us your goals."
                }
            }
        )

    def test_registration_form_city(self):
        self._assert_reg_field(
            {"city": "optional"},
            {
                "name": "city",
                "type": "text",
                "required": False,
                "label": "City",
                "errorMessages": {
                    "required": "Enter your city."
                }
            }
        )

    def test_registration_form_state(self):
        self._assert_reg_field(
            {"state": "optional"},
            {
                "name": "state",
                "type": "text",
                "required": False,
                "label": "State/Province/Region",
            }
        )

    def test_registration_form_country(self):
        country_options = (
            [
                {
                    "name": "--",
                    "value": "",
                    "default": True
                }
            ] + [
                {
                    "value": country_code,
                    "name": unicode(country_name),
                    "default": False
                }
                for country_code, country_name in SORTED_COUNTRIES
            ]
        )
        self._assert_reg_field(
            {"country": "required"},
            {
                "label": "Country or Region of Residence",
                "name": "country",
                "type": "select",
                "instructions": "The country or region where you live.",
                "required": True,
                "options": country_options,
                "errorMessages": {
                    "required": "Select your country or region of residence."
                },
            }
        )

    def test_registration_form_confirm_email(self):
        self._assert_reg_field(
            {"confirm_email": "required"},
            {
                "name": "confirm_email",
                "type": "text",
                "required": True,
                "label": "Confirm Email",
                "errorMessages": {
                    "required": "The email addresses do not match.",
                }
            }
        )

    @override_settings(
        MKTG_URLS={"ROOT": "https://www.test.com/", "HONOR": "honor"},
    )
    @mock.patch.dict(settings.FEATURES, {"ENABLE_MKTG_SITE": True})
    def test_registration_honor_code_mktg_site_enabled(self):
        link_template = "<a href='https://www.test.com/honor' target='_blank'>{link_label}</a>"
        link_template2 = "<a href='#' target='_blank'>{link_label}</a>"
        link_label = "Terms of Service and Honor Code"
        link_label2 = "Privacy Policy"
        self._assert_reg_field(
            {"honor_code": "required"},
            {
                "label": (u"By creating an account with {platform_name}, you agree {spacing}"
                          u"to abide by our {platform_name} {spacing}"
                          u"{link_label} {spacing}"
                          u"and agree to our {link_label2}.").format(
                    platform_name=settings.PLATFORM_NAME,
                    link_label=link_template.format(link_label=link_label),
                    link_label2=link_template2.format(link_label=link_label2),
                    spacing=' ' * 18
                ),
                "name": "honor_code",
                "defaultValue": False,
                "type": "plaintext",
                "required": True,
                "errorMessages": {
                    "required": u"You must agree to the {platform_name} {link_label}".format(
                        platform_name=settings.PLATFORM_NAME,
                        link_label=link_label
                    )
                }
            }
        )

    @override_settings(MKTG_URLS_LINK_MAP={"HONOR": "honor"})
    @mock.patch.dict(settings.FEATURES, {"ENABLE_MKTG_SITE": False})
    def test_registration_honor_code_mktg_site_disabled(self):
        link_template = "<a href='/privacy' target='_blank'>{link_label}</a>"
        link_label = "Terms of Service and Honor Code"
        link_label2 = "Privacy Policy"
        self._assert_reg_field(
            {"honor_code": "required"},
            {
                "label": (u"By creating an account with {platform_name}, you agree {spacing}"
                          u"to abide by our {platform_name} {spacing}"
                          u"{link_label} {spacing}"
                          u"and agree to our {link_label2}.").format(
                    platform_name=settings.PLATFORM_NAME,
                    link_label=self.link_template.format(link_label=link_label),
                    link_label2=link_template.format(link_label=link_label2),
                    spacing=' ' * 18
                ),
                "name": "honor_code",
                "defaultValue": False,
                "type": "plaintext",
                "required": True,
                "errorMessages": {
                    "required": u"You must agree to the {platform_name} {link_label}".format(
                        platform_name=settings.PLATFORM_NAME,
                        link_label=link_label
                    )
                }
            }
        )

    @override_settings(MKTG_URLS={
        "ROOT": "https://www.test.com/",
        "HONOR": "honor",
        "TOS": "tos",
    })
    @mock.patch.dict(settings.FEATURES, {"ENABLE_MKTG_SITE": True})
    def test_registration_separate_terms_of_service_mktg_site_enabled(self):
        # Honor code field should say ONLY honor code,
        # not "terms of service and honor code"
        link_label = 'Honor Code'
        link_template = "<a href='https://www.test.com/honor' target='_blank'>{link_label}</a>"
        self._assert_reg_field(
            {"honor_code": "required", "terms_of_service": "required"},
            {
                "label": u"I agree to the {platform_name} {link_label}".format(
                    platform_name=settings.PLATFORM_NAME,
                    link_label=link_template.format(link_label=link_label)
                ),
                "name": "honor_code",
                "defaultValue": False,
                "type": "checkbox",
                "required": True,
                "errorMessages": {
                    "required": u"You must agree to the {platform_name} {link_label}".format(
                        platform_name=settings.PLATFORM_NAME,
                        link_label=link_label
                    )
                }
            }
        )

        # Terms of service field should also be present
        link_label = "Terms of Service"
        link_template = "<a href='https://www.test.com/tos' target='_blank'>{link_label}</a>"
        self._assert_reg_field(
            {"honor_code": "required", "terms_of_service": "required"},
            {
                "label": u"I agree to the {platform_name} {link_label}".format(
                    platform_name=settings.PLATFORM_NAME,
                    link_label=link_template.format(link_label=link_label)
                ),
                "name": "terms_of_service",
                "defaultValue": False,
                "type": "checkbox",
                "required": True,
                "errorMessages": {
                    "required": u"You must agree to the {platform_name} {link_label}".format(
                        platform_name=settings.PLATFORM_NAME,
                        link_label=link_label
                    )
                }
            }
        )

    @override_settings(MKTG_URLS_LINK_MAP={"HONOR": "honor", "TOS": "tos"})
    @mock.patch.dict(settings.FEATURES, {"ENABLE_MKTG_SITE": False})
    def test_registration_separate_terms_of_service_mktg_site_disabled(self):
        # Honor code field should say ONLY honor code,
        # not "terms of service and honor code"
        link_label = 'Honor Code'
        self._assert_reg_field(
            {"honor_code": "required", "terms_of_service": "required"},
            {
                "label": u"I agree to the {platform_name} {link_label}".format(
                    platform_name=settings.PLATFORM_NAME,
                    link_label=self.link_template.format(link_label=link_label)
                ),
                "name": "honor_code",
                "defaultValue": False,
                "type": "checkbox",
                "required": True,
                "errorMessages": {
                    "required": u"You must agree to the {platform_name} Honor Code".format(
                        platform_name=settings.PLATFORM_NAME
                    )
                }
            }
        )

        link_label = 'Terms of Service'
        # Terms of service field should also be present
        link_template = "<a href='/tos' target='_blank'>{link_label}</a>"
        self._assert_reg_field(
            {"honor_code": "required", "terms_of_service": "required"},
            {
                "label": u"I agree to the {platform_name} {link_label}".format(
                    platform_name=settings.PLATFORM_NAME,
                    link_label=link_template.format(link_label=link_label)
                ),
                "name": "terms_of_service",
                "defaultValue": False,
                "type": "checkbox",
                "required": True,
                "errorMessages": {
                    "required": u"You must agree to the {platform_name} Terms of Service".format(  # pylint: disable=line-too-long
                        platform_name=settings.PLATFORM_NAME
                    )
                }
            }
        )

    @override_settings(
        REGISTRATION_EXTRA_FIELDS={
            "level_of_education": "optional",
            "gender": "optional",
            "year_of_birth": "optional",
            "mailing_address": "optional",
            "goals": "optional",
            "city": "optional",
            "state": "optional",
            "country": "required",
            "honor_code": "required",
            "confirm_email": "required",
        },
        REGISTRATION_EXTENSION_FORM='openedx.core.djangoapps.user_api.tests.test_helpers.TestCaseForm',
    )
    def test_field_order(self):
        response = self.client.get(self.url)
        self.assertHttpOK(response)

        # Verify that all fields render in the correct order
        form_desc = json.loads(response.content)
        field_names = [field["name"] for field in form_desc["fields"]]
        self.assertEqual(field_names, [
            "email",
            "name",
            "username",
            "password",
            "favorite_movie",
            "favorite_editor",
            "confirm_email",
            "city",
            "state",
            "country",
            "gender",
            "year_of_birth",
            "level_of_education",
            "mailing_address",
            "goals",
            "honor_code",
        ])

    @override_settings(
        REGISTRATION_EXTRA_FIELDS={
            "level_of_education": "optional",
            "gender": "optional",
            "year_of_birth": "optional",
            "mailing_address": "optional",
            "goals": "optional",
            "city": "optional",
            "state": "optional",
            "country": "required",
            "honor_code": "required",
            "confirm_email": "required",
        },
        REGISTRATION_FIELD_ORDER=[
            "name",
            "username",
            "email",
            "confirm_email",
            "password",
            "first_name",
            "last_name",
            "city",
            "state",
            "country",
            "gender",
            "year_of_birth",
            "level_of_education",
            "company",
            "title",
            "job_title",
            "mailing_address",
            "goals",
            "honor_code",
            "terms_of_service",
            "specialty",
            "profession",
        ],
    )
    def test_field_order_override(self):
        response = self.client.get(self.url)
        self.assertHttpOK(response)

        # Verify that all fields render in the correct order
        form_desc = json.loads(response.content)
        field_names = [field["name"] for field in form_desc["fields"]]
        self.assertEqual(field_names, [
            "name",
            "username",
            "email",
            "confirm_email",
            "password",
            "city",
            "state",
            "country",
            "gender",
            "year_of_birth",
            "level_of_education",
            "mailing_address",
            "goals",
            "honor_code",
        ])

    @override_settings(
        REGISTRATION_EXTRA_FIELDS={
            "level_of_education": "optional",
            "gender": "optional",
            "year_of_birth": "optional",
            "mailing_address": "optional",
            "goals": "optional",
            "city": "optional",
            "state": "optional",
            "country": "required",
            "honor_code": "required",
            "confirm_email": "required",
        },
        REGISTRATION_EXTENSION_FORM='openedx.core.djangoapps.user_api.tests.test_helpers.TestCaseForm',
        REGISTRATION_FIELD_ORDER=[
            "name",
            "confirm_email",
            "password",
            "first_name",
            "last_name",
            "gender",
            "year_of_birth",
            "level_of_education",
            "company",
            "title",
            "mailing_address",
            "goals",
            "honor_code",
            "terms_of_service",
        ],
    )
    def test_field_order_invalid_override(self):
        response = self.client.get(self.url)
        self.assertHttpOK(response)

        # Verify that all fields render in the correct order
        form_desc = json.loads(response.content)
        field_names = [field["name"] for field in form_desc["fields"]]
        self.assertEqual(field_names, [
            "email",
            "name",
            "username",
            "password",
            "favorite_movie",
            "favorite_editor",
            "confirm_email",
            "city",
            "state",
            "country",
            "gender",
            "year_of_birth",
            "level_of_education",
            "mailing_address",
            "goals",
            "honor_code",
        ])

    def test_register(self):
        # Create a new registration
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertHttpOK(response)
        self.assertIn(settings.EDXMKTG_LOGGED_IN_COOKIE_NAME, self.client.cookies)
        self.assertIn(settings.EDXMKTG_USER_INFO_COOKIE_NAME, self.client.cookies)

        user = User.objects.get(username=self.USERNAME)
        request = RequestFactory().get('/url')
        request.user = user
        account_settings = get_account_settings(request)[0]

        self.assertEqual(self.USERNAME, account_settings["username"])
        self.assertEqual(self.EMAIL, account_settings["email"])
        self.assertFalse(account_settings["is_active"])
        self.assertEqual(self.NAME, account_settings["name"])

        # Verify that we've been logged in
        # by trying to access a page that requires authentication
        response = self.client.get(reverse("dashboard"))
        self.assertHttpOK(response)

    @override_settings(REGISTRATION_EXTRA_FIELDS={
        "level_of_education": "optional",
        "gender": "optional",
        "year_of_birth": "optional",
        "mailing_address": "optional",
        "goals": "optional",
        "country": "required",
    })
    def test_register_with_profile_info(self):
        # Register, providing lots of demographic info
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "level_of_education": self.EDUCATION,
            "mailing_address": self.ADDRESS,
            "year_of_birth": self.YEAR_OF_BIRTH,
            "goals": self.GOALS,
            "country": self.COUNTRY,
            "honor_code": "true",
        })
        self.assertHttpOK(response)

        # Verify the user's account
        user = User.objects.get(username=self.USERNAME)
        request = RequestFactory().get('/url')
        request.user = user
        account_settings = get_account_settings(request)[0]

        self.assertEqual(account_settings["level_of_education"], self.EDUCATION)
        self.assertEqual(account_settings["mailing_address"], self.ADDRESS)
        self.assertEqual(account_settings["year_of_birth"], int(self.YEAR_OF_BIRTH))
        self.assertEqual(account_settings["goals"], self.GOALS)
        self.assertEqual(account_settings["country"], self.COUNTRY)

    @override_settings(REGISTRATION_EXTENSION_FORM='openedx.core.djangoapps.user_api.tests.test_helpers.TestCaseForm')
    @mock.patch('openedx.core.djangoapps.user_api.tests.test_helpers.TestCaseForm.DUMMY_STORAGE', new_callable=dict)
    @mock.patch(
        'openedx.core.djangoapps.user_api.tests.test_helpers.DummyRegistrationExtensionModel',
    )
    def test_with_extended_form(self, dummy_model, storage_dict):
        dummy_model_instance = mock.Mock()
        dummy_model.return_value = dummy_model_instance
        # Create a new registration
        self.assertEqual(storage_dict, {})
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
            "favorite_movie": "Inception",
            "favorite_editor": "cat",
        })
        self.assertHttpOK(response)
        self.assertIn(settings.EDXMKTG_LOGGED_IN_COOKIE_NAME, self.client.cookies)
        self.assertIn(settings.EDXMKTG_USER_INFO_COOKIE_NAME, self.client.cookies)

        user = User.objects.get(username=self.USERNAME)
        request = RequestFactory().get('/url')
        request.user = user
        account_settings = get_account_settings(request)[0]

        self.assertEqual(self.USERNAME, account_settings["username"])
        self.assertEqual(self.EMAIL, account_settings["email"])
        self.assertFalse(account_settings["is_active"])
        self.assertEqual(self.NAME, account_settings["name"])

        self.assertEqual(storage_dict, {'favorite_movie': "Inception", "favorite_editor": "cat"})
        self.assertEqual(dummy_model_instance.user, user)

        # Verify that we've been logged in
        # by trying to access a page that requires authentication
        response = self.client.get(reverse("dashboard"))
        self.assertHttpOK(response)

    def test_activation_email(self):
        # Register, which should trigger an activation email
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertHttpOK(response)

        # Verify that the activation email was sent
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.to, [self.EMAIL])
        self.assertEqual(
            sent_email.subject,
            u"Action Required: Activate your {platform} account".format(platform=settings.PLATFORM_NAME)
        )
        self.assertIn(
            u"high-quality {platform} courses".format(platform=settings.PLATFORM_NAME),
            sent_email.body
        )

    @ddt.data(
        {"email": ""},
        {"email": "invalid"},
        {"name": ""},
        {"username": ""},
        {"username": "a"},
        {"password": ""},
    )
    def test_register_invalid_input(self, invalid_fields):
        # Initially, the field values are all valid
        data = {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
        }

        # Override the valid fields, making the input invalid
        data.update(invalid_fields)

        # Attempt to create the account, expecting an error response
        response = self.client.post(self.url, data)
        self.assertHttpBadRequest(response)

    @override_settings(REGISTRATION_EXTRA_FIELDS={"country": "required"})
    @ddt.data("email", "name", "username", "password", "country")
    def test_register_missing_required_field(self, missing_field):
        data = {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "country": self.COUNTRY,
        }

        del data[missing_field]

        # Send a request missing a field
        response = self.client.post(self.url, data)
        self.assertHttpBadRequest(response)

    def test_register_duplicate_email(self):
        # Register the first user
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertHttpOK(response)

        # Try to create a second user with the same email address
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": "Someone Else",
            "username": "someone_else",
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertEqual(response.status_code, 409)
        response_json = json.loads(response.content)
        self.assertEqual(
            response_json,
            {
                "email": [{
                    "user_message": (
                        "It looks like {} belongs to an existing account. "
                        "Try again with a different email address."
                    ).format(
                        self.EMAIL
                    )
                }]
            }
        )

    def test_register_duplicate_username(self):
        # Register the first user
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertHttpOK(response)

        # Try to create a second user with the same username
        response = self.client.post(self.url, {
            "email": "someone+else@example.com",
            "name": "Someone Else",
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertEqual(response.status_code, 409)
        response_json = json.loads(response.content)
        self.assertEqual(
            response_json,
            {
                "username": [{
                    "user_message": (
                        "It looks like {} belongs to an existing account. "
                        "Try again with a different username."
                    ).format(
                        self.USERNAME
                    )
                }]
            }
        )

    def test_register_duplicate_username_and_email(self):
        # Register the first user
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertHttpOK(response)

        # Try to create a second user with the same username
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": "Someone Else",
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertEqual(response.status_code, 409)
        response_json = json.loads(response.content)
        self.assertEqual(
            response_json,
            {
                "username": [{
                    "user_message": (
                        "It looks like {} belongs to an existing account. "
                        "Try again with a different username."
                    ).format(
                        self.USERNAME
                    )
                }],
                "email": [{
                    "user_message": (
                        "It looks like {} belongs to an existing account. "
                        "Try again with a different email address."
                    ).format(
                        self.EMAIL
                    )
                }]
            }
        )

    @override_settings(REGISTRATION_EXTRA_FIELDS={"honor_code": "hidden", "terms_of_service": "hidden"})
    def test_register_hidden_honor_code_and_terms_of_service(self):
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
        })
        self.assertHttpOK(response)

    def test_missing_fields(self):
        response = self.client.post(
            self.url,
            {
                "email": self.EMAIL,
                "name": self.NAME,
                "honor_code": "true",
            }
        )
        self.assertEqual(response.status_code, 400)
        response_json = json.loads(response.content)
        self.assertEqual(
            response_json,
            {
                u"username": [{u"user_message": USERNAME_BAD_LENGTH_MSG}],
                u"password": [{u"user_message": u"A valid password is required"}],
            }
        )

    def test_country_overrides(self):
        """Test that overridden countries are available in country list."""
        # Retrieve the registration form description
        with override_settings(REGISTRATION_EXTRA_FIELDS={"country": "required"}):
            response = self.client.get(self.url)
            self.assertHttpOK(response)

        self.assertContains(response, 'Kosovo')

    def test_create_account_not_allowed(self):
        """
        Test case to check user creation is forbidden when ALLOW_PUBLIC_ACCOUNT_CREATION feature flag is turned off
        """
        def _side_effect_for_get_value(value, default=None):
            """
            returns a side_effect with given return value for a given value
            """
            if value == 'ALLOW_PUBLIC_ACCOUNT_CREATION':
                return False
            else:
                return get_value(value, default)

        with mock.patch('openedx.core.djangoapps.site_configuration.helpers.get_value') as mock_get_value:
            mock_get_value.side_effect = _side_effect_for_get_value
            response = self.client.post(self.url, {"email": self.EMAIL, "username": self.USERNAME})
            self.assertEqual(response.status_code, 403)

    def _assert_fields_match(self, actual_field, expected_field):
        self.assertIsNot(
            actual_field, None,
            msg="Could not find field {name}".format(name=expected_field["name"])
        )

        for key, value in expected_field.iteritems():
            self.assertEqual(
                actual_field[key], expected_field[key],
                msg=u"Expected {expected} for {key} but got {actual} instead".format(
                    key=key,
                    actual=actual_field[key],
                    expected=expected_field[key]
                )
            )

    def _populate_always_present_fields(self, field):
        defaults = [
            ("label", ""),
            ("instructions", ""),
            ("placeholder", ""),
            ("defaultValue", ""),
            ("restrictions", {}),
            ("errorMessages", {}),
        ]
        field.update({
            key: value
            for key, value in defaults if key not in field
        })

    def _assert_reg_field(self, extra_fields_setting, expected_field):
        """Retrieve the registration form description from the server and
        verify that it contains the expected field.

        Args:
            extra_fields_setting (dict): Override the Django setting controlling
                which extra fields are displayed in the form.

            expected_field (dict): The field definition we expect to find in the form.

        Raises:
            AssertionError

        """
        # Add in fields that are always present
        self._populate_always_present_fields(expected_field)

        # Retrieve the registration form description
        with override_settings(REGISTRATION_EXTRA_FIELDS=extra_fields_setting):
            response = self.client.get(self.url)
            self.assertHttpOK(response)

        # Verify that the form description matches what we'd expect
        form_desc = json.loads(response.content)

        actual_field = None
        for field in form_desc["fields"]:
            if field["name"] == expected_field["name"]:
                actual_field = field
                break

        self._assert_fields_match(actual_field, expected_field)

    def _assert_password_field_hidden(self, field_settings):
        self._assert_reg_field(field_settings, {
            "name": "password",
            "type": "hidden",
            "required": False
        })

    def _assert_social_auth_provider_present(self, field_settings, backend):
        self._assert_reg_field(field_settings, {
            "name": "social_auth_provider",
            "type": "hidden",
            "required": False,
            "defaultValue": backend.name
        })


@httpretty.activate
@ddt.ddt
class ThirdPartyRegistrationTestMixin(ThirdPartyOAuthTestMixin, CacheIsolationTestCase):
    """
    Tests for the User API registration endpoint with 3rd party authentication.
    """
    CREATE_USER = False

    ENABLED_CACHES = ['default']

    __test__ = False

    def setUp(self):
        super(ThirdPartyRegistrationTestMixin, self).setUp()
        self.url = reverse('user_api_registration')

    def tearDown(self):
        super(ThirdPartyRegistrationTestMixin, self).tearDown()
        Partial.objects.all().delete()

    def data(self, user=None):
        """Returns the request data for the endpoint."""
        return {
            "provider": self.BACKEND,
            "access_token": self.access_token,
            "client_id": self.client_id,
            "honor_code": "true",
            "country": "US",
            "username": user.username if user else "test_username",
            "name": user.first_name if user else "test name",
            "email": user.email if user else "test@test.com"
        }

    def _assert_existing_user_error(self, response):
        """Assert that the given response was an error with the given status_code and error code."""
        self.assertEqual(response.status_code, 409)
        errors = json.loads(response.content)
        for conflict_attribute in ["username", "email"]:
            self.assertIn(conflict_attribute, errors)
            self.assertIn("belongs to an existing account", errors[conflict_attribute][0]["user_message"])

    def _assert_access_token_error(self, response, expected_error_message):
        """Assert that the given response was an error for the access_token field with the given error message."""
        self.assertEqual(response.status_code, 400)
        response_json = json.loads(response.content)
        self.assertEqual(
            response_json,
            {"access_token": [{"user_message": expected_error_message}]}
        )

    def _assert_third_party_session_expired_error(self, response, expected_error_message):
        """Assert that given response is an error due to third party session expiry"""
        self.assertEqual(response.status_code, 400)
        response_json = json.loads(response.content)
        self.assertEqual(
            response_json,
            {"session_expired": [{"user_message": expected_error_message}]}
        )

    def _verify_user_existence(self, user_exists, social_link_exists, user_is_active=None, username=None):
        """Verifies whether the user object exists."""
        users = User.objects.filter(username=(username if username else "test_username"))
        self.assertEquals(users.exists(), user_exists)
        if user_exists:
            self.assertEquals(users[0].is_active, user_is_active)
            self.assertEqual(
                UserSocialAuth.objects.filter(user=users[0], provider=self.BACKEND).exists(),
                social_link_exists
            )
        else:
            self.assertEquals(UserSocialAuth.objects.count(), 0)

    def test_success(self):
        self._verify_user_existence(user_exists=False, social_link_exists=False)

        self._setup_provider_response(success=True)
        response = self.client.post(self.url, self.data())
        self.assertEqual(response.status_code, 200)

        self._verify_user_existence(user_exists=True, social_link_exists=True, user_is_active=False)

    def test_unlinked_active_user(self):
        user = UserFactory()
        response = self.client.post(self.url, self.data(user))
        self._assert_existing_user_error(response)
        self._verify_user_existence(
            user_exists=True, social_link_exists=False, user_is_active=True, username=user.username
        )

    def test_unlinked_inactive_user(self):
        user = UserFactory(is_active=False)
        response = self.client.post(self.url, self.data(user))
        self._assert_existing_user_error(response)
        self._verify_user_existence(
            user_exists=True, social_link_exists=False, user_is_active=False, username=user.username
        )

    def test_user_already_registered(self):
        self._setup_provider_response(success=True)
        user = UserFactory()
        UserSocialAuth.objects.create(user=user, provider=self.BACKEND, uid=self.social_uid)
        response = self.client.post(self.url, self.data(user))
        self._assert_existing_user_error(response)
        self._verify_user_existence(
            user_exists=True, social_link_exists=True, user_is_active=True, username=user.username
        )

    def test_social_user_conflict(self):
        self._setup_provider_response(success=True)
        user = UserFactory()
        UserSocialAuth.objects.create(user=user, provider=self.BACKEND, uid=self.social_uid)
        response = self.client.post(self.url, self.data())
        self._assert_access_token_error(response, "The provided access_token is already associated with another user.")
        self._verify_user_existence(
            user_exists=True, social_link_exists=True, user_is_active=True, username=user.username
        )

    def test_invalid_token(self):
        self._setup_provider_response(success=False)
        response = self.client.post(self.url, self.data())
        self._assert_access_token_error(response, "The provided access_token is not valid.")
        self._verify_user_existence(user_exists=False, social_link_exists=False)

    def test_missing_token(self):
        data = self.data()
        data.pop("access_token")
        response = self.client.post(self.url, data)
        self._assert_access_token_error(
            response,
            "An access_token is required when passing value ({}) for provider.".format(self.BACKEND)
        )
        self._verify_user_existence(user_exists=False, social_link_exists=False)

    def test_expired_pipeline(self):

        """
        Test that there is an error and account is not created
        when request is made for account creation using third (Google, Facebook etc) party with pipeline
        getting expired using browser (not mobile application).

        NOTE: We are NOT using actual pipeline here so pipeline is always expired in this environment.
        we don't have to explicitly expire pipeline.

        """

        data = self.data()
        # provider is sent along request when request is made from mobile application
        data.pop("provider")
        # to identify that request is made using browser
        data.update({"social_auth_provider": "Google"})
        response = self.client.post(self.url, data)
        self._assert_third_party_session_expired_error(
            response,
            u"Registration using {provider} has timed out.".format(provider="Google")
        )
        self._verify_user_existence(user_exists=False, social_link_exists=False)


@skipUnless(settings.FEATURES.get("ENABLE_THIRD_PARTY_AUTH"), "third party auth not enabled")
class TestFacebookRegistrationView(
    ThirdPartyRegistrationTestMixin, ThirdPartyOAuthTestMixinFacebook, TransactionTestCase
):
    """Tests the User API registration endpoint with Facebook authentication."""
    __test__ = True

    def test_social_auth_exception(self):
        """
        According to the do_auth method in social_core.backends.facebook.py,
        the Facebook API sometimes responds back a JSON with just False as value.
        """
        self._setup_provider_response_with_body(200, json.dumps("false"))
        response = self.client.post(self.url, self.data())
        self._assert_access_token_error(response, "The provided access_token is not valid.")
        self._verify_user_existence(user_exists=False, social_link_exists=False)


@skipUnless(settings.FEATURES.get("ENABLE_THIRD_PARTY_AUTH"), "third party auth not enabled")
class TestGoogleRegistrationView(
    ThirdPartyRegistrationTestMixin, ThirdPartyOAuthTestMixinGoogle, TransactionTestCase
):
    """Tests the User API registration endpoint with Google authentication."""
    __test__ = True


@ddt.ddt
@skip_unless_lms
class UpdateEmailOptInTestCase(UserAPITestCase, SharedModuleStoreTestCase):
    """Tests the UpdateEmailOptInPreference view. """

    USERNAME = "steve"
    EMAIL = "steve@isawesome.com"
    PASSWORD = "steveopolis"

    @classmethod
    def setUpClass(cls):
        super(UpdateEmailOptInTestCase, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.url = reverse("preferences_email_opt_in")

    def setUp(self):
        """ Create a course and user, then log in. """
        super(UpdateEmailOptInTestCase, self).setUp()
        self.user = UserFactory.create(username=self.USERNAME, email=self.EMAIL, password=self.PASSWORD)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

    @ddt.data(
        (u"True", u"True"),
        (u"true", u"True"),
        (u"TrUe", u"True"),
        (u"Banana", u"False"),
        (u"strawberries", u"False"),
        (u"False", u"False"),
    )
    @ddt.unpack
    def test_update_email_opt_in(self, opt, result):
        """Tests the email opt in preference"""
        # Register, which should trigger an activation email
        response = self.client.post(self.url, {
            "course_id": unicode(self.course.id),
            "email_opt_in": opt
        })
        self.assertHttpOK(response)
        preference = UserOrgTag.objects.get(
            user=self.user, org=self.course.id.org, key="email-optin"
        )
        self.assertEquals(preference.value, result)

    @ddt.data(
        (True, False),
        (False, True),
        (False, False)
    )
    @ddt.unpack
    def test_update_email_opt_in_wrong_params(self, use_course_id, use_opt_in):
        """Tests the email opt in preference"""
        params = {}
        if use_course_id:
            params["course_id"] = unicode(self.course.id)
        if use_opt_in:
            params["email_opt_in"] = u"True"

        response = self.client.post(self.url, params)
        self.assertHttpBadRequest(response)

    def test_update_email_opt_in_inactive_user(self):
        """Test that an inactive user can still update their email optin preference."""
        self.user.is_active = False
        self.user.save()
        # Register, which should trigger an activation email
        response = self.client.post(self.url, {
            "course_id": unicode(self.course.id),
            "email_opt_in": u"True"
        })
        self.assertHttpOK(response)
        preference = UserOrgTag.objects.get(
            user=self.user, org=self.course.id.org, key="email-optin"
        )
        self.assertEquals(preference.value, u"True")

    def test_update_email_opt_in_anonymous_user(self):
        """
        Test that an anonymous user gets 403 response when
        updating email optin preference.
        """
        self.client.logout()
        response = self.client.post(self.url, {
            "course_id": unicode(self.course.id),
            "email_opt_in": u"True"
        })
        self.assertEqual(response.status_code, 403)

    def test_update_email_opt_with_invalid_course_key(self):
        """
        Test that with invalid key it returns bad request
        and not update their email optin preference.
        """
        response = self.client.post(self.url, {
            "course_id": 'invalid',
            "email_opt_in": u"True"
        })
        self.assertHttpBadRequest(response)
        with self.assertRaises(UserOrgTag.DoesNotExist):
            UserOrgTag.objects.get(user=self.user, org=self.course.id.org, key="email-optin")


@ddt.ddt
class CountryTimeZoneListViewTest(UserApiTestCase):
    """
    Test cases covering the list viewing behavior for country time zones
    """
    ALL_TIME_ZONES_URI = "/user_api/v1/preferences/time_zones/"
    COUNTRY_TIME_ZONES_URI = "/user_api/v1/preferences/time_zones/?country_code=cA"

    @ddt.data(ALL_TIME_ZONES_URI, COUNTRY_TIME_ZONES_URI)
    def test_options(self, country_uri):
        """ Verify that following options are allowed """
        self.assertAllowedMethods(country_uri, ['OPTIONS', 'GET', 'HEAD'])

    @ddt.data(ALL_TIME_ZONES_URI, COUNTRY_TIME_ZONES_URI)
    def test_methods_not_allowed(self, country_uri):
        """ Verify that put, patch, and delete are not allowed """
        unallowed_methods = ['put', 'patch', 'delete']
        for unallowed_method in unallowed_methods:
            self.assertHttpMethodNotAllowed(self.request_with_auth(unallowed_method, country_uri))

    def _assert_time_zone_is_valid(self, time_zone_info):
        """ Asserts that the time zone is a valid pytz time zone """
        time_zone_name = time_zone_info['time_zone']
        self.assertIn(time_zone_name, common_timezones_set)
        self.assertEqual(time_zone_info['description'], get_display_time_zone(time_zone_name))

    # The time zones count may need to change each time we upgrade pytz
    @ddt.data((ALL_TIME_ZONES_URI, 439),
              (COUNTRY_TIME_ZONES_URI, 28))
    @ddt.unpack
    def test_get_basic(self, country_uri, expected_count):
        """ Verify that correct time zone info is returned """
        results = self.get_json(country_uri)
        self.assertEqual(len(results), expected_count)
        for time_zone_info in results:
            self._assert_time_zone_is_valid(time_zone_info)
