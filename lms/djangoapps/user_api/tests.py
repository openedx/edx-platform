from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase
from django.test.utils import override_settings
from factory import DjangoModelFactory
import json
import re
from unittest import SkipTest

from student.tests.factories import UserFactory
from user_api.models import UserPreference


TEST_API_KEY = "test_api_key"
USER_LIST_URI = "/user_api/v1/users/"
USER_PREFERENCE_LIST_URI = "/user_api/v1/user_prefs/"


class UserPreferenceFactory(DjangoModelFactory):
    FACTORY_FOR = UserPreference

    user = None
    key = None
    value = "default test value"


class UserPreferenceModelTest(TestCase):
    def test_duplicate_user_key(self):
        user = UserFactory.create()
        UserPreferenceFactory.create(user=user, key="testkey", value="first")
        self.assertRaises(
            IntegrityError,
            UserPreferenceFactory.create,
            user=user,
            key="testkey",
            value="second"
        )

    def test_arbitrary_values(self):
        user = UserFactory.create()
        UserPreferenceFactory.create(user=user, key="testkey0", value="")
        UserPreferenceFactory.create(user=user, key="testkey1", value="This is some English text!")
        UserPreferenceFactory.create(user=user, key="testkey2", value="{'some': 'json'}")


class UserApiTestCase(TestCase):
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

    def get_with_auth(self, *args, **kwargs):
        """Issue a get request to the given URI with the API key header"""
        return self.client.get(*args, HTTP_X_EDX_API_KEY=TEST_API_KEY, **kwargs)

    def get_json(self, *args, **kwargs):
        """Make a request with the given args and return the parsed JSON repsonse"""
        resp = self.get_with_auth(*args, **kwargs)
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
        resp = self.client.options(uri)
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
        self.assertItemsEqual(user.keys(), ["email", "id", "name", "url"])
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

    def assertHttpMethodNotAllowed(self, response):
        """Assert that the given response has the status code 405"""
        self.assertEqual(response.status_code, 405)


class UserViewSetTest(UserApiTestCase):
    LIST_URI = USER_LIST_URI

    def setUp(self):
        super(UserViewSetTest, self).setUp()
        self.DETAIL_URI = self.get_uri_for_user(self.users[0])

    # List view tests

    def test_options_list(self):
        self.assertAllowedMethods(self.LIST_URI, ["OPTIONS", "GET", "HEAD"])

    def test_post_list_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.client.post(self.LIST_URI))

    def test_put_list_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.client.put(self.LIST_URI))

    def test_patch_list_not_allowed(self):
        raise SkipTest("Django 1.4's test client does not support patch")

    def test_delete_list_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.client.delete(self.LIST_URI))

    @override_settings(EDX_API_KEY=TEST_API_KEY)
    def test_list_unauthorized(self):
        self.assertHttpForbidden(self.client.get(self.LIST_URI))

    @override_settings(EDX_API_KEY=TEST_API_KEY)
    def test_list_auth(self):
        self.assertHttpOK(self.get_with_auth(self.LIST_URI))

    def test_get_list_empty(self):
        User.objects.all().delete()
        result = self.get_json(self.LIST_URI)
        self.assertEqual(result["count"], 0)
        self.assertIsNone(result["next"])
        self.assertIsNone(result["previous"])
        self.assertEqual(result["results"], [])

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
        self.assertAllowedMethods(self.DETAIL_URI, ["OPTIONS", "GET", "HEAD"])

    def test_post_detail_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.client.post(self.DETAIL_URI))

    def test_put_detail_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.client.put(self.DETAIL_URI))

    def test_patch_detail_not_allowed(self):
        raise SkipTest("Django 1.4's test client does not support patch")

    def test_delete_detail_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.client.delete(self.DETAIL_URI))

    @override_settings(EDX_API_KEY=TEST_API_KEY)
    def test_get_detail_unauthorized(self):
        self.assertHttpForbidden(self.client.get(self.DETAIL_URI))

    @override_settings(EDX_API_KEY=TEST_API_KEY)
    def test_detail_auth(self):
        self.assertHttpOK(self.get_with_auth(self.DETAIL_URI))

    def test_get_detail(self):
        user = self.users[1]
        uri = self.get_uri_for_user(user)
        self.assertEqual(
            self.get_json(uri),
            {
                "email": user.email,
                "id": user.id,
                "name": user.profile.name,
                "url": uri,
            }
        )


class UserPreferenceViewSetTest(UserApiTestCase):
    LIST_URI = USER_PREFERENCE_LIST_URI

    def setUp(self):
        super(UserPreferenceViewSetTest, self).setUp()
        self.DETAIL_URI = self.get_uri_for_pref(self.prefs[0])

    # List view tests

    def test_options_list(self):
        self.assertAllowedMethods(self.LIST_URI, ["OPTIONS", "GET", "HEAD"])

    def test_put_list_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.client.put(self.LIST_URI))

    def test_patch_list_not_allowed(self):
        raise SkipTest("Django 1.4's test client does not support patch")

    def test_delete_list_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.client.delete(self.LIST_URI))

    @override_settings(EDX_API_KEY=TEST_API_KEY)
    def test_list_unauthorized(self):
        self.assertHttpForbidden(self.client.get(self.LIST_URI))

    @override_settings(EDX_API_KEY=TEST_API_KEY)
    def test_list_auth(self):
        self.assertHttpOK(self.get_with_auth(self.LIST_URI))

    def test_get_list_empty(self):
        UserPreference.objects.all().delete()
        result = self.get_json(self.LIST_URI)
        self.assertEqual(result["count"], 0)
        self.assertIsNone(result["next"])
        self.assertIsNone(result["previous"])
        self.assertEqual(result["results"], [])

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
        self.assertAllowedMethods(self.DETAIL_URI, ["OPTIONS", "GET", "HEAD"])

    def test_post_detail_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.client.post(self.DETAIL_URI))

    def test_put_detail_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.client.put(self.DETAIL_URI))

    def test_patch_detail_not_allowed(self):
        raise SkipTest("Django 1.4's test client does not support patch")

    def test_delete_detail_not_allowed(self):
        self.assertHttpMethodNotAllowed(self.client.delete(self.DETAIL_URI))

    @override_settings(EDX_API_KEY=TEST_API_KEY)
    def test_detail_unauthorized(self):
        self.assertHttpForbidden(self.client.get(self.DETAIL_URI))

    @override_settings(EDX_API_KEY=TEST_API_KEY)
    def test_detail_auth(self):
        self.assertHttpOK(self.get_with_auth(self.DETAIL_URI))

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
                    "url": self.get_uri_for_user(pref.user),
                },
                "key": pref.key,
                "value": pref.value,
                "url": uri,
            }
        )
