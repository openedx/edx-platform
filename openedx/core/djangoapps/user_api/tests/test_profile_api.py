# -*- coding: utf-8 -*-
""" Tests for the profile API. """
from django.contrib.auth.models import User

from django.test import TestCase
import ddt
from django.test.utils import override_settings
from nose.tools import raises
from dateutil.parser import parse as parse_datetime
from pytz import UTC
from xmodule.modulestore.tests.factories import CourseFactory
import datetime

from ..api import account as account_api
from ..api import profile as profile_api
from ..models import UserProfile, UserOrgTag


@ddt.ddt
class ProfileApiTest(TestCase):

    USERNAME = u'frank-underwood'
    PASSWORD = u'ṕáśśẃőŕd'
    EMAIL = u'frank+underwood@example.com'

    def test_create_profile(self):
        # Create a new account, which should have an empty profile by default.
        account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)

        # Retrieve the profile, expecting default values
        profile = profile_api.profile_info(username=self.USERNAME)
        self.assertEqual(profile, {
            'username': self.USERNAME,
            'email': self.EMAIL,
            'full_name': u'',
            'goals': None,
            'level_of_education': None,
            'mailing_address': None,
            'year_of_birth': None,
            'country': '',
            'city': None,
        })

    def test_update_full_name(self):
        account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        profile_api.update_profile(self.USERNAME, full_name=u'ȻħȺɍłɇs')
        profile = profile_api.profile_info(self.USERNAME)
        self.assertEqual(profile['full_name'], u'ȻħȺɍłɇs')

    @raises(profile_api.ProfileInvalidField)
    @ddt.data('', 'a', 'a' * profile_api.FULL_NAME_MAX_LENGTH + 'a')
    def test_update_full_name_invalid(self, invalid_name):
        account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        profile_api.update_profile(self.USERNAME, full_name=invalid_name)

    @raises(profile_api.ProfileUserNotFound)
    def test_update_profile_no_user(self):
        profile_api.update_profile(self.USERNAME, full_name='test')

    def test_retrieve_profile_no_user(self):
        profile = profile_api.profile_info('does not exist')
        self.assertIs(profile, None)

    def test_record_name_change_history(self):
        account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)

        # Change the name once
        # Since the original name was an empty string, expect that the list
        # of old names is empty
        profile_api.update_profile(self.USERNAME, full_name='new name')
        meta = UserProfile.objects.get(user__username=self.USERNAME).get_meta()
        self.assertEqual(meta, {})

        # Change the name again and expect the new name is stored in the history
        profile_api.update_profile(self.USERNAME, full_name='another new name')
        meta = UserProfile.objects.get(user__username=self.USERNAME).get_meta()

        self.assertEqual(len(meta['old_names']), 1)
        name, rationale, timestamp = meta['old_names'][0]
        self.assertEqual(name, 'new name')
        self.assertEqual(rationale, u'')
        self._assert_is_datetime(timestamp)

        # Change the name a third time and expect both names are stored in the history
        profile_api.update_profile(self.USERNAME, full_name='yet another new name')
        meta = UserProfile.objects.get(user__username=self.USERNAME).get_meta()

        self.assertEqual(len(meta['old_names']), 2)
        name, rationale, timestamp = meta['old_names'][1]
        self.assertEqual(name, 'another new name')
        self.assertEqual(rationale, u'')
        self._assert_is_datetime(timestamp)

    def test_update_and_retrieve_preference_info(self):
        account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)

        profile_api.update_preferences(self.USERNAME, preference_key='preference_value')

        preferences = profile_api.preference_info(self.USERNAME)
        self.assertEqual(preferences['preference_key'], 'preference_value')

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
        account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)

        # Set year of birth
        user = User.objects.get(username=self.USERNAME)
        profile = UserProfile.objects.get(user=user)
        year_of_birth = datetime.datetime.now().year - age  # pylint: disable=maybe-no-member
        profile.year_of_birth = year_of_birth
        profile.save()

        profile_api.update_email_opt_in(self.USERNAME, course.id.org, option)
        result_obj = UserOrgTag.objects.get(user=user, org=course.id.org, key='email-optin')
        self.assertEqual(result_obj.value, expected_result)

    def test_update_email_optin_no_age_set(self):
        # Test that the API still works if no age is specified.
        # Create the course and account.
        course = CourseFactory.create()
        account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)

        user = User.objects.get(username=self.USERNAME)

        profile_api.update_email_opt_in(self.USERNAME, course.id.org, True)
        result_obj = UserOrgTag.objects.get(user=user, org=course.id.org, key='email-optin')
        self.assertEqual(result_obj.value, u"True")

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
        account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)

        # Set year of birth
        user = User.objects.get(username=self.USERNAME)
        profile = UserProfile.objects.get(user=user)
        year_of_birth = datetime.datetime.now(UTC).year - age  # pylint: disable=maybe-no-member
        profile.year_of_birth = year_of_birth
        profile.save()

        profile_api.update_email_opt_in(self.USERNAME, course.id.org, option)
        profile_api.update_email_opt_in(self.USERNAME, course.id.org, second_option)

        result_obj = UserOrgTag.objects.get(user=user, org=course.id.org, key='email-optin')
        self.assertEqual(result_obj.value, expected_result)

    @raises(profile_api.ProfileUserNotFound)
    def test_retrieve_and_update_preference_info_no_user(self):
        preferences = profile_api.preference_info(self.USERNAME)
        self.assertEqual(preferences, {})

        profile_api.update_preferences(self.USERNAME, preference_key='preference_value')

    def test_update_and_retrieve_preference_info_unicode(self):
        account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)

        profile_api.update_preferences(self.USERNAME, **{u'ⓟⓡⓔⓕⓔⓡⓔⓝⓒⓔ_ⓚⓔⓨ': u'ǝnןɐʌ_ǝɔuǝɹǝɟǝɹd'})

        preferences = profile_api.preference_info(self.USERNAME)
        self.assertEqual(preferences[u'ⓟⓡⓔⓕⓔⓡⓔⓝⓒⓔ_ⓚⓔⓨ'], u'ǝnןɐʌ_ǝɔuǝɹǝɟǝɹd')

    def _assert_is_datetime(self, timestamp):
        if not timestamp:
            return False
        try:
            parse_datetime(timestamp)
        except ValueError:
            return False
        else:
            return True
