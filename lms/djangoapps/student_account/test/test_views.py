# -*- coding: utf-8 -*-
""" Tests for student account views. """

import re
from unittest import skipUnless
from urllib import urlencode

from mock import patch
import ddt
from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core import mail

from util.testing import UrlResetMixin
from user_api.api import account as account_api
from user_api.api import profile as profile_api
from util.bad_request_rate_limiter import BadRequestRateLimiter


@ddt.ddt
class StudentAccountViewTest(UrlResetMixin, TestCase):
    """ Tests for the student account views. """

    USERNAME = u"heisenberg"
    ALTERNATE_USERNAME = u"walt"
    OLD_PASSWORD = u"ḅḷüëṡḳÿ"
    NEW_PASSWORD = u"🄱🄸🄶🄱🄻🅄🄴"
    OLD_EMAIL = u"walter@graymattertech.com"
    NEW_EMAIL = u"walt@savewalterwhite.com"

    INVALID_ATTEMPTS = 100

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

    INVALID_KEY = u"123abc"

    @patch.dict(settings.FEATURES, {'ENABLE_NEW_DASHBOARD': True})
    def setUp(self):
        super(StudentAccountViewTest, self).setUp()

        # Create/activate a new account
        activation_key = account_api.create_account(self.USERNAME, self.OLD_PASSWORD, self.OLD_EMAIL)
        account_api.activate_account(activation_key)

        # Login
        result = self.client.login(username=self.USERNAME, password=self.OLD_PASSWORD)
        self.assertTrue(result)

    def test_index(self):
        response = self.client.get(reverse('account_index'))
        self.assertContains(response, "Student Account")

    def test_email_change(self):
        response = self._change_email(self.NEW_EMAIL, self.OLD_PASSWORD)
        self.assertEquals(response.status_code, 200)

        # Verify that the email associated with the account remains unchanged
        profile_info = profile_api.profile_info(self.USERNAME)
        self.assertEquals(profile_info['email'], self.OLD_EMAIL)

        # Check that an email was sent with the activation key
        self.assertEqual(len(mail.outbox), 1)
        self._assert_email(
            mail.outbox[0],
            [self.NEW_EMAIL],
            u"Email Change Request",
            u"There was recently a request to change the email address"
        )

        # Retrieve the activation key from the email
        email_body = mail.outbox[0].body
        result = re.search('/email/confirmation/([^ \n]+)', email_body)
        self.assertIsNot(result, None)
        activation_key = result.group(1)

        # Attempt to activate the email
        response = self.client.get(reverse('email_change_confirm', kwargs={'key': activation_key}))
        self.assertEqual(response.status_code, 200)

        # Verify that the email was changed
        profile_info = profile_api.profile_info(self.USERNAME)
        self.assertEquals(profile_info['email'], self.NEW_EMAIL)

        # Verify that notification emails were sent
        self.assertEqual(len(mail.outbox), 2)
        self._assert_email(
            mail.outbox[1],
            [self.OLD_EMAIL, self.NEW_EMAIL],
            u"Email Change Successful",
            u"You successfully changed the email address"
        )

    def test_email_change_wrong_password(self):
        response = self._change_email(self.NEW_EMAIL, "wrong password")
        self.assertEqual(response.status_code, 401)

    def test_email_change_request_no_user(self):
        # Patch account API to raise an internal error when an email change is requested
        with patch('student_account.views.account_api.request_email_change') as mock_call:
            mock_call.side_effect = account_api.AccountUserNotFound
            response = self._change_email(self.NEW_EMAIL, self.OLD_PASSWORD)

        self.assertEquals(response.status_code, 400)

    def test_email_change_request_email_taken_by_active_account(self):
        # Create/activate a second user with the new email
        activation_key = account_api.create_account(self.ALTERNATE_USERNAME, self.OLD_PASSWORD, self.NEW_EMAIL)
        account_api.activate_account(activation_key)

        # Request to change the original user's email to the email now used by the second user
        response = self._change_email(self.NEW_EMAIL, self.OLD_PASSWORD)
        self.assertEquals(response.status_code, 409)

    def test_email_change_request_email_taken_by_inactive_account(self):
        # Create a second user with the new email, but don't active them
        account_api.create_account(self.ALTERNATE_USERNAME, self.OLD_PASSWORD, self.NEW_EMAIL)

        # Request to change the original user's email to the email used by the inactive user
        response = self._change_email(self.NEW_EMAIL, self.OLD_PASSWORD)
        self.assertEquals(response.status_code, 200)

    @ddt.data(*INVALID_EMAILS)
    def test_email_change_request_email_invalid(self, invalid_email):
        # Request to change the user's email to an invalid address
        response = self._change_email(invalid_email, self.OLD_PASSWORD)
        self.assertEquals(response.status_code, 400)

    def test_email_change_confirmation(self):
        # Get an email change activation key
        activation_key = account_api.request_email_change(self.USERNAME, self.NEW_EMAIL, self.OLD_PASSWORD)

        # Follow the link sent in the confirmation email
        response = self.client.get(reverse('email_change_confirm', kwargs={'key': activation_key}))
        self.assertContains(response, "Email change successful")

        # Verify that the email associated with the account has changed
        profile_info = profile_api.profile_info(self.USERNAME)
        self.assertEquals(profile_info['email'], self.NEW_EMAIL)

    def test_email_change_confirmation_invalid_key(self):
        # Visit the confirmation page with an invalid key
        response = self.client.get(reverse('email_change_confirm', kwargs={'key': self.INVALID_KEY}))
        self.assertContains(response, "Something went wrong")

        # Verify that the email associated with the account has not changed
        profile_info = profile_api.profile_info(self.USERNAME)
        self.assertEquals(profile_info['email'], self.OLD_EMAIL)

    def test_email_change_confirmation_email_already_exists(self):
        # Get an email change activation key
        email_activation_key = account_api.request_email_change(self.USERNAME, self.NEW_EMAIL, self.OLD_PASSWORD)

        # Create/activate a second user with the new email
        account_activation_key = account_api.create_account(self.ALTERNATE_USERNAME, self.OLD_PASSWORD, self.NEW_EMAIL)
        account_api.activate_account(account_activation_key)

        # Follow the link sent to the original user
        response = self.client.get(reverse('email_change_confirm', kwargs={'key': email_activation_key}))
        self.assertContains(response, "address you wanted to use is already used")

        # Verify that the email associated with the original account has not changed
        profile_info = profile_api.profile_info(self.USERNAME)
        self.assertEquals(profile_info['email'], self.OLD_EMAIL)

    def test_email_change_confirmation_internal_error(self):
        # Get an email change activation key
        activation_key = account_api.request_email_change(self.USERNAME, self.NEW_EMAIL, self.OLD_PASSWORD)

        # Patch account API to return an internal error
        with patch('student_account.views.account_api.confirm_email_change') as mock_call:
            mock_call.side_effect = account_api.AccountInternalError
            response = self.client.get(reverse('email_change_confirm', kwargs={'key': activation_key}))

        self.assertContains(response, "Something went wrong")

    def test_email_change_request_missing_email_param(self):
        response = self._change_email(None, self.OLD_PASSWORD)
        self.assertEqual(response.status_code, 400)

    def test_email_change_request_missing_password_param(self):
        response = self._change_email(self.OLD_EMAIL, None)
        self.assertEqual(response.status_code, 400)

    @skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in LMS')
    def test_password_change(self):
        # Request a password change while logged in, simulating
        # use of the password reset link from the account page
        response = self._change_password()
        self.assertEqual(response.status_code, 200)

        # Check that an email was sent
        self.assertEqual(len(mail.outbox), 1)

        # Retrieve the activation link from the email body
        email_body = mail.outbox[0].body
        result = re.search('(?P<url>https?://[^\s]+)', email_body)
        self.assertIsNot(result, None)
        activation_link = result.group('url')

        # Visit the activation link
        response = self.client.get(activation_link)
        self.assertEqual(response.status_code, 200)

        # Submit a new password and follow the redirect to the success page
        response = self.client.post(
            activation_link,
            # These keys are from the form on the current password reset confirmation page.
            {'new_password1': self.NEW_PASSWORD, 'new_password2': self.NEW_PASSWORD},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your password has been set.")

        # Log the user out to clear session data
        self.client.logout()

        # Verify that the new password can be used to log in
        result = self.client.login(username=self.USERNAME, password=self.NEW_PASSWORD)
        self.assertTrue(result)

        # Try reusing the activation link to change the password again
        response = self.client.post(
            activation_link,
            {'new_password1': self.OLD_PASSWORD, 'new_password2': self.OLD_PASSWORD},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The password reset link was invalid, possibly because the link has already been used.")

        self.client.logout()

        # Verify that the old password cannot be used to log in
        result = self.client.login(username=self.USERNAME, password=self.OLD_PASSWORD)
        self.assertFalse(result)

        # Verify that the new password continues to be valid
        result = self.client.login(username=self.USERNAME, password=self.NEW_PASSWORD)
        self.assertTrue(result)


    @ddt.data(True, False)
    def test_password_change_logged_out(self, send_email):
        # Log the user out
        self.client.logout()

        # Request a password change while logged out, simulating
        # use of the password reset link from the login page
        if send_email:
            response = self._change_password(email=self.OLD_EMAIL)
            self.assertEqual(response.status_code, 200)
        else:
            # Don't send an email in the POST data, simulating
            # its (potentially accidental) omission in the POST
            # data sent from the login page
            response = self._change_password()
            self.assertEqual(response.status_code, 400)

    def test_password_change_inactive_user(self):
        # Log out the user created during test setup
        self.client.logout()

        # Create a second user, but do not activate it
        account_api.create_account(self.ALTERNATE_USERNAME, self.OLD_PASSWORD, self.NEW_EMAIL)
        
        # Send the view the email address tied to the inactive user
        response = self._change_password(email=self.NEW_EMAIL)
        self.assertEqual(response.status_code, 400)

    def test_password_change_no_user(self):
        # Log out the user created during test setup
        self.client.logout()
        
        # Send the view an email address not tied to any user
        response = self._change_password(email=self.NEW_EMAIL)
        self.assertEqual(response.status_code, 400)

    def test_password_change_rate_limited(self):
        # Log out the user created during test setup, to prevent the view from
        # selecting the logged-in user's email address over the email provided
        # in the POST data
        self.client.logout()

        # Make many consecutive bad requests in an attempt to trigger the rate limiter
        for attempt in xrange(self.INVALID_ATTEMPTS):
            self._change_password(email=self.NEW_EMAIL)
        
        response = self._change_password(email=self.NEW_EMAIL)
        self.assertEqual(response.status_code, 403)

    @ddt.data(
        ('get', 'account_index', []),
        ('post', 'email_change_request', []),
        ('get', 'email_change_confirm', [123])
    )
    @ddt.unpack
    def test_require_login(self, method, url_name, args):
        # Access the page while logged out
        self.client.logout()
        url = reverse(url_name, args=args)
        response = getattr(self.client, method)(url, follow=True)

        # Should have been redirected to the login page
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertIn('accounts/login?next=', response.redirect_chain[0][0])

    @ddt.data(
        ('get', 'account_index', []),
        ('post', 'email_change_request', []),
        ('get', 'email_change_confirm', [123]),
        ('post', 'password_change_request', []),
    )
    @ddt.unpack
    def test_require_http_method(self, correct_method, url_name, args):
        wrong_methods = {'get', 'put', 'post', 'head', 'options', 'delete'} - {correct_method}
        url = reverse(url_name, args=args)

        for method in wrong_methods:
            response = getattr(self.client, method)(url)
            self.assertEqual(response.status_code, 405)

    def _assert_email(self, email, expected_to, expected_subject, expected_body):
        """Check whether an email has the correct properties. """
        self.assertEqual(email.to, expected_to)
        self.assertIn(expected_subject, email.subject)
        self.assertIn(expected_body, email.body)

    def _change_email(self, new_email, password):
        """Request to change the user's email. """
        data = {}

        if new_email is not None:
            data['email'] = new_email
        if password is not None:
            # We can't pass a Unicode object to urlencode, so we encode the Unicode object
            data['password'] = password.encode('utf-8')

        return self.client.post(path=reverse('email_change_request'), data=data)

    def _change_password(self, email=None):
        """Request to change the user's password. """
        data = {}

        if email:
            data['email'] = email

        return self.client.post(path=reverse('password_change_request'), data=data)
