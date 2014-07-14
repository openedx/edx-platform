import base64

from django.test import TestCase
from django.test.utils import override_settings
import json
import re
from student.tests.factories import UserFactory
from unittest import SkipTest
from user_api.models import UserPreference
from user_api.tests.factories import UserPreferenceFactory
from django_comment_common import models
from opaque_keys.edx.locations import SlashSeparatedCourseKey


TEST_API_KEY = "test_api_key"
USER_LIST_URI = "/user_api/v1/users/"
USER_PREFERENCE_LIST_URI = "/user_api/v1/user_prefs/"
ROLE_LIST_URI = "/user_api/v1/forum_roles/Moderator/users/"


@override_settings(EDX_API_KEY=TEST_API_KEY)
class ApiTestCase(TestCase):

    LIST_URI = USER_LIST_URI

    def basic_auth(self, username, password):
        return {'HTTP_AUTHORIZATION': 'Basic ' + base64.b64encode('%s:%s' % (username, password))}

    def request_with_auth(self, method, *args, **kwargs):
        """Issue a get request to the given URI with the API key header"""
        return getattr(self.client, method)(*args, HTTP_X_EDX_API_KEY=TEST_API_KEY, **kwargs)

    def get_json(self, *args, **kwargs):
        """Make a request with the given args and return the parsed JSON repsonse"""
        resp = self.request_with_auth("get", *args, **kwargs)
        self.assertHttpOK(resp)
        self.assertTrue(resp["Content-Type"].startswith("application/json"))
        return json.loads(resp.content)

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
            if (pref["user"]["id"] == target_pref.user.id and pref["key"] == target_pref.key):
                return pref["url"]
        self.fail()

    def assertAllowedMethods(self, uri, expected_methods):
        """Assert that the allowed methods for the given URI match the expected list"""
        resp = self.request_with_auth("options", uri)
        self.assertHttpOK(resp)
        allow_header = resp.get("Allow")
        self.assertIsNotNone(allow_header)
        allowed_methods = re.split('[^A-Z]+', allow_header)
        self.assertItemsEqual(allowed_methods, expected_methods)

    def assertSelfReferential(self, obj):
        """Assert that accessing the "url" entry in the given object returns the same object"""
        copy = self.get_json(obj["url"])
        self.assertEqual(obj, copy)

    def assertUserIsValid(self, user):
        """Assert that the given user result is valid"""
        self.assertItemsEqual(user.keys(), ["email", "id", "name", "username", "preferences", "url"])
        self.assertItemsEqual(
            user["preferences"].items(),
            [(pref.key, pref.value) for pref in self.prefs if pref.user.id == user["id"]]
        )
        self.assertSelfReferential(user)

    def assertPrefIsValid(self, pref):
        self.assertItemsEqual(pref.keys(), ["user", "key", "value", "url"])
        self.assertSelfReferential(pref)
        self.assertUserIsValid(pref["user"])

    def assertHttpOK(self, response):
        """Assert that the given response has the status code 200"""
        self.assertEqual(response.status_code, 200)

    def assertHttpForbidden(self, response):
        """Assert that the given response has the status code 403"""
        self.assertEqual(response.status_code, 403)

    def assertHttpBadRequest(self, response):
        """Assert that the given response has the status code 400"""
        self.assertEqual(response.status_code, 400)

    def assertHttpMethodNotAllowed(self, response):
        """Assert that the given response has the status code 405"""
        self.assertEqual(response.status_code, 405)


class EmptyUserTestCase(ApiTestCase):
    def test_get_list_empty(self):
        result = self.get_json(self.LIST_URI)
        self.assertEqual(result["count"], 0)
        self.assertIsNone(result["next"])
        self.assertIsNone(result["previous"])
        self.assertEqual(result["results"], [])


class EmptyRoleTestCase(ApiTestCase):
    """Test that the endpoint supports empty result sets"""
    course_id = SlashSeparatedCourseKey.from_deprecated_string("org/course/run")
    LIST_URI = ROLE_LIST_URI + "?course_id=" + course_id.to_deprecated_string()

    def test_get_list_empty(self):
        """Test that the endpoint properly returns empty result sets"""
        result = self.get_json(self.LIST_URI)
        self.assertEqual(result["count"], 0)
        self.assertIsNone(result["next"])
        self.assertIsNone(result["previous"])
        self.assertEqual(result["results"], [])


class UserApiTestCase(ApiTestCase):
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
    course_id = SlashSeparatedCourseKey.from_deprecated_string("org/course/run")
    LIST_URI = ROLE_LIST_URI + "?course_id=" + course_id.to_deprecated_string()

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
        raise SkipTest("Django 1.4's test client does not support patch")

    def test_delete_list_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.request_with_auth("delete", self.LIST_URI))

    def test_list_unauthorized(self):
        self.assertHttpForbidden(self.client.get(self.LIST_URI))

    @override_settings(DEBUG=True)
    @override_settings(EDX_API_KEY=None)
    def test_debug_auth(self):
        self.assertHttpOK(self.client.get(self.LIST_URI))

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
            "course_id": self.course_id.to_deprecated_string(),
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
        raise SkipTest("Django 1.4's test client does not support patch")

    def test_delete_list_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.request_with_auth("delete", self.LIST_URI))

    def test_list_unauthorized(self):
        self.assertHttpForbidden(self.client.get(self.LIST_URI))

    @override_settings(DEBUG=True)
    @override_settings(EDX_API_KEY=None)
    def test_debug_auth(self):
        self.assertHttpOK(self.client.get(self.LIST_URI))

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
        raise SkipTest("Django 1.4's test client does not support patch")

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


class UserPreferenceViewSetTest(UserApiTestCase):
    LIST_URI = USER_PREFERENCE_LIST_URI

    def setUp(self):
        super(UserPreferenceViewSetTest, self).setUp()
        self.detail_uri = self.get_uri_for_pref(self.prefs[0])

    # List view tests

    def test_options_list(self):
        self.assertAllowedMethods(self.LIST_URI, ["OPTIONS", "GET", "HEAD"])

    def test_put_list_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.request_with_auth("put", self.LIST_URI))

    def test_patch_list_not_allowed(self):
        raise SkipTest("Django 1.4's test client does not support patch")

    def test_delete_list_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.request_with_auth("delete", self.LIST_URI))

    def test_list_unauthorized(self):
        self.assertHttpForbidden(self.client.get(self.LIST_URI))

    @override_settings(DEBUG=True)
    @override_settings(EDX_API_KEY=None)
    def test_debug_auth(self):
        self.assertHttpOK(self.client.get(self.LIST_URI))

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
        raise SkipTest("Django 1.4's test client does not support patch")

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
    LIST_URI = "/user_api/v1/preferences/key0/users/"

    def test_options(self):
        self.assertAllowedMethods(self.LIST_URI, ["OPTIONS", "GET", "HEAD"])

    def test_put_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.request_with_auth("put", self.LIST_URI))

    def test_patch_not_allowed(self):
        raise SkipTest("Django 1.4's test client does not support patch")

    def test_delete_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.request_with_auth("delete", self.LIST_URI))

    def test_unauthorized(self):
        self.assertHttpForbidden(self.client.get(self.LIST_URI))

    @override_settings(DEBUG=True)
    @override_settings(EDX_API_KEY=None)
    def test_debug_auth(self):
        self.assertHttpOK(self.client.get(self.LIST_URI))

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
