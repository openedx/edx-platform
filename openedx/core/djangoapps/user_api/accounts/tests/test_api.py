# -*- coding: utf-8 -*-
"""
Unit tests for behavior that is specific to the api methods (vs. the view methods).
Most of the functionality is covered in test_views.py.
"""
import re
import ddt
from dateutil.parser import parse as parse_datetime

from mock import Mock, patch
from django.test import TestCase
from nose.tools import raises
import unittest
from student.tests.factories import UserFactory
from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from student.models import PendingEmailChange
from student.tests.tests import UserSettingsEventTestMixin
from ...errors import (
    UserNotFound, UserNotAuthorized, AccountUpdateError, AccountValidationError,
    AccountUserAlreadyExists, AccountUsernameInvalid, AccountEmailInvalid, AccountPasswordInvalid, AccountRequestError
)
from ..api import (
    get_account_settings, update_account_settings, create_account, activate_account, request_password_change
)
from .. import USERNAME_MAX_LENGTH, EMAIL_MAX_LENGTH, PASSWORD_MAX_LENGTH


def mock_render_to_string(template_name, context):
    """Return a string that encodes template_name and context"""
    return str((template_name, sorted(context.iteritems())))


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Account APIs are only supported in LMS')
class TestAccountApi(UserSettingsEventTestMixin, TestCase):
    """
    These tests specifically cover the parts of the API methods that are not covered by test_views.py.
    This includes the specific types of error raised, and default behavior when optional arguments
    are not specified.
    """
    password = "test"

    def setUp(self):
        super(TestAccountApi, self).setUp()
        self.table = "student_languageproficiency"
        self.user = UserFactory.create(password=self.password)
        self.different_user = UserFactory.create(password=self.password)
        self.staff_user = UserFactory(is_staff=True, password=self.password)
        self.reset_tracker()

    def test_get_username_provided(self):
        """Test the difference in behavior when a username is supplied to get_account_settings."""
        account_settings = get_account_settings(self.user)
        self.assertEqual(self.user.username, account_settings["username"])

        account_settings = get_account_settings(self.user, username=self.user.username)
        self.assertEqual(self.user.username, account_settings["username"])

        account_settings = get_account_settings(self.user, username=self.different_user.username)
        self.assertEqual(self.different_user.username, account_settings["username"])

    def test_get_configuration_provided(self):
        """Test the difference in behavior when a configuration is supplied to get_account_settings."""
        config = {
            "default_visibility": "private",

            "shareable_fields": [
                'name',
            ],

            "public_fields": [
                'email',
            ],
        }

        # With default configuration settings, email is not shared with other (non-staff) users.
        account_settings = get_account_settings(self.user, self.different_user.username)
        self.assertFalse("email" in account_settings)

        account_settings = get_account_settings(self.user, self.different_user.username, configuration=config)
        self.assertEqual(self.different_user.email, account_settings["email"])

    def test_get_user_not_found(self):
        """Test that UserNotFound is thrown if there is no user with username."""
        with self.assertRaises(UserNotFound):
            get_account_settings(self.user, username="does_not_exist")

        self.user.username = "does_not_exist"
        with self.assertRaises(UserNotFound):
            get_account_settings(self.user)

    def test_update_username_provided(self):
        """Test the difference in behavior when a username is supplied to update_account_settings."""
        update_account_settings(self.user, {"name": "Mickey Mouse"})
        account_settings = get_account_settings(self.user)
        self.assertEqual("Mickey Mouse", account_settings["name"])

        update_account_settings(self.user, {"name": "Donald Duck"}, username=self.user.username)
        account_settings = get_account_settings(self.user)
        self.assertEqual("Donald Duck", account_settings["name"])

        with self.assertRaises(UserNotAuthorized):
            update_account_settings(self.different_user, {"name": "Pluto"}, username=self.user.username)

    def test_update_user_not_found(self):
        """Test that UserNotFound is thrown if there is no user with username."""
        with self.assertRaises(UserNotFound):
            update_account_settings(self.user, {}, username="does_not_exist")

        self.user.username = "does_not_exist"
        with self.assertRaises(UserNotFound):
            update_account_settings(self.user, {})

    def test_update_error_validating(self):
        """Test that AccountValidationError is thrown if incorrect values are supplied."""
        with self.assertRaises(AccountValidationError):
            update_account_settings(self.user, {"username": "not_allowed"})

        with self.assertRaises(AccountValidationError):
            update_account_settings(self.user, {"gender": "undecided"})

        with self.assertRaises(AccountValidationError):
            update_account_settings(
                self.user,
                {"profile_image": {"has_image": "not_allowed", "image_url": "not_allowed"}}
            )

        # Check the various language_proficiencies validation failures.
        # language_proficiencies must be a list of dicts, each containing a
        # unique 'code' key representing the language code.
        with self.assertRaises(AccountValidationError):
            update_account_settings(
                self.user,
                {"language_proficiencies": "not_a_list"}
            )
        with self.assertRaises(AccountValidationError):
            update_account_settings(
                self.user,
                {"language_proficiencies": [{}]}
            )

    def test_update_multiple_validation_errors(self):
        """Test that all validation errors are built up and returned at once"""
        # Send a read-only error, serializer error, and email validation error.
        naughty_update = {
            "username": "not_allowed",
            "gender": "undecided",
            "email": "not an email address"
        }

        with self.assertRaises(AccountValidationError) as context_manager:
            update_account_settings(self.user, naughty_update)
        field_errors = context_manager.exception.field_errors
        self.assertEqual(3, len(field_errors))
        self.assertEqual("This field is not editable via this API", field_errors["username"]["developer_message"])
        self.assertIn("Select a valid choice", field_errors["gender"]["developer_message"])
        self.assertIn("Valid e-mail address required.", field_errors["email"]["developer_message"])

    @patch('django.core.mail.send_mail')
    @patch('student.views.render_to_string', Mock(side_effect=mock_render_to_string, autospec=True))
    def test_update_sending_email_fails(self, send_mail):
        """Test what happens if all validation checks pass, but sending the email for email change fails."""
        send_mail.side_effect = [Exception, None]
        less_naughty_update = {
            "name": "Mickey Mouse",
            "email": "seems_ok@sample.com"
        }
        with self.assertRaises(AccountUpdateError) as context_manager:
            update_account_settings(self.user, less_naughty_update)
        self.assertIn("Error thrown from do_email_change_request", context_manager.exception.developer_message)

        # Verify that the name change happened, even though the attempt to send the email failed.
        account_settings = get_account_settings(self.user)
        self.assertEqual("Mickey Mouse", account_settings["name"])

    @patch('openedx.core.djangoapps.user_api.accounts.serializers.AccountUserSerializer.save')
    def test_serializer_save_fails(self, serializer_save):
        """
        Test the behavior of one of the serializers failing to save. Note that email request change
        won't be processed in this case.
        """
        serializer_save.side_effect = [Exception, None]
        update_will_fail = {
            "name": "Mickey Mouse",
            "email": "ok@sample.com"
        }

        with self.assertRaises(AccountUpdateError) as context_manager:
            update_account_settings(self.user, update_will_fail)
        self.assertIn("Error thrown when saving account updates", context_manager.exception.developer_message)

        # Verify that no email change request was initiated.
        pending_change = PendingEmailChange.objects.filter(user=self.user)
        self.assertEqual(0, len(pending_change))

    def test_language_proficiency_eventing(self):
        """
        Test that eventing of language proficiencies, which happens update_account_settings method, behaves correctly.
        """
        def verify_event_emitted(new_value, old_value):
            update_account_settings(self.user, {"language_proficiencies": new_value})
            self.assert_user_setting_event_emitted(setting='language_proficiencies', old=old_value, new=new_value)
            self.reset_tracker()

        # Change language_proficiencies and verify events are fired.
        verify_event_emitted([{"code": "en"}], [])
        verify_event_emitted([{"code": "en"}, {"code": "fr"}], [{"code": "en"}])
        # Note that events are fired even if there has been no actual change.
        verify_event_emitted([{"code": "en"}, {"code": "fr"}], [{"code": "en"}, {"code": "fr"}])
        verify_event_emitted([], [{"code": "en"}, {"code": "fr"}])


