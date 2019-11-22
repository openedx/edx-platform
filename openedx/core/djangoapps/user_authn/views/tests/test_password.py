# -*- coding: utf-8 -*-
"""
Tests for user authorization password-related functionality.
"""
import re
from mock import Mock, patch

from django.core import mail
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import RequestFactory

from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from openedx.core.djangoapps.user_api.accounts.tests.test_api import CreateAccountMixin
from openedx.core.djangoapps.user_api.accounts.api import (
    activate_account,
)
from openedx.core.djangoapps.user_api.errors import UserNotFound
from openedx.core.djangoapps.user_authn.views.password_reset import request_password_change
from openedx.core.djangolib.testing.utils import skip_unless_lms

from student.models import Registration


class TestRequestPasswordChange(CreateAccountMixin, TestCase):
    """
    Tests for users who request a password change.
    """

    USERNAME = u'claire-underwood'
    PASSWORD = u'ṕáśśẃőŕd'
    EMAIL = u'claire+underwood@example.com'

    IS_SECURE = False

    def get_activation_key(self, user):
        registration = Registration.objects.get(user=user)
        return registration.activation_key

    @skip_unless_lms
    def test_request_password_change(self):
        # Create and activate an account
        self.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        self.assertEqual(len(mail.outbox), 1)

        user = User.objects.get(username=self.USERNAME)
        activation_key = self.get_activation_key(user)
        activate_account(activation_key)

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

        # Verify that the activation email was still sent
        self.assertEqual(len(mail.outbox), 2)
