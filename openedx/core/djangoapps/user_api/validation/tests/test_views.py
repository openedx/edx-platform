# -*- coding: utf-8 -*-
"""
Tests for an API endpoint for client-side user data validation.
"""

import unittest

import ddt
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.test.utils import override_settings
from six import text_type

from openedx.core.djangoapps.user_api import accounts
from openedx.core.djangoapps.user_api.accounts.tests import testutils
from openedx.core.lib.api import test_utils
from openedx.core.djangoapps.user_api.validation.views import RegistrationValidationThrottle
from util.password_policy_validators import DEFAULT_MAX_PASSWORD_LENGTH


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

    def assertNotValidationDecision(self, data, decision):
        self.assertNotEqual(
            self.get_validation_decision(data),
            decision
        )

    def test_no_decision_for_empty_request(self):
        self.assertValidationDecision(
            {},
            {}
        )

    def test_no_decision_for_invalid_request(self):
        self.assertValidationDecision(
            {'invalid_field': 'random_user_data'},
            {}
        )

    @ddt.data(
        ['name', [name for name in testutils.VALID_NAMES]],
        ['email', [email for email in testutils.VALID_EMAILS]],
        ['password', [password for password in testutils.VALID_PASSWORDS]],
        ['username', [username for username in testutils.VALID_USERNAMES]],
        ['country', [country for country in testutils.VALID_COUNTRIES]]
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
        ['name', [name for name in testutils.INVALID_NAMES[1:]]],
        ['email', [email for email in testutils.INVALID_EMAILS[1:]]],
        ['password', [password for password in testutils.INVALID_PASSWORDS[1:]]],
        ['username', [username for username in testutils.INVALID_USERNAMES[1:]]],
        ['country', [country for country in testutils.INVALID_COUNTRIES[1:]]]
    )
    @ddt.unpack
    def test_negative_validation_decision(self, form_field_name, user_data):
        """
        Test if {0} as any item in {1} gives a negative validation decision.
        """
        self.assertNotValidationDecision(
            {form_field_name: user_data},
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
                "username": accounts.USERNAME_CONFLICT_MSG.format(
                    username=user.username
                ) if username == user.username else '',
                "email": accounts.EMAIL_CONFLICT_MSG.format(
                    email_address=user.email
                ) if email == user.email else ''
            }
        )

    @ddt.data('', ('e' * accounts.EMAIL_MAX_LENGTH) + '@email.com')
    def test_email_bad_length_validation_decision(self, email):
        self.assertValidationDecision(
            {'email': email},
            {'email': accounts.EMAIL_BAD_LENGTH_MSG}
        )

    def test_email_generically_invalid_validation_decision(self):
        email = 'email'
        self.assertValidationDecision(
            {'email': email},
            {'email': accounts.EMAIL_INVALID_MSG.format(email=email)}
        )

    def test_confirm_email_matches_email(self):
        email = 'user@email.com'
        self.assertValidationDecision(
            {'email': email, 'confirm_email': email},
            {'email': '', 'confirm_email': ''}
        )

    @ddt.data('', 'users@other.email')
    def test_confirm_email_doesnt_equal_email(self, confirm_email):
        self.assertValidationDecision(
            {'email': 'user@email.com', 'confirm_email': confirm_email},
            {'email': '', 'confirm_email': text_type(accounts.REQUIRED_FIELD_CONFIRM_EMAIL_MSG)}
        )

    @ddt.data(
        'u' * (accounts.USERNAME_MIN_LENGTH - 1),
        'u' * (accounts.USERNAME_MAX_LENGTH + 1)
    )
    def test_username_bad_length_validation_decision(self, username):
        self.assertValidationDecision(
            {'username': username},
            {'username': text_type(accounts.USERNAME_BAD_LENGTH_MSG)}
        )

    @unittest.skipUnless(settings.FEATURES.get("ENABLE_UNICODE_USERNAME"), "Unicode usernames disabled.")
    @ddt.data(*testutils.INVALID_USERNAMES_UNICODE)
    def test_username_invalid_unicode_validation_decision(self, username):
        self.assertValidationDecision(
            {'username': username},
            {'username': text_type(accounts.USERNAME_INVALID_CHARS_UNICODE)}
        )

    @unittest.skipIf(settings.FEATURES.get("ENABLE_UNICODE_USERNAME"), "Unicode usernames enabled.")
    @ddt.data(*testutils.INVALID_USERNAMES_ASCII)
    def test_username_invalid_ascii_validation_decision(self, username):
        self.assertValidationDecision(
            {'username': username},
            {"username": text_type(accounts.USERNAME_INVALID_CHARS_ASCII)}
        )

    def test_password_empty_validation_decision(self):
        # 2 is the default setting for minimum length found in lms/envs/common.py
        # under AUTH_PASSWORD_VALIDATORS.MinimumLengthValidator
        msg = u'This password is too short. It must contain at least 2 characters.'
        self.assertValidationDecision(
            {'password': ''},
            {"password": msg}
        )

    def test_password_bad_min_length_validation_decision(self):
        password = 'p'
        # 2 is the default setting for minimum length found in lms/envs/common.py
        # under AUTH_PASSWORD_VALIDATORS.MinimumLengthValidator
        msg = u'This password is too short. It must contain at least 2 characters.'
        self.assertValidationDecision(
            {'password': password},
            {"password": msg}
        )

    def test_password_bad_max_length_validation_decision(self):
        password = 'p' * DEFAULT_MAX_PASSWORD_LENGTH
        # 75 is the default setting for maximum length found in lms/envs/common.py
        # under AUTH_PASSWORD_VALIDATORS.MaximumLengthValidator
        msg = u'This password is too long. It must contain no more than 75 characters.'
        self.assertValidationDecision(
            {'password': password},
            {"password": msg}
        )

    def test_password_equals_username_validation_decision(self):
        self.assertValidationDecision(
            {"username": "somephrase", "password": "somephrase"},
            {"username": "", "password": u"The password is too similar to the username."}
        )

    @override_settings(
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'registration_proxy',
            }
        }
    )
    def test_rate_limiting_registration_view(self):
        """
        Confirm rate limits work as expected for registration
        end point /api/user/v1/validation/registration/. Note
        that drf's rate limiting makes use of the default cache
        to enforce limits; that's why this test needs a "real"
        default cache (as opposed to the usual-for-tests DummyCache)
        """
        for _ in range(RegistrationValidationThrottle().num_requests):
            self.request_without_auth('post', self.path)
        response = self.request_without_auth('post', self.path)
        self.assertEqual(response.status_code, 429)
