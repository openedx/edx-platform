# -*- coding: utf-8 -*-
"""
Unit tests for preference APIs.
"""
import ddt

from django.test.utils import override_settings
from nose.tools import raises
import datetime
from dateutil.parser import parse as parse_datetime
from pytz import UTC
from django.contrib.auth.models import User

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from openedx.core.djangoapps.user_api.accounts.api import create_account
from openedx.core.djangoapps.user_api.models import UserProfile, UserOrgTag
from openedx.core.djangoapps.user_api.preferences.api import (
    update_email_opt_in, set_user_preference, get_user_preferences, update_user_preferences
)


@ddt.ddt
class UpdateEmailOptInTests(ModuleStoreTestCase):

    USERNAME = u'frank-underwood'
    PASSWORD = u'ṕáśśẃőŕd'
    EMAIL = u'frank+underwood@example.com'

    def test_update_and_retrieve_preference_info(self):
        # TODO: move test into preferences API test.
        create_account(self.USERNAME, self.PASSWORD, self.EMAIL)

        user = User.objects.get(username=self.USERNAME)
        set_user_preference(user, 'preference_key', 'preference_value')

        preferences = get_user_preferences(user)
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
        create_account(self.USERNAME, self.PASSWORD, self.EMAIL)

        # Set year of birth
        user = User.objects.get(username=self.USERNAME)
        profile = UserProfile.objects.get(user=user)
        year_of_birth = datetime.datetime.now().year - age  # pylint: disable=maybe-no-member
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
        year_of_birth = datetime.datetime.now(UTC).year - age  # pylint: disable=maybe-no-member
        profile.year_of_birth = year_of_birth
        profile.save()

        update_email_opt_in(user, course.id.org, option)
        update_email_opt_in(user, course.id.org, second_option)

        result_obj = UserOrgTag.objects.get(user=user, org=course.id.org, key='email-optin')
        self.assertEqual(result_obj.value, expected_result)

    def test_update_and_retrieve_preference_info_unicode(self):
        # TODO: cover in preference API unit test.
        create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        user = User.objects.get(username=self.USERNAME)
        update_user_preferences(user, {u'ⓟⓡⓔⓕⓔⓡⓔⓝⓒⓔ_ⓚⓔⓨ': u'ǝnןɐʌ_ǝɔuǝɹǝɟǝɹd'})

        preferences = get_user_preferences(user)
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

