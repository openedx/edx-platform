"""Tests for util.password_policy_validators module."""

import unittest

from django.core.exceptions import ValidationError
from django.test.utils import override_settings

from util.password_policy_validators import validate_password_dictionary


class PasswordPolicyValidatorsTestCase(unittest.TestCase):
    """ Tests for password validator utility functions """

    @override_settings(PASSWORD_DICTIONARY_EDIT_DISTANCE_THRESHOLD=2)
    @override_settings(PASSWORD_DICTIONARY=['testme'])
    def test_validate_password_dictionary(self):
        """ Tests dictionary checks """
        # Direct match
        with self.assertRaises(ValidationError):
            validate_password_dictionary('testme')

        # Off by one
        with self.assertRaises(ValidationError):
            validate_password_dictionary('estme')

        # Off by two
        with self.assertRaises(ValidationError):
            validate_password_dictionary('bestmet')

        # Off by three (should pass)
        validate_password_dictionary('bestem')
