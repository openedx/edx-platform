# -*- coding: utf-8 -*-
"""Tests for util.password_policy_validators module."""

import mock
import unittest

from ddt import data, ddt, unpack
from django.conf import settings
from django.core.exceptions import ValidationError
from django.test.utils import override_settings

from util.password_policy_validators import (
    password_instructions, password_min_length, validate_password, _validate_password_dictionary
)


@ddt
class PasswordPolicyValidatorsTestCase(unittest.TestCase):
    """ Tests for password validator utility functions """

    @override_settings(PASSWORD_DICTIONARY_EDIT_DISTANCE_THRESHOLD=2)
    @override_settings(PASSWORD_DICTIONARY=['testme'])
    @mock.patch.dict(settings.FEATURES, {'ENFORCE_PASSWORD_POLICY': True})
    def test_validate_password_dictionary(self):
        """ Tests dictionary checks """
        # Direct match
        with self.assertRaises(ValidationError):
            _validate_password_dictionary(u'testme')

        # Off by one
        with self.assertRaises(ValidationError):
            _validate_password_dictionary(u'estme')

        # Off by two
        with self.assertRaises(ValidationError):
            _validate_password_dictionary(u'bestmet')

        # Off by three (should pass)
        _validate_password_dictionary(u'bestem')

    def test_unicode_password(self):
        """ Tests that validate_password enforces unicode """
        byte_str = b'𤭮'
        unicode_str = u'𤭮'

        # Sanity checks and demonstration of why this test is useful
        self.assertEqual(len(byte_str), 4)
        self.assertEqual(len(unicode_str), 1)
        self.assertEqual(password_min_length(), 2)

        # Test length check
        with self.assertRaises(ValidationError):
            validate_password(byte_str)
        validate_password(byte_str + byte_str)

        # Test badly encoded password
        with self.assertRaises(ValidationError) as cm:
            validate_password(b'\xff\xff')
        self.assertEquals('Invalid password.', cm.exception.message)

    @data(
        (u'', 'at least 2 characters & 2 letters & 1 number.'),
        (u'a.', 'at least 2 letters & 1 number.'),
        (u'a1', 'at least 2 letters.'),
        (u'aa1', None),
    )
    @unpack
    @override_settings(PASSWORD_COMPLEXITY={'ALPHABETIC': 2, 'NUMERIC': 1})
    @mock.patch.dict(settings.FEATURES, {'ENFORCE_PASSWORD_POLICY': True})
    def test_validation_errors(self, password, msg):
        """ Tests validate_password error messages """
        if msg is None:
            validate_password(password)
        else:
            with self.assertRaises(ValidationError) as cm:
                validate_password(password)
            self.assertIn(msg, cm.exception.message)

    @data(
        ({}, 'at least 2 characters.'),
        ({'ALPHABETIC': 2}, 'characters, including 2 letters.'),
        ({'ALPHABETIC': 2, 'NUMERIC': 1}, 'characters, including 2 letters & 1 number.'),
        ({'NON ASCII': 2, 'NUMERIC': 1, 'UPPER': 3}, 'including 3 uppercase letters & 1 number & 2 symbols.'),
    )
    @unpack
    @mock.patch.dict(settings.FEATURES, {'ENFORCE_PASSWORD_POLICY': True})
    def test_password_instruction(self, config, msg):
        """ Tests password_instruction """
        with override_settings(PASSWORD_COMPLEXITY=config):
            self.assertIn(msg, password_instructions())
