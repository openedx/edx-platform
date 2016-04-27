# -*- coding: utf-8 -*-
"""
Unit tests for preference APIs.
"""
import datetime
import ddt
import unittest
from mock import patch
from nose.plugins.attrib import attr
from pytz import common_timezones, utc

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings
from dateutil.parser import parse as parse_datetime

from student.tests.factories import UserFactory

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from ...accounts.api import create_account
from ...errors import (
    UserNotFound,
    UserNotAuthorized,
    PreferenceValidationError,
    PreferenceUpdateError,
    CountryCodeError,
)
from ...models import UserProfile, UserOrgTag
from ...preferences.api import (
    get_user_preference,
    get_user_preferences,
    set_user_preference,
    update_user_preferences,
    delete_user_preference,
    update_email_opt_in,
    get_country_time_zones,
)


@attr(shard=2)
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Account APIs are only supported in LMS')
class TestPreferenceAPI(TestCase):
    """
    These tests specifically cover the parts of the API methods that are not covered by test_views.py.
    This includes the specific types of error raised, and default behavior when optional arguments
    are not specified.
    """
    password = "test"

    def setUp(self):
        super(TestPreferenceAPI, self).setUp()
        self.user = UserFactory.create(password=self.password)
        self.different_user = UserFactory.create(password=self.password)
        self.staff_user = UserFactory(is_staff=True, password=self.password)
        self.no_such_user = UserFactory.create(password=self.password)
        self.no_such_user.username = "no_such_user"
        self.test_preference_key = "test_key"
        self.test_preference_value = "test_value"
        set_user_preference(self.user, self.test_preference_key, self.test_preference_value)

    def test_get_user_preference(self):
        """
        Verifies the basic behavior of get_user_preference.
        """
        self.assertEqual(
            get_user_preference(self.user, self.test_preference_key),
            self.test_preference_value
        )
        self.assertEqual(
            get_user_preference(self.staff_user, self.test_preference_key, username=self.user.username),
            self.test_preference_value
        )

    def test_get_user_preference_errors(self):
        """
        Verifies that get_user_preference returns appropriate errors.
        """
        with self.assertRaises(UserNotFound):
            get_user_preference(self.user, self.test_preference_key, username="no_such_user")

        with self.assertRaises(UserNotFound):
            get_user_preference(self.no_such_user, self.test_preference_key)

        with self.assertRaises(UserNotAuthorized):
            get_user_preference(self.different_user, self.test_preference_key, username=self.user.username)

    def test_get_user_preferences(self):
        """
        Verifies the basic behavior of get_user_preferences.
        """
        expected_user_preferences = {
            self.test_preference_key: self.test_preference_value,
        }
        self.assertEqual(get_user_preferences(self.user), expected_user_preferences)
        self.assertEqual(get_user_preferences(self.staff_user, username=self.user.username), expected_user_preferences)

    def test_get_user_preferences_errors(self):
        """
        Verifies that get_user_preferences returns appropriate errors.
        """
        with self.assertRaises(UserNotFound):
            get_user_preferences(self.user, username="no_such_user")

        with self.assertRaises(UserNotFound):
            get_user_preferences(self.no_such_user)

        with self.assertRaises(UserNotAuthorized):
            get_user_preferences(self.different_user, username=self.user.username)

    def test_set_user_preference(self):
        """
        Verifies the basic behavior of set_user_preference.
        """
        test_key = u'ⓟⓡⓔⓕⓔⓡⓔⓝⓒⓔ_ⓚⓔⓨ'
        test_value = u'ǝnןɐʌ_ǝɔuǝɹǝɟǝɹd'
        set_user_preference(self.user, test_key, test_value)
        self.assertEqual(get_user_preference(self.user, test_key), test_value)
        set_user_preference(self.user, test_key, "new_value", username=self.user.username)
        self.assertEqual(get_user_preference(self.user, test_key), "new_value")

    @patch('openedx.core.djangoapps.user_api.models.UserPreference.save')
    def test_set_user_preference_errors(self, user_preference_save):
        """
        Verifies that set_user_preference returns appropriate errors.
        """
        with self.assertRaises(UserNotFound):
            set_user_preference(self.user, self.test_preference_key, "new_value", username="no_such_user")

        with self.assertRaises(UserNotFound):
            set_user_preference(self.no_such_user, self.test_preference_key, "new_value")

        with self.assertRaises(UserNotAuthorized):
            set_user_preference(self.staff_user, self.test_preference_key, "new_value", username=self.user.username)

        with self.assertRaises(UserNotAuthorized):
            set_user_preference(self.different_user, self.test_preference_key, "new_value", username=self.user.username)

        too_long_key = "x" * 256
        with self.assertRaises(PreferenceValidationError) as context_manager:
            set_user_preference(self.user, too_long_key, "new_value")
        errors = context_manager.exception.preference_errors
        self.assertEqual(len(errors.keys()), 1)
        self.assertEqual(
            errors[too_long_key],
            {
                "developer_message": get_expected_validation_developer_message(too_long_key, "new_value"),
                "user_message": get_expected_key_error_user_message(too_long_key, "new_value"),
            }
        )

        for empty_value in (None, "", "   "):
            with self.assertRaises(PreferenceValidationError) as context_manager:
                set_user_preference(self.user, self.test_preference_key, empty_value)
            errors = context_manager.exception.preference_errors
            self.assertEqual(len(errors.keys()), 1)
            self.assertEqual(
                errors[self.test_preference_key],
                {
                    "developer_message": get_empty_preference_message(self.test_preference_key),
                    "user_message": get_empty_preference_message(self.test_preference_key),
                }
            )

        user_preference_save.side_effect = [Exception, None]
        with self.assertRaises(PreferenceUpdateError) as context_manager:
            set_user_preference(self.user, u"new_key_ȻħȺɍłɇs", u"new_value_ȻħȺɍłɇs")
        self.assertEqual(
            context_manager.exception.developer_message,
            u"Save failed for user preference 'new_key_ȻħȺɍłɇs' with value 'new_value_ȻħȺɍłɇs': "
        )
        self.assertEqual(
            context_manager.exception.user_message,
            u"Save failed for user preference 'new_key_ȻħȺɍłɇs' with value 'new_value_ȻħȺɍłɇs'."
        )

    def test_update_user_preferences(self):
        """
        Verifies the basic behavior of update_user_preferences.
        """
        set_user_preference(self.user, self.test_preference_key, "new_value")
        self.assertEqual(
            get_user_preference(self.user, self.test_preference_key),
            "new_value"
        )
        set_user_preference(self.user, self.test_preference_key, "new_value", username=self.user.username)
        self.assertEqual(
            get_user_preference(self.user, self.test_preference_key),
            "new_value"
        )

    def test_update_user_preferences_with_username(self):
        """
        Verifies the basic behavior of update_user_preferences when passed
        username string.
        """
        update_data = {
            self.test_preference_key: "new_value"
        }
        update_user_preferences(self.user, update_data, user=self.user.username)
        self.assertEqual(
            get_user_preference(self.user, self.test_preference_key),
            "new_value"
        )

    def test_update_user_preferences_with_user(self):
        """
        Verifies the basic behavior of update_user_preferences when passed
        user object.
        """
        update_data = {
            self.test_preference_key: "new_value"
        }
        update_user_preferences(self.user, update_data, user=self.user)
        self.assertEqual(
            get_user_preference(self.user, self.test_preference_key),
            "new_value"
        )

    @patch('openedx.core.djangoapps.user_api.models.UserPreference.delete')
    @patch('openedx.core.djangoapps.user_api.models.UserPreference.save')
    def test_update_user_preferences_errors(self, user_preference_save, user_preference_delete):
        """
        Verifies that set_user_preferences returns appropriate errors.
        """
        update_data = {
            self.test_preference_key: "new_value"
        }
        with self.assertRaises(UserNotFound):
            update_user_preferences(self.user, update_data, user="no_such_user")

        with self.assertRaises(UserNotFound):
            update_user_preferences(self.no_such_user, update_data)

        with self.assertRaises(UserNotAuthorized):
            update_user_preferences(self.staff_user, update_data, user=self.user.username)

        with self.assertRaises(UserNotAuthorized):
            update_user_preferences(self.different_user, update_data, user=self.user.username)

        too_long_key = "x" * 256
        with self.assertRaises(PreferenceValidationError) as context_manager:
            update_user_preferences(self.user, {too_long_key: "new_value"})
        errors = context_manager.exception.preference_errors
        self.assertEqual(len(errors.keys()), 1)
        self.assertEqual(
            errors[too_long_key],
            {
                "developer_message": get_expected_validation_developer_message(too_long_key, "new_value"),
                "user_message": get_expected_key_error_user_message(too_long_key, "new_value"),
            }
        )

        for empty_value in ("", "   "):
            with self.assertRaises(PreferenceValidationError) as context_manager:
                update_user_preferences(self.user, {self.test_preference_key: empty_value})
            errors = context_manager.exception.preference_errors
            self.assertEqual(len(errors.keys()), 1)
            self.assertEqual(
                errors[self.test_preference_key],
                {
                    "developer_message": get_empty_preference_message(self.test_preference_key),
                    "user_message": get_empty_preference_message(self.test_preference_key),
                }
            )

        user_preference_save.side_effect = [Exception, None]
        with self.assertRaises(PreferenceUpdateError) as context_manager:
            update_user_preferences(self.user, {self.test_preference_key: "new_value"})
        self.assertEqual(
            context_manager.exception.developer_message,
            u"Save failed for user preference 'test_key' with value 'new_value': "
        )
        self.assertEqual(
            context_manager.exception.user_message,
            u"Save failed for user preference 'test_key' with value 'new_value'."
        )

        user_preference_delete.side_effect = [Exception, None]
        with self.assertRaises(PreferenceUpdateError) as context_manager:
            update_user_preferences(self.user, {self.test_preference_key: None})
        self.assertEqual(
            context_manager.exception.developer_message,
            u"Delete failed for user preference 'test_key': "
        )
        self.assertEqual(
            context_manager.exception.user_message,
            u"Delete failed for user preference 'test_key'."
        )

    def test_delete_user_preference(self):
        """
        Verifies the basic behavior of delete_user_preference.
        """
        self.assertTrue(delete_user_preference(self.user, self.test_preference_key))
        set_user_preference(self.user, self.test_preference_key, self.test_preference_value)
        self.assertTrue(delete_user_preference(self.user, self.test_preference_key, username=self.user.username))
        self.assertFalse(delete_user_preference(self.user, "no_such_key"))

    @patch('openedx.core.djangoapps.user_api.models.UserPreference.delete')
    def test_delete_user_preference_errors(self, user_preference_delete):
        """
        Verifies that delete_user_preference returns appropriate errors.
        """
        with self.assertRaises(UserNotFound):
            delete_user_preference(self.user, self.test_preference_key, username="no_such_user")

        with self.assertRaises(UserNotFound):
            delete_user_preference(self.no_such_user, self.test_preference_key)

        with self.assertRaises(UserNotAuthorized):
            delete_user_preference(self.staff_user, self.test_preference_key, username=self.user.username)

        with self.assertRaises(UserNotAuthorized):
            delete_user_preference(self.different_user, self.test_preference_key, username=self.user.username)

        user_preference_delete.side_effect = [Exception, None]
        with self.assertRaises(PreferenceUpdateError) as context_manager:
            delete_user_preference(self.user, self.test_preference_key)
        self.assertEqual(
            context_manager.exception.developer_message,
            u"Delete failed for user preference 'test_key': "
        )
        self.assertEqual(
            context_manager.exception.user_message,
            u"Delete failed for user preference 'test_key'."
        )


