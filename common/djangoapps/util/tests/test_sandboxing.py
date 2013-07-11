"""
Tests for sandboxing.py in util app
"""

from django.test import TestCase
from util.sandboxing import can_execute_unsafe_code
from django.test.utils import override_settings


class SandboxingTest(TestCase):
    """
    Test sandbox whitelisting
    """
    @override_settings(COURSES_WITH_UNSAFE_CODE=['edX/full/.*'])
    def test_sandbox_exclusion(self):
        """
        Test to make sure that a non-match returns false
        """
        self.assertFalse(can_execute_unsafe_code('edX/notful/empty'))

    @override_settings(COURSES_WITH_UNSAFE_CODE=['edX/full/.*'])
    def test_sandbox_inclusion(self):
        """
        Test to make sure that a match works across course runs
        """
        self.assertTrue(can_execute_unsafe_code('edX/full/2012_Fall'))
        self.assertTrue(can_execute_unsafe_code('edX/full/2013_Spring'))
