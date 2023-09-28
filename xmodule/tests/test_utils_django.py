"""Tests for methods defined in util/django.py"""


from unittest import TestCase

from xmodule.util.xmodule_django import get_current_request, get_current_request_hostname


class UtilDjangoTests(TestCase):
    """
    Tests for methods exposed in util/django
    """

    def test_get_current_request(self):
        """
        Since we are running outside of Django assert that get_current_request returns None
        """
        assert get_current_request() is None

    def test_get_current_request_hostname(self):
        """
        Since we are running outside of Django assert that get_current_request_hostname returns None
        """
        assert get_current_request_hostname() is None
