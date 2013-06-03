"""
Tests for ErrorModule and NonStaffErrorModule
"""
import unittest
from xmodule.tests import test_system
import xmodule.error_module as error_module


class TestErrorModule(unittest.TestCase):
    """
    Tests for ErrorModule and ErrorDescriptor
    """
    def setUp(self):
        self.system = test_system()
        self.org = "org"
        self.course = "course"
        self.fake_xml = "<problem />"
        self.broken_xml = "<problem>"
        self.error_msg = "Error"

    def test_error_module_create(self):
        descriptor = error_module.ErrorDescriptor.from_xml(
            self.fake_xml, self.system, self.org, self.course)
        self.assertTrue(isinstance(descriptor, error_module.ErrorDescriptor))

    def test_error_module_rendering(self):
        descriptor = error_module.ErrorDescriptor.from_xml(
            self.fake_xml, self.system, self.org, self.course, self.error_msg)
        module = descriptor.xmodule(self.system)
        rendered_html = module.get_html()
        self.assertIn(self.error_msg, rendered_html)
        self.assertIn(self.fake_xml, rendered_html)


class TestNonStaffErrorModule(TestErrorModule):
    """
    Tests for NonStaffErrorModule and NonStaffErrorDescriptor
    """

    def test_non_staff_error_module_create(self):
        descriptor = error_module.NonStaffErrorDescriptor.from_xml(
            self.fake_xml, self.system, self.org, self.course)
        self.assertTrue(isinstance(descriptor, error_module.NonStaffErrorDescriptor))

    def test_non_staff_error_module_rendering(self):
        descriptor = error_module.NonStaffErrorDescriptor.from_xml(
            self.fake_xml, self.system, self.org, self.course)
        module = descriptor.xmodule(self.system)
        rendered_html = module.get_html()
        self.assertNotIn(self.error_msg, rendered_html)
        self.assertNotIn(self.fake_xml, rendered_html)
