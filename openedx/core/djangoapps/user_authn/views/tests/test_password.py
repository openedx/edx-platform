# -*- coding: utf-8 -*-
"""
Tests for user authorization password-related functionality.
"""
import json
import logging
import re
from datetime import datetime, timedelta

import ddt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse
from freezegun import freeze_time
from mock import Mock, patch
from oauth2_provider.models import AccessToken as dot_access_token
from oauth2_provider.models import RefreshToken as dot_refresh_token
from pytz import UTC
from testfixtures import LogCapture

from openedx.core.djangoapps.oauth_dispatch.tests import factories as dot_factories
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from openedx.core.djangoapps.user_api.accounts.tests.test_api import CreateAccountMixin
from openedx.core.djangoapps.user_api.errors import UserAPIInternalError, UserNotFound
from openedx.core.djangoapps.user_authn.views.password_reset import request_password_change
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms

LOGGER_NAME = 'audit'
User = get_user_model()  # pylint:disable=invalid-name


class TestRequestPasswordChange(CreateAccountMixin, TestCase):
    """
    Tests for users who request a password change.
    """
    USERNAME = u'claire-underwood'
    PASSWORD = u'ṕáśśẃőŕd'
    EMAIL = u'claire+underwood@example.com'

    IS_SECURE = False

    @skip_unless_lms
    def test_request_password_change(self):
        # Create and activate an account
        self.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        self.assertEqual(len(mail.outbox), 1)

        request = RequestFactory().post('/password')
        request.user = Mock()
        request.site = SiteFactory()

        with patch('crum.get_current_request', return_value=request):
            # Request a password change
            request_password_change(self.EMAIL, self.IS_SECURE)

        # Verify that a new email message has been sent
        self.assertEqual(len(mail.outbox), 2)

        # Verify that the body of the message contains something that looks
        # like an activation link
        email_body = mail.outbox[0].body
        result = re.search(r'(?P<url>https?://[^\s]+)', email_body)
        self.assertIsNot(result, None)

    @skip_unless_lms
    def test_request_password_change_invalid_user(self):
        with self.assertRaises(UserNotFound):
            request_password_change(self.EMAIL, self.IS_SECURE)

        # Verify that no email messages have been sent
        self.assertEqual(len(mail.outbox), 0)

    @skip_unless_lms
    def test_request_password_change_inactive_user(self):
        # Create an account, but do not activate it
        self.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        self.assertEqual(len(mail.outbox), 1)

        request = RequestFactory().post('/password')
        request.user = Mock()
        request.site = SiteFactory()

        with patch('crum.get_current_request', return_value=request):
            request_password_change(self.EMAIL, self.IS_SECURE)

        # Verify that the password change email was still sent
        self.assertEqual(len(mail.outbox), 2)


