# -*- coding: utf-8 -*-
"""
Unit tests for preference APIs.
"""

import unittest
import ddt
import json

from django.core.urlresolvers import reverse
from django.conf import settings

from ...accounts.tests.test_views import UserAPITestCase
from ..api import set_user_preference
from .test_api import get_expected_validation_developer_message, get_expected_key_error_user_message

TOO_LONG_PREFERENCE_KEY = u"x" * 256


@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestPreferencesAPI(UserAPITestCase):
    """
    Unit tests /api/user/v0/accounts/{username}/
    """
    def setUp(self):
        super(TestPreferencesAPI, self).setUp()
        self.url_endpoint_name = "preferences_api"
        self.url = reverse(self.url_endpoint_name, kwargs={'username': self.user.username})

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

    def test_get_different_user(self):
        """
        Test that a client (logged in) cannot get the preferences information for a different client.
        """
        self.different_client.login(username=self.different_user.username, password=self.test_password)
        self.send_get(self.different_client, expected_status=404)

    @ddt.data(
        ("client", "user"),
        ("staff_client", "staff_user"),
    )
    @ddt.unpack
    def test_get_unknown_user(self, api_client, username):
        """
        Test that requesting a user who does not exist returns a 404.
        """
        client = self.login_client(api_client, username)
        response = client.get(reverse(self.url_endpoint_name, kwargs={'username': "does_not_exist"}))
        self.assertEqual(404, response.status_code)

    def test_get_preferences_default(self):
        """
        Test that a client (logged in) can get her own preferences information (verifying the default
        state before any preferences are stored).
        """
        self.client.login(username=self.user.username, password=self.test_password)
        response = self.send_get(self.client)
        self.assertEqual({}, response.data)

    @ddt.data(
        ("client", "user"),
        ("staff_client", "staff_user"),
    )
    @ddt.unpack
    def test_get_preferences(self, api_client, user):
        """
        Test that a client (logged in) can get her own preferences information. Also verifies that a "is_staff"
        user can get the preferences information for other users.
        """
        # Create some test preferences values.
        set_user_preference(self.user, "dict_pref", {"int_key": 10})
        set_user_preference(self.user, "string_pref", "value")

        # Log in the client and do the GET.
        client = self.login_client(api_client, user)
        response = self.send_get(client)
        self.assertEqual({"dict_pref": "{'int_key': 10}", "string_pref": "value"}, response.data)

    @ddt.data(
        ("client", "user"),
        ("staff_client", "staff_user"),
    )
    @ddt.unpack
    def test_patch_unknown_user(self, api_client, user):
        """
        Test that trying to update preferences for a user who does not exist returns a 404.
        """
        client = self.login_client(api_client, user)
        response = client.patch(
            reverse(self.url_endpoint_name, kwargs={'username': "does_not_exist"}),
            data=json.dumps({"string_pref": "value"}), content_type="application/merge-patch+json"
        )
        self.assertEqual(404, response.status_code)

    def test_patch_bad_content_type(self):
        """
        Test the behavior of patch when an incorrect content_type is specified.
        """
        self.client.login(username=self.user.username, password=self.test_password)
        self.send_patch(self.client, {}, content_type="application/json", expected_status=415)
        self.send_patch(self.client, {}, content_type="application/xml", expected_status=415)

    def test_create_preferences(self):
        """
        Test that a client (logged in) can create her own preferences information.
        """
        self._do_create_preferences_test(True)

    def test_create_preferences_inactive(self):
        """
        Test that a client (logged in but not active) can create her own preferences information.
        """
        self._do_create_preferences_test(False)

    def _do_create_preferences_test(self, is_active):
        self.client.login(username=self.user.username, password=self.test_password)
        if not is_active:
            self.user.is_active = False
            self.user.save()
        self.send_patch(self.client, {
            "dict_pref": {"int_key": 10},
            "string_pref": "value",
        })
        response = self.send_get(self.client)
        self.assertEqual({u"dict_pref": u"{u'int_key': 10}", u"string_pref": u"value"}, response.data)

    @ddt.data(
        ("different_client", "different_user"),
        ("staff_client", "staff_user"),
    )
    @ddt.unpack
    def test_create_preferences_other_user(self, api_client, user):
        """
        Test that a client (logged in) cannot create preferences for another user.
        """
        client = self.login_client(api_client, user)
        self.send_patch(
            client,
            {
                "dict_pref": {"int_key": 10},
                "string_pref": "value",
            },
            expected_status=403 if user == "staff_user" else 404,
        )

    def test_update_preferences(self):
        """
        Test that a client (logged in) can update her own preferences information.
        """
        # Create some test preferences values.
        set_user_preference(self.user, "dict_pref", {"int_key": 10})
        set_user_preference(self.user, "string_pref", "value")
        set_user_preference(self.user, "extra_pref", "extra_value")

        # Send the patch request
        self.client.login(username=self.user.username, password=self.test_password)
        self.send_patch(self.client, {
            "string_pref": "updated_value",
            "new_pref": "new_value",
            "extra_pref": None,
        })

        # Verify that GET returns the updated preferences
        response = self.send_get(self.client)
        expected_preferences = {
            "dict_pref": "{'int_key': 10}",
            "string_pref": "updated_value",
            "new_pref": "new_value",
        }
        self.assertEqual(expected_preferences, response.data)

    def test_update_preferences_bad_data(self):
        """
        Test that a client (logged in) receives appropriate errors for a bad update.
        """
        # Create some test preferences values.
        set_user_preference(self.user, "dict_pref", {"int_key": 10})
        set_user_preference(self.user, "string_pref", "value")
        set_user_preference(self.user, "extra_pref", "extra_value")

        # Send the patch request
        self.client.login(username=self.user.username, password=self.test_password)
        response = self.send_patch(
            self.client,
            {
                "string_pref": "updated_value",
                TOO_LONG_PREFERENCE_KEY: "new_value",
                "new_pref": "new_value",
                u"empty_pref_ȻħȺɍłɇs": "",
            },
            expected_status=400
        )
        self.assertTrue(response.data.get("field_errors", None))
        field_errors = response.data["field_errors"]
        self.assertEquals(
            field_errors,
            {
                TOO_LONG_PREFERENCE_KEY: {
                    "developer_message": get_expected_validation_developer_message(
                        TOO_LONG_PREFERENCE_KEY, "new_value"
                    ),
                    "user_message": get_expected_key_error_user_message(
                        TOO_LONG_PREFERENCE_KEY, "new_value"
                    ),
                },
                u"empty_pref_ȻħȺɍłɇs": {
                    "developer_message": u"Preference 'empty_pref_ȻħȺɍłɇs' cannot be set to an empty value.",
                    "user_message": u"Preference 'empty_pref_ȻħȺɍłɇs' cannot be set to an empty value.",
                },
            }
        )

        # Verify that GET returns the original preferences
        response = self.send_get(self.client)
        expected_preferences = {
            u"dict_pref": u"{'int_key': 10}",
            u"string_pref": u"value",
            u"extra_pref": u"extra_value",
        }
        self.assertEqual(expected_preferences, response.data)

    def test_update_preferences_bad_request(self):
        """
        Test that a client (logged in) receives appropriate errors for a bad request.
        """
        self.client.login(username=self.user.username, password=self.test_password)

        # Verify a non-dict request
        response = self.send_patch(self.client, "non_dict_request", expected_status=400)
        self.assertEqual(
            response.data,
            {
                "developer_message": u"No data provided for user preference update",
                "user_message": u"No data provided for user preference update"
            }
        )

        # Verify an empty dict request
        response = self.send_patch(self.client, {}, expected_status=400)
        self.assertEqual(
            response.data,
            {
                "developer_message": u"No data provided for user preference update",
                "user_message": u"No data provided for user preference update"
            }
        )

    @ddt.data(
        ("different_client", "different_user"),
        ("staff_client", "staff_user"),
    )
    @ddt.unpack
    def test_update_preferences_other_user(self, api_client, user):
        """
        Test that a client (logged in) cannot update preferences for another user.
        """
        # Create some test preferences values.
        set_user_preference(self.user, "dict_pref", {"int_key": 10})
        set_user_preference(self.user, "string_pref", "value")
        set_user_preference(self.user, "extra_pref", "extra_value")

        # Send the patch request
        client = self.login_client(api_client, user)
        self.send_patch(
            client,
            {
                "string_pref": "updated_value",
                "new_pref": "new_value",
                "extra_pref": None,
            },
            expected_status=403 if user == "staff_user" else 404
        )