@patch('openedx.core.djangoapps.user_api.accounts.image_helpers._PROFILE_IMAGE_SIZES', [50, 10])
@patch.dict(
    'openedx.core.djangoapps.user_api.accounts.image_helpers.PROFILE_IMAGE_SIZES_MAP', {'full': 50, 'small': 10}, clear=True
)
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Account APIs are only supported in LMS')
class AccountSettingsOnCreationTest(TestCase):
    # pylint: disable=missing-docstring

    USERNAME = u'frank-underwood'
    PASSWORD = u'ṕáśśẃőŕd'
    EMAIL = u'frank+underwood@example.com'

    def test_create_account(self):
        # Create a new account, which should have empty account settings by default.
        create_account(self.USERNAME, self.PASSWORD, self.EMAIL)

        # Retrieve the account settings
        user = User.objects.get(username=self.USERNAME)
        account_settings = get_account_settings(user)

        # Expect a date joined field but remove it to simplify the following comparison
        self.assertIsNotNone(account_settings['date_joined'])
        del account_settings['date_joined']

        # Expect all the values to be defaulted
        self.assertEqual(account_settings, {
            'username': self.USERNAME,
            'email': self.EMAIL,
            'name': u'',
            'gender': None,
            'goals': None,
            'is_active': False,
            'level_of_education': None,
            'mailing_address': None,
            'year_of_birth': None,
            'country': None,
            'bio': None,
            'profile_image': {
                'has_image': False,
                'image_url_full': '/static/default_50.png',
                'image_url_small': '/static/default_10.png',
            },
            'requires_parental_consent': True,
            'language_proficiencies': [],
        })


