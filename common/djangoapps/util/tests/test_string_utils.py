"""
Tests for string_utils.py
"""

import pytest
from django.test import TestCase

from common.djangoapps.util.string_utils import str_to_bool


class StringUtilsTest(TestCase):
    """
    Tests for str_to_bool.
    """
    def test_str_to_bool_true(self):
        assert str_to_bool('True')
        assert str_to_bool('true')
        assert str_to_bool('trUe')

    def test_str_to_bool_false(self):
        assert not str_to_bool('Tru')
        assert not str_to_bool('False')
        assert not str_to_bool('false')
        assert not str_to_bool('')
        assert not str_to_bool(None)
        assert not str_to_bool('anything')

    def test_str_to_bool_errors(self):
        def test_raises_error(val):
            with pytest.raises(AttributeError):
                assert not str_to_bool(val)

        test_raises_error({})
        test_raises_error([])
        test_raises_error(1)
        test_raises_error(True)
