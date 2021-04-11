"""
Tests for sandboxing.py in util app
"""


from django.test import TestCase
from django.test.utils import override_settings
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import CourseLocator, LibraryLocator

from xmodule.util.sandboxing import can_execute_unsafe_code


class SandboxingTest(TestCase):
    """
    Test sandbox whitelisting
    """
    @override_settings(COURSES_WITH_UNSAFE_CODE=['edX/full/.*', 'library:v1-edX+.*'])
    def test_sandbox_exclusion(self):
        """
        Test to make sure that a non-match returns false
        """
        self.assertFalse(can_execute_unsafe_code(CourseLocator('edX', 'notful', 'empty')))
        self.assertFalse(can_execute_unsafe_code(LibraryLocator('edY', 'test_bank')))

    @override_settings(COURSES_WITH_UNSAFE_CODE=['edX/full/.*'])
    def test_sandbox_inclusion(self):
        """
        Test to make sure that a match works across course runs
        """
        self.assertTrue(can_execute_unsafe_code(CourseKey.from_string('edX/full/2012_Fall')))
        self.assertTrue(can_execute_unsafe_code(CourseKey.from_string('edX/full/2013_Spring')))
        self.assertFalse(can_execute_unsafe_code(LibraryLocator('edX', 'test_bank')))

    def test_courselikes_with_unsafe_code_default(self):
        """
        Test that the default setting for COURSES_WITH_UNSAFE_CODE is an empty setting, e.g. we don't use @override_settings in these tests
        """
        self.assertFalse(can_execute_unsafe_code(CourseLocator('edX', 'full', '2012_Fall')))
        self.assertFalse(can_execute_unsafe_code(CourseLocator('edX', 'full', '2013_Spring')))
        self.assertFalse(can_execute_unsafe_code(LibraryLocator('edX', 'test_bank')))