@ddt.ddt
class AccountCreationActivationAndPasswordChangeTest(TestCase):

    USERNAME = u'frank-underwood'
    PASSWORD = u'ṕáśśẃőŕd'
    EMAIL = u'frank+underwood@example.com'

    ORIG_HOST = 'example.com'
    IS_SECURE = False

    INVALID_USERNAMES = [
        None,
        u'',
        u'a',
        u'a' * (USERNAME_MAX_LENGTH + 1),
        u'invalid_symbol_@',
        u'invalid-unicode_fŕáńḱ',
    ]

    INVALID_EMAILS = [
        None,
        u'',
        u'a',
        'no_domain',
        'no+domain',
        '@',
        '@domain.com',
        'test@no_extension',
        u'fŕáńḱ@example.com',
        u'frank@éxáḿṕĺé.ćőḿ',

        # Long email -- subtract the length of the @domain
        # except for one character (so we exceed the max length limit)
        u'{user}@example.com'.format(
            user=(u'e' * (EMAIL_MAX_LENGTH - 11))
        )
    ]

    INVALID_PASSWORDS = [
        None,
        u'',
        u'a',
        u'a' * (PASSWORD_MAX_LENGTH + 1)
    ]

    def test_activate_account(self):
        # Create the account, which is initially inactive
        activation_key = create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        user = User.objects.get(username=self.USERNAME)
        account = get_account_settings(user)
        self.assertEqual(self.USERNAME, account["username"])
        self.assertEqual(self.EMAIL, account["email"])
        self.assertFalse(account["is_active"])

        # Activate the account and verify that it is now active
        activate_account(activation_key)
        account = get_account_settings(user)
        self.assertTrue(account['is_active'])

    def test_create_account_duplicate_username(self):
        create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        with self.assertRaises(AccountUserAlreadyExists):
            create_account(self.USERNAME, self.PASSWORD, 'different+email@example.com')

    # Email uniqueness constraints were introduced in a database migration,
    # which we disable in the unit tests to improve the speed of the test suite.
    @unittest.skipUnless(settings.SOUTH_TESTS_MIGRATE, "South migrations required")
    def test_create_account_duplicate_email(self):
        create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        with self.assertRaises(AccountUserAlreadyExists):
            create_account('different_user', self.PASSWORD, self.EMAIL)

    def test_username_too_long(self):
        long_username = 'e' * (USERNAME_MAX_LENGTH + 1)
        with self.assertRaises(AccountUsernameInvalid):
            create_account(long_username, self.PASSWORD, self.EMAIL)

    @raises(AccountEmailInvalid)
    @ddt.data(*INVALID_EMAILS)
    def test_create_account_invalid_email(self, invalid_email):
        create_account(self.USERNAME, self.PASSWORD, invalid_email)

    @raises(AccountPasswordInvalid)
    @ddt.data(*INVALID_PASSWORDS)
    def test_create_account_invalid_password(self, invalid_password):
        create_account(self.USERNAME, invalid_password, self.EMAIL)

    @raises(AccountPasswordInvalid)
    def test_create_account_username_password_equal(self):
        # Username and password cannot be the same
        create_account(self.USERNAME, self.USERNAME, self.EMAIL)

    @raises(AccountRequestError)
    @ddt.data(*INVALID_USERNAMES)
    def test_create_account_invalid_username(self, invalid_username):
        create_account(invalid_username, self.PASSWORD, self.EMAIL)

    @raises(UserNotAuthorized)
    def test_activate_account_invalid_key(self):
        activate_account(u'invalid')

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in LMS')
    def test_request_password_change(self):
        # Create and activate an account
        activation_key = create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        activate_account(activation_key)

        # Request a password change
        request_password_change(self.EMAIL, self.ORIG_HOST, self.IS_SECURE)

        # Verify that one email message has been sent
        self.assertEqual(len(mail.outbox), 1)

        # Verify that the body of the message contains something that looks
        # like an activation link
        email_body = mail.outbox[0].body
        result = re.search('(?P<url>https?://[^\s]+)', email_body)
        self.assertIsNot(result, None)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in LMS')
    def test_request_password_change_invalid_user(self):
        with self.assertRaises(UserNotFound):
            request_password_change(self.EMAIL, self.ORIG_HOST, self.IS_SECURE)

        # Verify that no email messages have been sent
        self.assertEqual(len(mail.outbox), 0)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in LMS')
    def test_request_password_change_inactive_user(self):
        # Create an account, but do not activate it
        create_account(self.USERNAME, self.PASSWORD, self.EMAIL)

        request_password_change(self.EMAIL, self.ORIG_HOST, self.IS_SECURE)

        # Verify that the activation email was still sent
        self.assertEqual(len(mail.outbox), 1)

    def _assert_is_datetime(self, timestamp):
        if not timestamp:
            return False
        try:
            parse_datetime(timestamp)
        except ValueError:
            return False
        else:
            return True
