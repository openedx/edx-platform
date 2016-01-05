"""Tests for account activation"""
from mock import patch
import unittest

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from student.models import Registration


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestActivateAccount(TestCase):
    """Tests for account creation"""

    def setUp(self):
        super(TestActivateAccount, self).setUp()
        self.username = "jack"
        self.email = "jack@fake.edx.org"
        self.user = User.objects.create(username=self.username, email=self.email, is_active=False)

        # Set Up Registration
        self.registration = Registration()
        self.registration.register(self.user)
        self.registration.save()

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
