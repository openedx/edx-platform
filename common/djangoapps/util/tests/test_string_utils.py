"""
Tests for string_utils.py
"""

from django.test import TestCase
from util.string_utils import str_to_bool


class StringUtilsTest(TestCase):
    """
    Tests for str_to_bool.
    """
    def test_str_to_bool_true(self):
        self.assertTrue(str_to_bool('True'))
        self.assertTrue(str_to_bool('true'))
        self.assertTrue(str_to_bool('trUe'))

    def test_str_to_bool_false(self):
        self.assertFalse(str_to_bool('Tru'))
        self.assertFalse(str_to_bool('False'))
        self.assertFalse(str_to_bool('false'))
        self.assertFalse(str_to_bool(''))
        self.assertFalse(str_to_bool(None))
        self.assertFalse(str_to_bool('anything'))

    def test_str_to_bool_errors(self):
        def test_raises_error(val):
            with self.assertRaises(AttributeError):
                self.assertFalse(str_to_bool(val))

        test_raises_error({})
        test_raises_error([])
        test_raises_error(1)
        test_raises_error(True)
