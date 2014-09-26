# -*- coding: utf-8 -*-
""" Tests for student account views. """

import re
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


@ddt.ddt
class StudentAccountViewTest(UrlResetMixin, TestCase):
    """ Tests for the student account views. """

    USERNAME = u"heisenberg"
    ALTERNATE_USERNAME = u"walt"
    PASSWORD = u"ḅḷüëṡḳÿ"
    OLD_EMAIL = u"walter@graymattertech.com"
    NEW_EMAIL = u"walt@savewalterwhite.com"

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
        activation_key = account_api.create_account(self.USERNAME, self.PASSWORD, self.OLD_EMAIL)
        account_api.activate_account(activation_key)

        # Login
        result = self.client.login(username=self.USERNAME, password=self.PASSWORD)
        self.assertTrue(result)

    def test_index(self):
        response = self.client.get(reverse('account_index'))
        self.assertContains(response, "Student Account")

    def test_change_email(self):
        response = self._change_email(self.NEW_EMAIL, self.PASSWORD)
        self.assertEquals(response.status_code, 204)

        # Verify that the email associated with the account remains unchanged
        profile_info = profile_api.profile_info(self.USERNAME)
        self.assertEquals(profile_info['email'], self.OLD_EMAIL)

        # Check that an email was sent with the activation key
        self.assertEqual(len(mail.outbox), 1)
        self._assert_email(
            mail.outbox[0],
            [self.NEW_EMAIL],
            u'Email Change Request',
            u'There was recently a request to change the email address'
        )

        # Retrieve the activation key from the email
        email_body = mail.outbox[0].body
        result = re.search('/email_change_confirm/([^ \n]+)', email_body)
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
            u'Email Change Successful',
            u'You successfully changed the email address'
        )

    def test_email_change_wrong_password(self):
        response = self._change_email(self.NEW_EMAIL, "wrong password")
        self.assertEqual(response.status_code, 401)

    def test_email_change_request_internal_error(self):
        # Patch account API to raise an internal error when an email change is requested
        with patch('student_account.views.account_api.request_email_change') as mock_call:
            mock_call.side_effect = account_api.AccountUserNotFound
            response = self._change_email(self.NEW_EMAIL, self.PASSWORD)

        self.assertEquals(response.status_code, 500)

    def test_email_change_request_email_taken_by_active_account(self):
        # Create/activate a second user with the new email
        activation_key = account_api.create_account(self.ALTERNATE_USERNAME, self.PASSWORD, self.NEW_EMAIL)
        account_api.activate_account(activation_key)

        # Request to change the original user's email to the email now used by the second user
        response = self._change_email(self.NEW_EMAIL, self.PASSWORD)
        self.assertEquals(response.status_code, 409)

    def test_email_change_request_email_taken_by_inactive_account(self):
        # Create a second user with the new email, but don't active them
        account_api.create_account(self.ALTERNATE_USERNAME, self.PASSWORD, self.NEW_EMAIL)

        # Request to change the original user's email to the email used by the inactive user
        response = self._change_email(self.NEW_EMAIL, self.PASSWORD)
        self.assertEquals(response.status_code, 204)

    @ddt.data(*INVALID_EMAILS)
    def test_email_change_request_email_invalid(self, invalid_email):
        # Request to change the user's email to an invalid address
        response = self._change_email(invalid_email, self.PASSWORD)
        self.assertEquals(response.status_code, 400)

    def test_email_change_confirmation(self):
        # Get an email change activation key
        activation_key = account_api.request_email_change(self.USERNAME, self.NEW_EMAIL, self.PASSWORD)

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
        email_activation_key = account_api.request_email_change(self.USERNAME, self.NEW_EMAIL, self.PASSWORD)

        # Create/activate a second user with the new email
        account_activation_key = account_api.create_account(self.ALTERNATE_USERNAME, self.PASSWORD, self.NEW_EMAIL)
        account_api.activate_account(account_activation_key)

        # Follow the link sent to the original user
        response = self.client.get(reverse('email_change_confirm', kwargs={'key': email_activation_key}))
        self.assertContains(response, "address you wanted to use is already used")

        # Verify that the email associated with the original account has not changed
        profile_info = profile_api.profile_info(self.USERNAME)
        self.assertEquals(profile_info['email'], self.OLD_EMAIL)

    def test_email_change_confirmation_internal_error(self):
        # Get an email change activation key
        activation_key = account_api.request_email_change(self.USERNAME, self.NEW_EMAIL, self.PASSWORD)

        # Patch account API to return an internal error
        with patch('student_account.views.account_api.confirm_email_change') as mock_call:
            mock_call.side_effect = account_api.AccountInternalError
            response = self.client.get(reverse('email_change_confirm', kwargs={'key': activation_key}))

        self.assertContains(response, "Something went wrong")

    def test_change_email_request_missing_email_param(self):
        response = self._change_email(None, self.PASSWORD)
        self.assertEqual(response.status_code, 400)

    def test_change_email_request_missing_password_param(self):
        response = self._change_email(self.OLD_EMAIL, None)
        self.assertEqual(response.status_code, 400)

    @ddt.data(
        ('get', 'account_index'),
        ('put', 'email_change_request')
    )
    @ddt.unpack
    def test_require_login(self, method, url_name):
        # Access the page while logged out
        self.client.logout()
        url = reverse(url_name)
        response = getattr(self.client, method)(url, follow=True)

        # Should have been redirected to the login page
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertIn('accounts/login?next=', response.redirect_chain[0][0])

    @ddt.data(
        ('get', 'account_index'),
        ('put', 'email_change_request')
    )
    @ddt.unpack
    def test_require_http_method(self, correct_method, url_name):
        wrong_methods = {'get', 'put', 'post', 'head', 'options', 'delete'} - {correct_method}
        url = reverse(url_name)

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
            data['new_email'] = new_email
        if password is not None:
            # We can't pass a Unicode object to urlencode, so we encode the Unicode object
            data['password'] = password.encode('utf-8')

        response = self.client.put(
            path=reverse('email_change_request'),
            data=urlencode(data),
            content_type='application/x-www-form-urlencoded'
        )

        return response
