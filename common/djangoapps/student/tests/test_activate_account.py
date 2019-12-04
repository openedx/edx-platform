"""Tests for account activation"""
from __future__ import absolute_import

import unittest
from uuid import uuid4

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from mock import patch

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.user_api.config.waffle import PREVENT_AUTH_USER_WRITES, SYSTEM_MAINTENANCE_MSG, waffle
from student.models import Registration
from student.tests.factories import UserFactory


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestActivateAccount(TestCase):
    """Tests for account creation"""

    def setUp(self):
        super(TestActivateAccount, self).setUp()
        self.username = "jack"
        self.email = "jack@fake.edx.org"
        self.password = "test-password"
        self.user = UserFactory.create(
            username=self.username, email=self.email, password=self.password, is_active=False,
        )

        # Set Up Registration
        self.registration = Registration()
        self.registration.register(self.user)
        self.registration.save()

        self.platform_name = configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME)
        self.activation_email_support_link = configuration_helpers.get_value(
            'ACTIVATION_EMAIL_SUPPORT_LINK', settings.ACTIVATION_EMAIL_SUPPORT_LINK
        ) or settings.SUPPORT_SITE_LINK

    def login(self):
        """
        Login with test user.

        Since, only active users can login, so we must activate the user before login.
        This method does the following tasks in order,
            1. Stores user's active/in-active status in a variable.
            2. Makes sure user account is active.
            3. Authenticated user with the client.
            4. Reverts user's original active/in-active status.
        """
        is_active = self.user.is_active

        # Make sure user is active before login
        self.user.is_active = True
        self.user.save()
        self.client.login(username=self.username, password=self.password)

        # Revert user activation status
        self.user.is_active = is_active
        self.user.save()

    def assert_no_tracking(self, mock_segment_identify):
        """ Assert that activate sets the flag but does not call segment. """
        # Ensure that the user starts inactive
        self.assertFalse(self.user.is_active)

        # Until you explicitly activate it
        self.registration.activate()
        self.assertTrue(self.user.is_active)
        self.assertFalse(mock_segment_identify.called)

    def test_account_activation_message(self):
        """
        Verify that account correct activation message is displayed.

        If logged in user has not activated his/her account, make sure that an
        account activation message is displayed on dashboard sidebar.
        """
        # Log in with test user.
        self.login()
        expected_message = (
            u"Check your {email_start}{email}{email_end} inbox for an account activation link from "
            u"{platform_name}. If you need help, contact {link_start}{platform_name} Support{link_end}."
        ).format(
            platform_name=self.platform_name,
            email_start="<strong>",
            email_end="</strong>",
            email=self.user.email,
            link_start="<a target='_blank' href='{activation_email_support_link}'>".format(
                activation_email_support_link=self.activation_email_support_link,
            ),
            link_end="</a>",
        )

        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, expected_message)

        # Now make sure account activation message goes away when user activated the account
        self.user.is_active = True
        self.user.save()
        self.login()
        response = self.client.get(reverse('dashboard'))
        self.assertNotContains(response, expected_message)

    def test_account_activation_notification_on_logistration(self):
        """
        Verify that logistration page displays success/error/info messages
        about account activation.
        """
        login_page_url = "{login_url}?next={redirect_url}".format(
            login_url=reverse('signin_user'),
            redirect_url=reverse('dashboard'),
        )
        # Access activation link, message should say that account has been activated.
        response = self.client.get(reverse('activate', args=[self.registration.activation_key]), follow=True)
        self.assertRedirects(response, login_page_url)
        self.assertContains(response, 'Success! You have activated your account.')

        # Access activation link again, message should say that account is already active.
        response = self.client.get(reverse('activate', args=[self.registration.activation_key]), follow=True)
        self.assertRedirects(response, login_page_url)
        self.assertContains(response, 'This account has already been activated.')

        # Open account activation page with an invalid activation link,
        # there should be an error message displayed.
        response = self.client.get(reverse('activate', args=[uuid4().hex]), follow=True)
        self.assertRedirects(response, login_page_url)
        self.assertContains(response, 'Your account could not be activated')

    def test_account_activation_prevent_auth_user_writes(self):
        login_page_url = "{login_url}?next={redirect_url}".format(
            login_url=reverse('signin_user'),
            redirect_url=reverse('dashboard'),
        )
        with waffle().override(PREVENT_AUTH_USER_WRITES, True):
            response = self.client.get(reverse('activate', args=[self.registration.activation_key]), follow=True)
            self.assertRedirects(response, login_page_url)
            self.assertContains(response, SYSTEM_MAINTENANCE_MSG)
            assert not self.user.is_active
