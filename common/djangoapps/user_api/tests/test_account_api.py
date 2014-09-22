# -*- coding: utf-8 -*-
""" Tests for the account API. """

from nose.tools import raises
import ddt
from django.test import TestCase
from user_api.api import account as account_api


@ddt.ddt
class AccountApiTest(TestCase):

    USERNAME = u"frank_under-wood"
    PASSWORD = u"ṕáśśẃőŕd"
    EMAIL = u"frank@example.com"

    INVALID_USERNAMES = [
        None,
        u"",
        u"a",
        u"a" * (account_api.USERNAME_MAX_LENGTH + 1),
        u"invalid_symbol_@",
        u"invalid-unicode_fŕáńḱ",
    ]

    INVALID_EMAILS = [
        None,
        u"",
        u"a",
        "no_domain",
        "no+domain",
        "@",
        "@domain.com",
        "test@no_extension",

        # Long email -- subtract the length of the @domain
        # except for one character (so we exceed the max length limit)
        u"{user}@example.com".format(
            user=(u'e' * (account_api.EMAIL_MAX_LENGTH - 11))
        )
    ]

    INVALID_PASSWORDS = [
        None,
        u"",
        u"a",
        u"a" * (account_api.PASSWORD_MAX_LENGTH + 1)
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

    def test_change_email(self):
        # Request an email change
        account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        activation_key = account_api.request_email_change(
            self.USERNAME, u"new+email@example.com", self.PASSWORD
        )

        # Verify that the email has not yet changed
        account = account_api.account_info(self.USERNAME)
        self.assertEqual(account['email'], self.EMAIL)

        # Confirm the change, using the activation code
        old_email, new_email = account_api.confirm_email_change(activation_key)
        self.assertEqual(old_email, self.EMAIL)
        self.assertEqual(new_email, u"new+email@example.com")

        # Verify that the email is changed
        account = account_api.account_info(self.USERNAME)
        self.assertEqual(account['email'], u"new+email@example.com")

    def test_confirm_email_change_repeat(self):
        account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        activation_key = account_api.request_email_change(
            self.USERNAME, u"new+email@example.com", self.PASSWORD
        )

        # Confirm the change once
        account_api.confirm_email_change(activation_key)

        # Confirm the change again
        # The activation code should be single-use
        # so this should raise an error.
        with self.assertRaises(account_api.AccountNotAuthorized):
            account_api.confirm_email_change(activation_key)

    def test_create_account_duplicate_username(self):
        account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        with self.assertRaises(account_api.AccountUserAlreadyExists):
            account_api.create_account(self.USERNAME, self.PASSWORD, 'different+email@example.com')

    def test_create_account_duplicate_email(self):
        account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        with self.assertRaises(account_api.AccountUserAlreadyExists):
            account_api.create_account("different_user", self.PASSWORD, self.EMAIL)

    def test_username_too_long(self):
        long_username = 'e' * (account_api.USERNAME_MAX_LENGTH + 1)
        with self.assertRaises(account_api.AccountUsernameInvalid):
            account_api.create_account(long_username, self.PASSWORD, self.EMAIL)

    def test_account_info_no_user(self):
        self.assertIs(account_api.account_info("does_not_exist"), None)

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
        account_api.activate_account(u"invalid")

    @raises(account_api.AccountUserNotFound)
    def test_request_email_change_no_user(self):
        account_api.request_email_change(u"no_such_user", self.EMAIL, self.PASSWORD)

    @ddt.data(*INVALID_EMAILS)
    def test_request_email_change_invalid_email(self, invalid_email):
        # Create an account with a valid email address
        account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)

        # Attempt to change the account to an invalid email
        with self.assertRaises(account_api.AccountEmailInvalid):
            account_api.request_email_change(self.USERNAME, invalid_email, self.PASSWORD)

    def test_request_email_change_already_exists(self):
        # Create two accounts
        account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        account_api.create_account(u"another_user", u"password", u"another+user@example.com")

        # Try to change the first user's email to the same as the second user's
        with self.assertRaises(account_api.AccountEmailAlreadyExists):
            account_api.request_email_change(self.USERNAME, u"another+user@example.com", self.PASSWORD)

    def test_request_email_change_same_address(self):
        account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)

        # Try to change the email address to the current address
        with self.assertRaises(account_api.AccountEmailAlreadyExists):
            account_api.request_email_change(self.USERNAME, self.EMAIL, self.PASSWORD)

    def test_request_email_change_wrong_password(self):
        account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)

        # Use the wrong password
        with self.assertRaises(account_api.AccountNotAuthorized):
            account_api.request_email_change(self.USERNAME, u"new+email@example.com", u"wrong password")

    def test_confirm_email_change_invalid_activation_key(self):
        account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        account_api.request_email_change(self.USERNAME, u"new+email@example.com", self.PASSWORD)

        with self.assertRaises(account_api.AccountNotAuthorized):
            account_api.confirm_email_change(u"invalid")

    def test_confirm_email_change_no_request_pending(self):
        account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)

    def test_confirm_email_already_exists(self):
        account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)

        # Request a change
        activation_key = account_api.request_email_change(
            self.USERNAME, u"new+email@example.com", self.PASSWORD
        )

        # Another use takes the email before we confirm the change
        account_api.create_account(u"other_user", u"password", u"new+email@example.com")

        # When we try to confirm our change, we get an error because the email is taken
        with self.assertRaises(account_api.AccountEmailAlreadyExists):
            account_api.confirm_email_change(activation_key)

        # Verify that the email was NOT changed
        self.assertEqual(account_api.account_info(self.USERNAME)['email'], self.EMAIL)
