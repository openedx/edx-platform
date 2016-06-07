"""Tests for methods defined in util/django.py"""
from xmodule.util.django import get_current_request, get_current_request_hostname
from nose.tools import assert_is_none
from unittest import TestCase


class UtilDjangoTests(TestCase):
    """
    Tests for methods exposed in util/django
    """
    def test_get_current_request(self):
        """
        Since we are running outside of Django assert that get_current_request returns None
        """
        assert_is_none(get_current_request())

    def test_get_current_request_hostname(self):
        """
        Since we are running outside of Django assert that get_current_request_hostname returns None
        """
        assert_is_none(get_current_request_hostname())