@attr(shard=2)
@ddt.ddt
class UpdateEmailOptInTests(ModuleStoreTestCase):
    """
    Test cases to cover API-driven email list opt-in update workflows
    """
    USERNAME = u'frank-underwood'
    PASSWORD = u'ṕáśśẃőŕd'
    EMAIL = u'frank+underwood@example.com'

    @ddt.data(
        # Check that a 27 year old can opt-in
        (27, True, u"True"),

        # Check that a 32-year old can opt-out
        (32, False, u"False"),

        # Check that someone 14 years old can opt-in
        (14, True, u"True"),

        # Check that someone 13 years old cannot opt-in (must have turned 13 before this year)
        (13, True, u"False"),

        # Check that someone 12 years old cannot opt-in
        (12, True, u"False")
    )
    @ddt.unpack
    @override_settings(EMAIL_OPTIN_MINIMUM_AGE=13)
    def test_update_email_optin(self, age, option, expected_result):
        # Create the course and account.
        course = CourseFactory.create()
        create_account(self.USERNAME, self.PASSWORD, self.EMAIL)

        # Set year of birth
        user = User.objects.get(username=self.USERNAME)
        profile = UserProfile.objects.get(user=user)
        year_of_birth = datetime.datetime.now().year - age
        profile.year_of_birth = year_of_birth
        profile.save()

        update_email_opt_in(user, course.id.org, option)
        result_obj = UserOrgTag.objects.get(user=user, org=course.id.org, key='email-optin')
        self.assertEqual(result_obj.value, expected_result)

    def test_update_email_optin_no_age_set(self):
        # Test that the API still works if no age is specified.
        # Create the course and account.
        course = CourseFactory.create()
        create_account(self.USERNAME, self.PASSWORD, self.EMAIL)

        user = User.objects.get(username=self.USERNAME)

        update_email_opt_in(user, course.id.org, True)
        result_obj = UserOrgTag.objects.get(user=user, org=course.id.org, key='email-optin')
        self.assertEqual(result_obj.value, u"True")

    def test_update_email_optin_anonymous_user(self):
        """Verify that the API raises an exception for a user with no profile."""
        course = CourseFactory.create()
        no_profile_user, __ = User.objects.get_or_create(username="no_profile_user", password=self.PASSWORD)
        with self.assertRaises(UserNotFound):
            update_email_opt_in(no_profile_user, course.id.org, True)

    @ddt.data(
        # Check that a 27 year old can opt-in, then out.
        (27, True, False, u"False"),

        # Check that a 32-year old can opt-out, then in.
        (32, False, True, u"True"),

        # Check that someone 13 years old can opt-in, then out.
        (13, True, False, u"False"),

        # Check that someone 12 years old cannot opt-in, then explicitly out.
        (12, True, False, u"False")
    )
    @ddt.unpack
    @override_settings(EMAIL_OPTIN_MINIMUM_AGE=13)
    def test_change_email_optin(self, age, option, second_option, expected_result):
        # Create the course and account.
        course = CourseFactory.create()
        create_account(self.USERNAME, self.PASSWORD, self.EMAIL)

        # Set year of birth
        user = User.objects.get(username=self.USERNAME)
        profile = UserProfile.objects.get(user=user)
        year_of_birth = datetime.datetime.now(utc).year - age
        profile.year_of_birth = year_of_birth
        profile.save()

        update_email_opt_in(user, course.id.org, option)
        update_email_opt_in(user, course.id.org, second_option)

        result_obj = UserOrgTag.objects.get(user=user, org=course.id.org, key='email-optin')
        self.assertEqual(result_obj.value, expected_result)

    def _assert_is_datetime(self, timestamp):
        """
        Internal helper to assert the type of the provided timestamp value
        """
        if not timestamp:
            return False
        try:
            parse_datetime(timestamp)
        except ValueError:
            return False
        else:
            return True


