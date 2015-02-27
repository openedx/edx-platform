# -*- coding: utf-8 -*-
""" Tests for the account API. """

import re
from unittest import skipUnless

from nose.tools import raises
from mock import patch
import ddt
from dateutil.parser import parse as parse_datetime
from django.core import mail
from django.test import TestCase
from django.conf import settings

from ..api import account as account_api
from ..models import UserProfile


@ddt.ddt
class AccountApiTest(TestCase):

    USERNAME = u'frank-underwood'
    PASSWORD = u'ṕáśśẃőŕd'
    EMAIL = u'frank+underwood@example.com'

    ORIG_HOST = 'example.com'
    IS_SECURE = False

    INVALID_USERNAMES = [
        None,
        u'',
        u'a',
        u'a' * (account_api.USERNAME_MAX_LENGTH + 1),
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
            user=(u'e' * (account_api.EMAIL_MAX_LENGTH - 11))
        )
    ]

    INVALID_PASSWORDS = [
        None,
        u'',
        u'a',
        u'a' * (account_api.PASSWORD_MAX_LENGTH + 1)
    ]

    def test_activate_account(self):
        # Create the account, which is initially inactive
        activation_key = account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        account = account_api.account_info(self.USERNAME)
        self.assertEqual(account, {
            'username': self.USERNAME,
            'email': self.EMAIL,
            'is_active': False
        })

        # Activate the account and verify that it is now active
        account_api.activate_account(activation_key)
        account = account_api.account_info(self.USERNAME)
        self.assertTrue(account['is_active'])

    def test_create_account_duplicate_username(self):
        account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        with self.assertRaises(account_api.AccountUserAlreadyExists):
            account_api.create_account(self.USERNAME, self.PASSWORD, 'different+email@example.com')

    # Email uniqueness constraints were introduced in a database migration,
    # which we disable in the unit tests to improve the speed of the test suite.
    @skipUnless(settings.SOUTH_TESTS_MIGRATE, "South migrations required")
    def test_create_account_duplicate_email(self):
        account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        with self.assertRaises(account_api.AccountUserAlreadyExists):
            account_api.create_account('different_user', self.PASSWORD, self.EMAIL)

    def test_username_too_long(self):
        long_username = 'e' * (account_api.USERNAME_MAX_LENGTH + 1)
        with self.assertRaises(account_api.AccountUsernameInvalid):
            account_api.create_account(long_username, self.PASSWORD, self.EMAIL)

    def test_account_info_no_user(self):
        self.assertIs(account_api.account_info('does_not_exist'), None)

    @raises(account_api.AccountEmailInvalid)
    @ddt.data(*INVALID_EMAILS)
    def test_create_account_invalid_email(self, invalid_email):
        account_api.create_account(self.USERNAME, self.PASSWORD, invalid_email)

    @raises(account_api.AccountPasswordInvalid)
    @ddt.data(*INVALID_PASSWORDS)
    def test_create_account_invalid_password(self, invalid_password):
        account_api.create_account(self.USERNAME, invalid_password, self.EMAIL)

    @raises(account_api.AccountPasswordInvalid)
    def test_create_account_username_password_equal(self):
        # Username and password cannot be the same
        account_api.create_account(self.USERNAME, self.USERNAME, self.EMAIL)

    @raises(account_api.AccountRequestError)
    @ddt.data(*INVALID_USERNAMES)
    def test_create_account_invalid_username(self, invalid_username):
        account_api.create_account(invalid_username, self.PASSWORD, self.EMAIL)

    @raises(account_api.AccountNotAuthorized)
    def test_activate_account_invalid_key(self):
        account_api.activate_account(u'invalid')

    @skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in LMS')
    def test_request_password_change(self):
        # Create and activate an account
        activation_key = account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        account_api.activate_account(activation_key)

        # Request a password change
        account_api.request_password_change(self.EMAIL, self.ORIG_HOST, self.IS_SECURE)

        # Verify that one email message has been sent
        self.assertEqual(len(mail.outbox), 1)

        # Verify that the body of the message contains something that looks
        # like an activation link
        email_body = mail.outbox[0].body
        result = re.search('(?P<url>https?://[^\s]+)', email_body)
        self.assertIsNot(result, None)

    @skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in LMS')
    def test_request_password_change_invalid_user(self):
        with self.assertRaises(account_api.AccountUserNotFound):
            account_api.request_password_change(self.EMAIL, self.ORIG_HOST, self.IS_SECURE)

        # Verify that no email messages have been sent
        self.assertEqual(len(mail.outbox), 0)

    @skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in LMS')
    def test_request_password_change_inactive_user(self):
        # Create an account, but do not activate it
        account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)

        account_api.request_password_change(self.EMAIL, self.ORIG_HOST, self.IS_SECURE)

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
