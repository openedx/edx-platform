# -*- coding: utf-8 -*-
"""
Unit tests for behavior that is specific to the api methods (vs. the view methods).
Most of the functionality is covered in test_views.py.
"""

from mock import Mock, patch
from django.test import TestCase
import unittest
from student.tests.factories import UserFactory
from django.conf import settings
from student.models import PendingEmailChange
from openedx.core.djangoapps.user_api.api.account import (
    AccountUserNotFound, AccountUpdateError, AccountNotAuthorized, AccountValidationError
)
from ..api import get_account_settings, update_account_settings
from ..serializers import AccountUserSerializer


def mock_render_to_string(template_name, context):
    """Return a string that encodes template_name and context"""
    return str((template_name, sorted(context.iteritems())))


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Account APIs are only supported in LMS')
class TestAccountApi(TestCase):
    """
    These tests specifically cover the parts of the API methods that are not covered by test_views.py.
    This includes the specific types of error raised, and default behavior when optional arguments
    are not specified.
    """
    password = "test"

    def setUp(self):
        super(TestAccountApi, self).setUp()
        self.user = UserFactory.create(password=self.password)
        self.different_user = UserFactory.create(password=self.password)
        self.staff_user = UserFactory(is_staff=True, password=self.password)

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
        """Test that AccountUserNotFound is thrown if there is no user with username."""
        with self.assertRaises(AccountUserNotFound):
            get_account_settings(self.user, username="does_not_exist")

        self.user.username = "does_not_exist"
        with self.assertRaises(AccountUserNotFound):
            get_account_settings(self.user)

    def test_update_username_provided(self):
        """Test the difference in behavior when a username is supplied to update_account_settings."""
        update_account_settings(self.user, {"name": "Mickey Mouse"})
        account_settings = get_account_settings(self.user)
        self.assertEqual("Mickey Mouse", account_settings["name"])

        update_account_settings(self.user, {"name": "Donald Duck"}, username=self.user.username)
        account_settings = get_account_settings(self.user)
        self.assertEqual("Donald Duck", account_settings["name"])

        with self.assertRaises(AccountNotAuthorized):
            update_account_settings(self.different_user, {"name": "Pluto"}, username=self.user.username)

    def test_update_user_not_found(self):
        """Test that AccountUserNotFound is thrown if there is no user with username."""
        with self.assertRaises(AccountUserNotFound):
            update_account_settings(self.user, {}, username="does_not_exist")

        self.user.username = "does_not_exist"
        with self.assertRaises(AccountUserNotFound):
            update_account_settings(self.user, {})

    def test_update_error_validating(self):
        """Test that AccountValidationError is thrown if incorrect values are supplied."""
        with self.assertRaises(AccountValidationError):
            update_account_settings(self.user, {"username": "not_allowed"})

        with self.assertRaises(AccountValidationError):
            update_account_settings(self.user, {"gender": "undecided"})

    def test_update_multiple_validation_errors(self):
        """Test that all validation errors are built up and returned at once"""
        # Send a read-only error, serializer error, and email validation error.
        naughty_update = {
            "username": "not_allowed",
            "gender": "undecided",
            "email": "not an email address"
        }

        error_thrown = False
        try:
            update_account_settings(self.user, naughty_update)
        except AccountValidationError as response:
            error_thrown = True
            field_errors = response.field_errors
            self.assertEqual(3, len(field_errors))
            self.assertEqual("This field is not editable via this API", field_errors["username"]["developer_message"])
            self.assertIn("Select a valid choice", field_errors["gender"]["developer_message"])
            self.assertIn("Valid e-mail address required.", field_errors["email"]["developer_message"])

        self.assertTrue(error_thrown, "No AccountValidationError was thrown")

    @patch('django.core.mail.send_mail')
    @patch('student.views.render_to_string', Mock(side_effect=mock_render_to_string, autospec=True))
    def test_update_sending_email_fails(self, send_mail):
        """Test what happens if all validation checks pass, but sending the email for email change fails."""
        send_mail.side_effect = [Exception, None]
        less_naughty_update = {
            "name": "Mickey Mouse",
            "email": "seems_ok@sample.com"
        }
        error_thrown = False
        try:
            update_account_settings(self.user, less_naughty_update)
        except AccountUpdateError as response:
            error_thrown = True
            self.assertIn("Error thrown from do_email_change_request", response.developer_message)

        self.assertTrue(error_thrown, "No AccountUpdateError was thrown")

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
        error_thrown = False
        try:
            update_account_settings(self.user, update_will_fail)
        except AccountUpdateError as response:
            error_thrown = True
            self.assertIn("Error thrown when saving account updates", response.developer_message)

        self.assertTrue(error_thrown, "No AccountUpdateError was thrown")

        # Verify that no email change request was initiated.
        pending_change = PendingEmailChange.objects.filter(user=self.user)
        self.assertEqual(0, len(pending_change))