@ddt.ddt
class CountryTimeZoneTest(TestCase):
    """
    Test cases to validate country code api functionality
    """

    @ddt.data(('NZ', ['Pacific/Auckland', 'Pacific/Chatham']),
              (None, common_timezones))
    @ddt.unpack
    def test_get_country_time_zones(self, country_code, expected_time_zones):
        """Verify that list of common country time zones are returned"""
        country_time_zones = get_country_time_zones(country_code)
        self.assertEqual(country_time_zones, expected_time_zones)

    def test_country_code_errors(self):
        """Verify that country code error is raised for invalid country code"""
        with self.assertRaises(CountryCodeError):
            get_country_time_zones('AA')


def get_expected_validation_developer_message(preference_key, preference_value):
    """
    Returns the expected dict of validation messages for the specified key.
    """
    return u"Value '{preference_value}' not valid for preference '{preference_key}': {error}".format(
        preference_key=preference_key,
        preference_value=preference_value,
        error={
            "key": [u"Ensure this value has at most 255 characters (it has 256)."]
        }
    )


def get_expected_key_error_user_message(preference_key, preference_value):
    """
    Returns the expected user message for an invalid key.
    """
    return u"Invalid user preference key '{preference_key}'.".format(preference_key=preference_key)


def get_empty_preference_message(preference_key):
    """
    Returns the validation message shown for an empty preference.
    """
    return "Preference '{preference_key}' cannot be set to an empty value.".format(preference_key=preference_key)
