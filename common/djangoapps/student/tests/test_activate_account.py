"""Tests for account activation"""
import unittest
from uuid import uuid4

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
from mock import patch

from edxmako.shortcuts import render_to_string
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
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

    @override_settings(
        LMS_SEGMENT_KEY="testkey",
        MAILCHIMP_NEW_USER_LIST_ID="listid"
    )
    @patch('student.models.analytics.identify')
    def test_activation_with_keys(self, mock_segment_identify):
        expected_segment_payload = {
            'email': self.email,
            'username': self.username,
            'activated': 1,
        }
        expected_segment_mailchimp_list = {
            "MailChimp": {
                "listId": settings.MAILCHIMP_NEW_USER_LIST_ID
            }
        }

        # Ensure that the user starts inactive
        self.assertFalse(self.user.is_active)

        # Until you explicitly activate it
        self.registration.activate()
        self.assertTrue(self.user.is_active)
        mock_segment_identify.assert_called_with(
            self.user.id,
            expected_segment_payload,
            expected_segment_mailchimp_list
        )

    @override_settings(LMS_SEGMENT_KEY="testkey")
    @patch('student.models.analytics.identify')
    def test_activation_without_mailchimp_key(self, mock_segment_identify):
        self.assert_no_tracking(mock_segment_identify)

    @override_settings(MAILCHIMP_NEW_USER_LIST_ID="listid")
    @patch('student.models.analytics.identify')
    def test_activation_without_segment_key(self, mock_segment_identify):
        self.assert_no_tracking(mock_segment_identify)

    @patch('student.models.analytics.identify')
    def test_activation_without_keys(self, mock_segment_identify):
        self.assert_no_tracking(mock_segment_identify)

    @override_settings(FEATURES=dict(settings.FEATURES, DISPLAY_ACCOUNT_ACTIVATION_MESSAGE_ON_SIDEBAR=True))
    def test_account_activation_message(self):
        """
        Verify that account correct activation message is displayed.

        If logged in user has not activated his/her account, make sure that an
        account activation message is displayed on dashboard sidebar.
        """
        # Log in with test user.
        self.login()
        expected_message = render_to_string(
            'registration/account_activation_sidebar_notice.html',
            {
                'email': self.user.email,
                'platform_name': self.platform_name,
                'activation_email_support_link': self.activation_email_support_link
            }
        )

        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, expected_message, html=True)

        # Now make sure account activation message goes away when user activated the account
        self.user.is_active = True
        self.user.save()
        self.login()
        expected_message = render_to_string(
            'registration/account_activation_sidebar_notice.html',
            {
                'email': self.user.email,
                'platform_name': self.platform_name,
                'activation_email_support_link': self.activation_email_support_link
            }
        )
        response = self.client.get(reverse('dashboard'))
        self.assertNotContains(response, expected_message, html=True)

    @override_settings(FEATURES=dict(settings.FEATURES, DISPLAY_ACCOUNT_ACTIVATION_MESSAGE_ON_SIDEBAR=False))
    def test_account_activation_message_disabled(self):
        """
        Verify that old account activation message is displayed when
        DISPLAY_ACCOUNT_ACTIVATION_MESSAGE_ON_SIDEBAR is disabled.
        """
        # Log in with test user.
        self.login()
        expected_message = render_to_string(
            'registration/activate_account_notice.html',
            {'email': self.user.email}
        )

        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, expected_message, html=True)

        # Now make sure account activation message goes away when user activated the account
        self.user.is_active = True
        self.user.save()
        self.login()
        expected_message = render_to_string(
            'registration/activate_account_notice.html',
            {'email': self.user.email}
        )
        response = self.client.get(reverse('dashboard'))
        self.assertNotContains(response, expected_message, html=True)

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
