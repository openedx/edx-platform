""" Test Authn related exception. """

from __future__ import absolute_import

from unittest import TestCase

from openedx.core.djangoapps.user_authn.exceptions import AuthFailedError
from openedx.core.djangolib.markup import Text


class AuthFailedErrorTests(TestCase):
    """ Tests for AuthFailedError exception."""

    def test_sanitize_message(self):
        """ Tests that AuthFailedError HTML-escapes the message."""
        script_tag = '<script>alert("vulnerable")</script>'
        exception = AuthFailedError(script_tag)

        expected_value = Text(script_tag)
        self.assertEqual(exception.value, expected_value)
