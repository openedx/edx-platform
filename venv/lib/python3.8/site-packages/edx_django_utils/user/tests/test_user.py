"""Test user functions"""

import pytest
from django.test import TestCase

from edx_django_utils.user import generate_password


class GeneratePasswordTest(TestCase):
    """Tests formation of randomly generated passwords."""

    def test_default_args(self):
        password = generate_password()
        assert 12 == len(password)
        assert any(c.isdigit for c in password)
        assert any(c.isalpha for c in password)

    def test_length(self):
        length = 25
        assert length == len(generate_password(length=length))

    def test_chars(self):
        char = '!'
        password = generate_password(length=12, chars=(char,))

        assert any(c.isdigit for c in password)
        assert any(c.isalpha for c in password)
        assert (char * 10) == password[2:]

    def test_min_length(self):
        with pytest.raises(ValueError):
            generate_password(length=7)
