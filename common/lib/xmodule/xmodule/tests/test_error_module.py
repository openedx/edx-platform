"""
Tests for ErrorModule and NonStaffErrorModule
"""
import unittest
from xmodule.tests import test_system
import xmodule.error_module as error_module
from xmodule.modulestore import Location
from xmodule.x_module import XModuleDescriptor
from mock import MagicMock


class TestErrorModule(unittest.TestCase):
    """
    Tests for ErrorModule and ErrorDescriptor
    """
    def setUp(self):
        self.system = test_system()
        self.org = "org"
        self.course = "course"
        self.location = Location(['i4x', self.org, self.course, None, None])
        self.valid_xml = "<problem />"
        self.broken_xml = "<problem>"
        self.error_msg = "Error"

    def test_error_module_xml_rendering(self):
        descriptor = error_module.ErrorDescriptor.from_xml(
            self.valid_xml, self.system, self.org, self.course, self.error_msg)
        self.assertTrue(isinstance(descriptor, error_module.ErrorDescriptor))
        module = descriptor.xmodule(self.system)
        rendered_html = module.get_html()
        self.assertIn(self.error_msg, rendered_html)
        self.assertIn(self.valid_xml, rendered_html)

    def test_error_module_from_descriptor(self):
        descriptor = MagicMock([XModuleDescriptor],
                               system=self.system,
                               location=self.location,
                               _model_data=self.valid_xml)

        error_descriptor = error_module.ErrorDescriptor.from_descriptor(
            descriptor, self.error_msg)
        self.assertTrue(isinstance(error_descriptor, error_module.ErrorDescriptor))
        module = error_descriptor.xmodule(self.system)
        rendered_html = module.get_html()
        self.assertIn(self.error_msg, rendered_html)
        self.assertIn(str(descriptor), rendered_html)


class TestNonStaffErrorModule(TestErrorModule):
    """
    Tests for NonStaffErrorModule and NonStaffErrorDescriptor
    """

    def test_non_staff_error_module_create(self):
        descriptor = error_module.NonStaffErrorDescriptor.from_xml(
            self.valid_xml, self.system, self.org, self.course)
        self.assertTrue(isinstance(descriptor, error_module.NonStaffErrorDescriptor))

    def test_from_xml_render(self):
        descriptor = error_module.NonStaffErrorDescriptor.from_xml(
            self.valid_xml, self.system, self.org, self.course)
        module = descriptor.xmodule(self.system)
        rendered_html = module.get_html()
        self.assertNotIn(self.error_msg, rendered_html)
        self.assertNotIn(self.valid_xml, rendered_html)

    def test_error_module_from_descriptor(self):
        descriptor = MagicMock([XModuleDescriptor],
                               system=self.system,
                               location=self.location,
                               _model_data=self.valid_xml)

        error_descriptor = error_module.NonStaffErrorDescriptor.from_descriptor(
            descriptor, self.error_msg)
        self.assertTrue(isinstance(error_descriptor, error_module.ErrorDescriptor))
        module = error_descriptor.xmodule(self.system)
        rendered_html = module.get_html()
        self.assertNotIn(self.error_msg, rendered_html)
        self.assertNotIn(str(descriptor), rendered_html)