@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestPreferencesDetailAPI(UserAPITestCase):
    """
    Unit tests /api/user/v0/accounts/{username}/{preference_key}
    """
    def setUp(self):
        super(TestPreferencesDetailAPI, self).setUp()
        self.test_pref_key = "test_key"
        self.test_pref_value = "test_value"
        set_user_preference(self.user, self.test_pref_key, self.test_pref_value)
        self.url_endpoint_name = "preferences_detail_api"
        self._set_url(self.test_pref_key)

    def _set_url(self, preference_key):
        self.url = reverse(
            self.url_endpoint_name,
            kwargs={'username': self.user.username, 'preference_key': preference_key}
        )

    def test_anonymous_user_access(self):
        """
        Test that an anonymous client (logged in) cannot manipulate preferences.
        """
        self.send_get(self.anonymous_client, expected_status=401)
        self.send_put(self.anonymous_client, "new_value", expected_status=401)
        self.send_delete(self.anonymous_client, expected_status=401)

    def test_unsupported_methods(self):
        """
        Test that POST and PATCH are not supported.
        """
        self.client.login(username=self.user.username, password=self.test_password)
        self.assertEqual(405, self.client.post(self.url).status_code)
        self.assertEqual(405, self.client.patch(self.url).status_code)

    def test_different_user_access(self):
        """
        Test that a client (logged in) cannot manipulate a preference for a different client.
        """
        self.different_client.login(username=self.different_user.username, password=self.test_password)
        self.send_get(self.different_client, expected_status=404)
        self.send_put(self.different_client, "new_value", expected_status=404)
        self.send_delete(self.different_client, expected_status=404)

    @ddt.data(
        ("client", "user"),
        ("staff_client", "staff_user"),
    )
    @ddt.unpack
    def test_get_unknown_user(self, api_client, username):
        """
        Test that requesting a user who does not exist returns a 404.
        """
        client = self.login_client(api_client, username)
        response = client.get(
            reverse(self.url_endpoint_name, kwargs={'username': "does_not_exist", 'preference_key': self.test_pref_key})
        )
        self.assertEqual(404, response.status_code)

    def test_get_preference_does_not_exist(self):
        """
        Test that a 404 is returned if the user does not have a preference with the given preference_key.
        """
        self._set_url("does_not_exist")
        self.client.login(username=self.user.username, password=self.test_password)
        response = self.send_get(self.client, expected_status=404)
        self.assertIsNone(response.data)

    @ddt.data(
        ("client", "user"),
        ("staff_client", "staff_user"),
    )
    @ddt.unpack
    def test_get_preference(self, api_client, user):
        """
        Test that a client (logged in) can get her own preferences information. Also verifies that a "is_staff"
        user can get the preferences information for other users.
        """
        client = self.login_client(api_client, user)
        response = self.send_get(client)
        self.assertEqual(self.test_pref_value, response.data)

        # Test a different value.
        set_user_preference(self.user, "dict_pref", {"int_key": 10})
        self._set_url("dict_pref")
        response = self.send_get(client)
        self.assertEqual("{'int_key': 10}", response.data)

    def test_create_preference(self):
        """
        Test that a client (logged in) can create a preference.
        """
        self._do_create_preference_test(True)

    def test_create_preference_inactive(self):
        """
        Test that a client (logged in but not active) can create a preference.
        """
        self._do_create_preference_test(False)

    def _do_create_preference_test(self, is_active):
        self.client.login(username=self.user.username, password=self.test_password)
        if not is_active:
            self.user.is_active = False
            self.user.save()
        self._set_url("new_key")
        new_value = "new value"
        self.send_put(self.client, new_value)
        response = self.send_get(self.client)
        self.assertEqual(new_value, response.data)

    @ddt.data(
        (None,),
        ("",),
        ("  ",),
    )
    @ddt.unpack
    def test_create_empty_preference(self, preference_value):
        """
        Test that a client (logged in) cannot create an empty preference.
        """
        self._set_url("new_key")
        self.client.login(username=self.user.username, password=self.test_password)
        response = self.send_put(self.client, preference_value, expected_status=400)
        self.assertEqual(
            response.data,
            {
                "developer_message": u"Preference 'new_key' cannot be set to an empty value.",
                "user_message": u"Preference 'new_key' cannot be set to an empty value."
            }
        )
        self.send_get(self.client, expected_status=404)

    def test_create_preference_too_long_key(self):
        """
        Test that a client cannot create preferences with bad keys
        """
        self.client.login(username=self.user.username, password=self.test_password)

        too_long_preference_key = "x" * 256
        new_value = "new value"
        self._set_url(too_long_preference_key)
        response = self.send_put(self.client, new_value, expected_status=400)
        self.assertEquals(
            response.data,
            {
                "developer_message": get_expected_validation_developer_message(too_long_preference_key, new_value),
                "user_message": get_expected_key_error_user_message(too_long_preference_key, new_value),
            }
        )

    @ddt.data(
        ("different_client", "different_user"),
        ("staff_client", "staff_user"),
    )
    @ddt.unpack
    def test_create_preference_other_user(self, api_client, user):
        """
        Test that a client (logged in) cannot create a preference for a different user.
        """
        # Verify that a new preference cannot be created
        self._set_url("new_key")
        client = self.login_client(api_client, user)
        new_value = "new value"
        self.send_put(client, new_value, expected_status=403 if user == "staff_user" else 404)

    @ddt.data(
        (u"new value",),
        (10,),
        ({u"int_key": 10},)
    )
    @ddt.unpack
    def test_update_preference(self, preference_value):
        """
        Test that a client (logged in) can update a preference.
        """
        self.client.login(username=self.user.username, password=self.test_password)
        self.send_put(self.client, preference_value)
        response = self.send_get(self.client)
        self.assertEqual(unicode(preference_value), response.data)

    @ddt.data(
        ("different_client", "different_user"),
        ("staff_client", "staff_user"),
    )
    @ddt.unpack
    def test_update_preference_other_user(self, api_client, user):
        """
        Test that a client (logged in) cannot update a preference for another user.
        """
        client = self.login_client(api_client, user)
        new_value = "new value"
        self.send_put(client, new_value, expected_status=403 if user == "staff_user" else 404)

    @ddt.data(
        (None,),
        ("",),
        ("  ",),
    )
    @ddt.unpack
    def test_update_preference_to_empty(self, preference_value):
        """
        Test that a client (logged in) cannot update a preference to null.
        """
        self.client.login(username=self.user.username, password=self.test_password)
        response = self.send_put(self.client, preference_value, expected_status=400)
        self.assertEqual(
            response.data,
            {
                "developer_message": u"Preference 'test_key' cannot be set to an empty value.",
                "user_message": u"Preference 'test_key' cannot be set to an empty value."
            }
        )
        response = self.send_get(self.client)
        self.assertEqual(self.test_pref_value, response.data)

    def test_delete_preference(self):
        """
        Test that a client (logged in) can delete her own preference.
        """
        self.client.login(username=self.user.username, password=self.test_password)

        # Verify that a preference can be deleted
        self.send_delete(self.client)
        self.send_get(self.client, expected_status=404)

        # Verify that deleting a non-existent preference throws a 404
        self.send_delete(self.client, expected_status=404)

    @ddt.data(
        ("different_client", "different_user"),
        ("staff_client", "staff_user"),
    )
    @ddt.unpack
    def test_delete_preference_other_user(self, api_client, user):
        """
        Test that a client (logged in) cannot delete a preference for another user.
        """
        client = self.login_client(api_client, user)
        self.send_delete(client, expected_status=403 if user == "staff_user" else 404)
