# -*- coding: utf-8 -*-
"""
Tests for an API endpoint for client-side user data validation.
"""

import unittest

import ddt
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from openedx.core.djangoapps.user_api.accounts import (
    EMAIL_BAD_LENGTH_MSG, EMAIL_INVALID_MSG,
    EMAIL_CONFLICT_MSG, EMAIL_MAX_LENGTH, EMAIL_MIN_LENGTH,
    PASSWORD_BAD_LENGTH_MSG, PASSWORD_CANT_EQUAL_USERNAME_MSG,
    PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH,
    USERNAME_BAD_LENGTH_MSG, USERNAME_INVALID_CHARS_ASCII, USERNAME_INVALID_CHARS_UNICODE,
    USERNAME_CONFLICT_MSG, USERNAME_MAX_LENGTH, USERNAME_MIN_LENGTH
)
from openedx.core.djangoapps.user_api.accounts.tests.testutils import (
    VALID_EMAILS, VALID_PASSWORDS, VALID_USERNAMES,
    INVALID_EMAILS, INVALID_PASSWORDS, INVALID_USERNAMES,
    INVALID_USERNAMES_ASCII, INVALID_USERNAMES_UNICODE
)
from openedx.core.lib.api import test_utils


@ddt.ddt
class RegistrationValidationViewTests(test_utils.ApiTestCase):
    """
    Tests for validity of user data in registration forms.
    """

    endpoint_name = 'registration_validation'
    path = reverse(endpoint_name)

    def get_validation_decision(self, data):
        response = self.client.post(self.path, data)
        return response.data.get('validation_decisions', {})

    def assertValidationDecision(self, data, decision):
        self.assertEqual(
            self.get_validation_decision(data),
            decision
        )

    def test_no_decision_for_empty_request(self):
        self.assertValidationDecision({}, {})

    def test_no_decision_for_invalid_request(self):
        self.assertValidationDecision({'invalid_field': 'random_user_data'}, {})

    @ddt.data(
        ['email', (email for email in VALID_EMAILS)],
        ['password', (password for password in VALID_PASSWORDS)],
        ['username', (username for username in VALID_USERNAMES)]
    )
    @ddt.unpack
    def test_positive_validation_decision(self, form_field_name, user_data):
        """
        Test if {0} as any item in {1} gives a positive validation decision.
        """
        self.assertValidationDecision(
            {form_field_name: user_data},
            {form_field_name: ''}
        )

    @ddt.data(
        # Skip None type for invalidity checks.
        ['email', (email for email in INVALID_EMAILS[1:])],
        ['password', (password for password in INVALID_PASSWORDS[1:])],
        ['username', (username for username in INVALID_USERNAMES[1:])]
    )
    @ddt.unpack
    def test_negative_validation_decision(self, form_field_name, user_data):
        """
        Test if {0} as any item in {1} gives a negative validation decision.
        """
        self.assertNotEqual(
            self.get_validation_decision({form_field_name: user_data}),
            {form_field_name: ''}
        )

    @ddt.data(
        ['username', 'username@email.com'],  # No conflict
        ['user', 'username@email.com'],  # Username conflict
        ['username', 'user@email.com'],  # Email conflict
        ['user', 'user@email.com']  # Both conflict
    )
    @ddt.unpack
    def test_existence_conflict(self, username, email):
        """
        Test if username '{0}' and email '{1}' have conflicts with
        username 'user' and email 'user@email.com'.
        """
        user = User.objects.create_user(username='user', email='user@email.com')
        self.assertValidationDecision(
            {
                'username': username,
                'email': email
            },
            {
                "username": USERNAME_CONFLICT_MSG.format(username=user.username) if username == user.username else '',
                "email": EMAIL_CONFLICT_MSG.format(email_address=user.email) if email == user.email else ''
            }
        )

    @ddt.data('', ('e' * EMAIL_MAX_LENGTH) + '@email.com')
    def test_email_less_than_min_length_validation_decision(self, email):
        self.assertValidationDecision(
            {'email': email},
            {'email': EMAIL_BAD_LENGTH_MSG.format(email=email, min=EMAIL_MIN_LENGTH, max=EMAIL_MAX_LENGTH)}
        )

    def test_email_generically_invalid_validation_decision(self):
        email = 'email'
        self.assertValidationDecision(
            {'email': email},
            {'email': EMAIL_INVALID_MSG.format(email=email)}
        )

    @ddt.data(
        'u' * (USERNAME_MIN_LENGTH - 1),
        'u' * (USERNAME_MAX_LENGTH + 1)
    )
    def test_username_less_than_min_length_validation_decision(self, username):
        self.assertValidationDecision(
            {'username': username},
            {
                'username': USERNAME_BAD_LENGTH_MSG.format(
                    username=username,
                    min=USERNAME_MIN_LENGTH,
                    max=USERNAME_MAX_LENGTH
                )
            }
        )

    @unittest.skipUnless(settings.FEATURES.get("ENABLE_UNICODE_USERNAME"), "Unicode usernames disabled.")
    @ddt.data(*INVALID_USERNAMES_UNICODE)
    @ddt.unpack
    def test_username_invalid_unicode_validation_decision(self, username):
        self.assertValidationDecision(
            {'username': username},
            {'username': USERNAME_INVALID_CHARS_UNICODE}
        )

    @unittest.skipIf(settings.FEATURES.get("ENABLE_UNICODE_USERNAME"), "Unicode usernames enabled.")
    @ddt.data(*INVALID_USERNAMES_ASCII)
    @ddt.unpack
    def test_username_invalid_ascii_validation_decision(self, username):
        self.assertValidationDecision(
            {'username': username},
            {"username": USERNAME_INVALID_CHARS_ASCII}
        )

    @ddt.data(
        'p' * (PASSWORD_MIN_LENGTH - 1),
        'p' * (PASSWORD_MAX_LENGTH + 1)
    )
    def test_password_less_than_min_length_validation_decision(self, password):
        self.assertValidationDecision(
            {'password': password},
            {"password": PASSWORD_BAD_LENGTH_MSG.format(min=PASSWORD_MIN_LENGTH, max=PASSWORD_MAX_LENGTH)}
        )

    def test_password_equals_username_validation_decision(self):
        self.assertValidationDecision(
            {"username": "somephrase", "password": "somephrase"},
            {"username": "", "password": PASSWORD_CANT_EQUAL_USERNAME_MSG}
        )
