"""
Tests for ErrorModule and NonStaffErrorModule
"""
import unittest
from xmodule.tests import get_test_system
import xmodule.error_module as error_module
from xmodule.modulestore import Location
from xmodule.x_module import XModuleDescriptor
from mock import MagicMock


class SetupTestErrorModules():
    def setUp(self):
        self.system = get_test_system()
        self.org = "org"
        self.course = "course"
        self.location = Location(['i4x', self.org, self.course, None, None])
        self.valid_xml = u"<problem>ABC \N{SNOWMAN}</problem>"
        self.error_msg = "Error"


class TestErrorModule(unittest.TestCase, SetupTestErrorModules):
    """
    Tests for ErrorModule and ErrorDescriptor
    """
    def setUp(self):
        SetupTestErrorModules.setUp(self)

    def test_error_module_xml_rendering(self):
        descriptor = error_module.ErrorDescriptor.from_xml(
            self.valid_xml, self.system, self.org, self.course, self.error_msg)
        self.assertIsInstance(descriptor, error_module.ErrorDescriptor)
        descriptor.xmodule_runtime = self.system
        context_repr = self.system.render(descriptor, 'student_view').content
        self.assertIn(self.error_msg, context_repr)
        self.assertIn(repr(self.valid_xml), context_repr)

    def test_error_module_from_descriptor(self):
        descriptor = MagicMock([XModuleDescriptor],
                               runtime=self.system,
                               location=self.location,
                               _field_data=self.valid_xml)

        error_descriptor = error_module.ErrorDescriptor.from_descriptor(
            descriptor, self.error_msg)
        self.assertIsInstance(error_descriptor, error_module.ErrorDescriptor)
        error_descriptor.xmodule_runtime = self.system
        context_repr = self.system.render(error_descriptor, 'student_view').content
        self.assertIn(self.error_msg, context_repr)
        self.assertIn(repr(descriptor), context_repr)


class TestNonStaffErrorModule(unittest.TestCase, SetupTestErrorModules):
    """
    Tests for NonStaffErrorModule and NonStaffErrorDescriptor
    """
    def setUp(self):
        SetupTestErrorModules.setUp(self)

    def test_non_staff_error_module_create(self):
        descriptor = error_module.NonStaffErrorDescriptor.from_xml(
            self.valid_xml, self.system, self.org, self.course)
        self.assertIsInstance(descriptor, error_module.NonStaffErrorDescriptor)

    def test_from_xml_render(self):
        descriptor = error_module.NonStaffErrorDescriptor.from_xml(
            self.valid_xml, self.system, self.org, self.course)
        descriptor.xmodule_runtime = self.system
        context_repr = self.system.render(descriptor, 'student_view').content
        self.assertNotIn(self.error_msg, context_repr)
        self.assertNotIn(repr(self.valid_xml), context_repr)

    def test_error_module_from_descriptor(self):
        descriptor = MagicMock([XModuleDescriptor],
                               runtime=self.system,
                               location=self.location,
                               _field_data=self.valid_xml)

        error_descriptor = error_module.NonStaffErrorDescriptor.from_descriptor(
            descriptor, self.error_msg)
        self.assertIsInstance(error_descriptor, error_module.ErrorDescriptor)
        error_descriptor.xmodule_runtime = self.system
        context_repr = self.system.render(error_descriptor, 'student_view').content
        self.assertNotIn(self.error_msg, context_repr)
        self.assertNotIn(str(descriptor), context_repr)
