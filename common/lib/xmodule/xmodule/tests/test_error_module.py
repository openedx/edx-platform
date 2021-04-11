"""
Tests for ErrorModule and NonStaffErrorModule
"""


import unittest

from mock import MagicMock, Mock, patch
from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator
from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds
from xblock.runtime import IdReader, Runtime
from xblock.test.tools import unabc

from xmodule.error_module import ErrorDescriptor, ErrorModule, NonStaffErrorDescriptor
from xmodule.modulestore.xml import CourseLocationManager
from xmodule.tests import get_test_system
from xmodule.x_module import STUDENT_VIEW, XModule, XModuleDescriptor


class SetupTestErrorModules(unittest.TestCase):
    """Common setUp for use in ErrorModule tests."""

    def setUp(self):
        super(SetupTestErrorModules, self).setUp()
        self.system = get_test_system()
        self.course_id = CourseLocator('org', 'course', 'run')
        self.location = self.course_id.make_usage_key('foo', 'bar')
        self.valid_xml = u"<problem>ABC \N{SNOWMAN}</problem>"
        self.error_msg = "Error"


class TestErrorModule(SetupTestErrorModules):
    """
    Tests for ErrorModule and ErrorDescriptor
    """

    def test_error_module_xml_rendering(self):
        descriptor = ErrorDescriptor.from_xml(
            self.valid_xml,
            self.system,
            CourseLocationManager(self.course_id),
            self.error_msg
        )
        self.assertIsInstance(descriptor, ErrorDescriptor)
        descriptor.xmodule_runtime = self.system
        context_repr = self.system.render(descriptor, STUDENT_VIEW).content
        self.assertIn(self.error_msg, context_repr)
        self.assertIn(repr(self.valid_xml), context_repr)

    def test_error_module_from_descriptor(self):
        descriptor = MagicMock(
            spec=XModuleDescriptor,
            runtime=self.system,
            location=self.location,
        )

        error_descriptor = ErrorDescriptor.from_descriptor(
            descriptor, self.error_msg)
        self.assertIsInstance(error_descriptor, ErrorDescriptor)
        error_descriptor.xmodule_runtime = self.system
        context_repr = self.system.render(error_descriptor, STUDENT_VIEW).content
        self.assertIn(self.error_msg, context_repr)
        self.assertIn(repr(descriptor), context_repr)


class TestNonStaffErrorModule(SetupTestErrorModules):
    """
    Tests for NonStaffErrorModule and NonStaffErrorDescriptor
    """

    def test_non_staff_error_module_create(self):
        descriptor = NonStaffErrorDescriptor.from_xml(
            self.valid_xml,
            self.system,
            CourseLocationManager(self.course_id)
        )
        self.assertIsInstance(descriptor, NonStaffErrorDescriptor)

    def test_from_xml_render(self):
        descriptor = NonStaffErrorDescriptor.from_xml(
            self.valid_xml,
            self.system,
            CourseLocationManager(self.course_id)
        )
        descriptor.xmodule_runtime = self.system
        context_repr = self.system.render(descriptor, STUDENT_VIEW).content
        self.assertNotIn(self.error_msg, context_repr)
        self.assertNotIn(repr(self.valid_xml), context_repr)

    def test_error_module_from_descriptor(self):
        descriptor = MagicMock(
            spec=XModuleDescriptor,
            runtime=self.system,
            location=self.location,
        )

        error_descriptor = NonStaffErrorDescriptor.from_descriptor(
            descriptor, self.error_msg)
        self.assertIsInstance(error_descriptor, ErrorDescriptor)
        error_descriptor.xmodule_runtime = self.system
        context_repr = self.system.render(error_descriptor, STUDENT_VIEW).content
        self.assertNotIn(self.error_msg, context_repr)
        self.assertNotIn(str(descriptor), context_repr)


class BrokenModule(XModule):
    def __init__(self, *args, **kwargs):
        super(BrokenModule, self).__init__(*args, **kwargs)
        raise Exception("This is a broken xmodule")


class BrokenDescriptor(XModuleDescriptor):
    module_class = BrokenModule


class TestException(Exception):
    """An exception type to use to verify raises in tests"""
    pass


@unabc("Tests should not call {}")
class TestRuntime(Runtime):
    pass


class TestErrorModuleConstruction(unittest.TestCase):
    """
    Test that error module construction happens correctly
    """

    def setUp(self):
        # pylint: disable=abstract-class-instantiated
        super(TestErrorModuleConstruction, self).setUp()
        field_data = DictFieldData({})
        self.descriptor = BrokenDescriptor(
            TestRuntime(Mock(spec=IdReader), field_data),
            field_data,
            ScopeIds(None, None, None,
                     BlockUsageLocator(CourseLocator('org', 'course', 'run'), 'broken', 'name'))
        )
        self.descriptor.xmodule_runtime = TestRuntime(Mock(spec=IdReader), field_data)
        self.descriptor.xmodule_runtime.error_descriptor_class = ErrorDescriptor
        self.descriptor.xmodule_runtime.xmodule_instance = None

    def test_broken_module(self):
        """
        Test that when an XModule throws an error during __init__, we
        get an ErrorModule back from XModuleDescriptor._xmodule
        """
        module = self.descriptor._xmodule
        self.assertIsInstance(module, ErrorModule)

    @patch.object(ErrorDescriptor, '__init__', Mock(side_effect=TestException))
    def test_broken_error_descriptor(self):
        """
        Test that a broken error descriptor doesn't cause an infinite loop
        """
        with self.assertRaises(TestException):
            module = self.descriptor._xmodule

    @patch.object(ErrorModule, '__init__', Mock(side_effect=TestException))
    def test_broken_error_module(self):
        """
        Test that a broken error module doesn't cause an infinite loop
        """
        with self.assertRaises(TestException):
            module = self.descriptor._xmodule