@skip_unless_lms
@ddt.ddt
class TestPasswordChange(CreateAccountMixin, CacheIsolationTestCase):
    """ Tests for views that change the user's password. """

    USERNAME = u"heisenberg"
    ALTERNATE_USERNAME = u"walt"
    OLD_PASSWORD = u"ḅḷüëṡḳÿ"
    NEW_PASSWORD = u"B🄸🄶B🄻🅄🄴"
    OLD_EMAIL = u"walter@graymattertech.com"
    NEW_EMAIL = u"walt@savewalterwhite.com"

    INVALID_KEY = u"123abc"

    ENABLED_CACHES = ['default']

    def setUp(self):
        super(TestPasswordChange, self).setUp()

        self.create_account(self.USERNAME, self.OLD_PASSWORD, self.OLD_EMAIL)
        result = self.client.login(username=self.USERNAME, password=self.OLD_PASSWORD)
        self.assertTrue(result)
        mail.outbox = []
        cache.clear()

    def test_password_change(self):
        # Request a password change while logged in, simulating
        # use of the password reset link from the account page
        response = self._change_password()
        self.assertEqual(response.status_code, 200)

        # Check that an email was sent
        self.assertEqual(len(mail.outbox), 1)

        # Retrieve the activation link from the email body
        email_body = mail.outbox[0].body
        result = re.search(r'(?P<url>https?://[^\s]+)', email_body)
        self.assertIsNot(result, None)
        activation_link = result.group('url')

        # Visit the activation link
        response = self.client.get(activation_link)
        self.assertEqual(response.status_code, 302)

        # Visit the redirect link
        _ = self.client.get(response.url)

        # Submit a new password and follow the redirect to the success page
        response = self.client.post(
            response.url,
            # These keys are from the form on the current password reset confirmation page.
            {'new_password1': self.NEW_PASSWORD, 'new_password2': self.NEW_PASSWORD},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your password has been reset.")

        # Log the user out to clear session data
        self.client.logout()

        # Verify that the new password can be used to log in
        login_api_url = reverse('login_api')
        response = self.client.post(login_api_url, {'email': self.OLD_EMAIL, 'password': self.NEW_PASSWORD})
        assert response.status_code == 200
        response_dict = json.loads(response.content.decode('utf-8'))
        assert response_dict['success']

        # Try reusing the activation link to change the password again
        # Visit the activation link again.
        response = self.client.get(activation_link)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This password reset link is invalid. It may have been used already.")

        self.client.logout()

        # Verify that the old password cannot be used to log in
        result = self.client.login(username=self.USERNAME, password=self.OLD_PASSWORD)
        self.assertFalse(result)

        # Verify that the new password continues to be valid
        response = self.client.post(login_api_url, {'email': self.OLD_EMAIL, 'password': self.NEW_PASSWORD})
        assert response.status_code == 200
        response_dict = json.loads(response.content.decode('utf-8'))
        assert response_dict['success']

    def test_password_change_failure(self):
        with patch(
            'openedx.core.djangoapps.user_authn.views.password_reset.request_password_change',
            side_effect=UserAPIInternalError,
        ):
            self._change_password()
            self.assertRaises(UserAPIInternalError)

    @patch.dict(settings.FEATURES, {'ENABLE_PASSWORD_RESET_FAILURE_EMAIL': True})
    def test_password_reset_failure_email(self):
        """Test that a password reset failure email notification is sent, when enabled."""
        # Log the user out
        self.client.logout()

        bad_email = 'doesnotexist@example.com'
        response = self._change_password(email=bad_email)
        self.assertEqual(response.status_code, 200)

        # Check that an email was sent
        self.assertEqual(len(mail.outbox), 1)

        # Verify that the body contains the failed password reset message
        sent_message = mail.outbox[0]
        text_body = sent_message.body
        html_body = sent_message.alternatives[0][0]

        for email_body in [text_body, html_body]:
            msg = u'However, there is currently no user account associated with your email address: {email}'.format(
                email=bad_email
            )

            assert u'reset for your user account at {}'.format(settings.PLATFORM_NAME) in email_body
            assert 'password_reset_confirm' not in email_body, 'The link should not be added if user was not found'
            assert msg in email_body

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

    def test_access_token_invalidation_logged_out(self):
        self.client.logout()
        user = User.objects.get(email=self.OLD_EMAIL)
        self._create_dot_tokens(user)
        response = self._change_password(email=self.OLD_EMAIL)
        self.assertEqual(response.status_code, 200)
        self._assert_access_token_destroyed(user)

    def test_access_token_invalidation_logged_in(self):
        user = User.objects.get(email=self.OLD_EMAIL)
        self._create_dot_tokens(user)
        response = self._change_password()
        self.assertEqual(response.status_code, 200)
        self._assert_access_token_destroyed(user)

    def test_password_change_inactive_user(self):
        # Log out the user created during test setup
        self.client.logout()

        # Create a second user, but do not activate it
        self.create_account(self.ALTERNATE_USERNAME, self.OLD_PASSWORD, self.NEW_EMAIL)
        mail.outbox = []

        # Send the view the email address tied to the inactive user
        response = self._change_password(email=self.NEW_EMAIL)

        # Expect that the activation email is still sent,
        # since the user may have lost the original activation email.
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

    def test_password_change_no_user(self):
        # Log out the user created during test setup
        self.client.logout()

        with LogCapture(LOGGER_NAME, level=logging.INFO) as logger:
            # Send the view an email address not tied to any user
            response = self._change_password(email=self.NEW_EMAIL)
            self.assertEqual(response.status_code, 200)

            expected_logs = (
                (LOGGER_NAME, 'INFO', 'Password reset initiated for user {}.'.format(self.NEW_EMAIL)),
                (LOGGER_NAME, 'INFO', 'Invalid password reset attempt')
            )
            logger.check(*expected_logs)

    def test_password_change_rate_limited(self):
        """
        Tests that password reset requests are rate limited as expected.
        """
        # Log out the user created during test setup, to prevent the view from
        # selecting the logged-in user's email address over the email provided
        # in the POST data
        self.client.logout()
        for status in [200, 403]:
            response = self._change_password(email=self.NEW_EMAIL)
            self.assertEqual(response.status_code, status)

        # now reset the time to 1 min from now in future and change the email and
        # verify that it will allow another request from same IP
        reset_time = datetime.now(UTC) + timedelta(seconds=61)
        with freeze_time(reset_time):
            response = self._change_password(email=self.OLD_EMAIL)
            self.assertEqual(response.status_code, 200)

    @ddt.data(
        ('post', 'password_change_request', []),
    )
    @ddt.unpack
    def test_require_http_method(self, correct_method, url_name, args):
        wrong_methods = {'get', 'put', 'post', 'head', 'options', 'delete'} - {correct_method}
        url = reverse(url_name, args=args)

        for method in wrong_methods:
            response = getattr(self.client, method)(url)
            self.assertEqual(response.status_code, 405)

    def _change_password(self, email=None):
        """Request to change the user's password. """
        data = {}

        if email:
            data['email'] = email

        return self.client.post(path=reverse('password_change_request'), data=data)

    def _create_dot_tokens(self, user=None):
        """Create dot access token for given user if user provided else for default user."""
        if not user:
            user = User.objects.get(email=self.OLD_EMAIL)

        application = dot_factories.ApplicationFactory(user=user)
        access_token = dot_factories.AccessTokenFactory(user=user, application=application)
        dot_factories.RefreshTokenFactory(user=user, application=application, access_token=access_token)

    def _assert_access_token_destroyed(self, user):
        """Assert all access tokens are destroyed."""
        self.assertFalse(dot_access_token.objects.filter(user=user).exists())
        self.assertFalse(dot_refresh_token.objects.filter(user=user).exists())
