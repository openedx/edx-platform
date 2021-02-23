"""
Tests for ErrorBlock and NonStaffErrorBlock
"""


import unittest

import pytest
from mock import MagicMock, Mock, patch
from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator
from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds
from xblock.runtime import IdReader, Runtime
from xblock.test.tools import unabc

from xmodule.error_module import ErrorBlock, NonStaffErrorBlock
from xmodule.modulestore.xml import CourseLocationManager
from xmodule.tests import get_test_system
from xmodule.x_module import STUDENT_VIEW, XModule, XModuleDescriptor


class SetupTestErrorBlock(unittest.TestCase):
    """Common setUp for use in ErrorBlock tests."""

    def setUp(self):
        super().setUp()
        self.system = get_test_system()
        self.course_id = CourseLocator('org', 'course', 'run')
        self.location = self.course_id.make_usage_key('foo', 'bar')
        self.valid_xml = u"<problem>ABC \N{SNOWMAN}</problem>"
        self.error_msg = "Error"


class TestErrorBlock(SetupTestErrorBlock):
    """
    Tests for ErrorBlock
    """

    def test_error_block_xml_rendering(self):
        descriptor = ErrorBlock.from_xml(
            self.valid_xml,
            self.system,
            CourseLocationManager(self.course_id),
            self.error_msg
        )
        assert isinstance(descriptor, ErrorBlock)
        descriptor.xmodule_runtime = self.system
        context_repr = self.system.render(descriptor, STUDENT_VIEW).content
        assert self.error_msg in context_repr
        assert repr(self.valid_xml) in context_repr

    def test_error_block_from_descriptor(self):
        descriptor = MagicMock(
            spec=XModuleDescriptor,
            runtime=self.system,
            location=self.location,
        )

        error_descriptor = ErrorBlock.from_descriptor(
            descriptor, self.error_msg)
        assert isinstance(error_descriptor, ErrorBlock)
        error_descriptor.xmodule_runtime = self.system
        context_repr = self.system.render(error_descriptor, STUDENT_VIEW).content
        assert self.error_msg in context_repr
        assert repr(descriptor) in context_repr


class TestNonStaffErrorBlock(SetupTestErrorBlock):
    """
    Tests for NonStaffErrorBlock.
    """

    def test_non_staff_error_block_create(self):
        descriptor = NonStaffErrorBlock.from_xml(
            self.valid_xml,
            self.system,
            CourseLocationManager(self.course_id)
        )
        assert isinstance(descriptor, NonStaffErrorBlock)

    def test_from_xml_render(self):
        descriptor = NonStaffErrorBlock.from_xml(
            self.valid_xml,
            self.system,
            CourseLocationManager(self.course_id)
        )
        descriptor.xmodule_runtime = self.system
        context_repr = self.system.render(descriptor, STUDENT_VIEW).content
        assert self.error_msg not in context_repr
        assert repr(self.valid_xml) not in context_repr

    def test_error_block_from_descriptor(self):
        descriptor = MagicMock(
            spec=XModuleDescriptor,
            runtime=self.system,
            location=self.location,
        )

        error_descriptor = NonStaffErrorBlock.from_descriptor(
            descriptor, self.error_msg)
        assert isinstance(error_descriptor, ErrorBlock)
        error_descriptor.xmodule_runtime = self.system
        context_repr = self.system.render(error_descriptor, STUDENT_VIEW).content
        assert self.error_msg not in context_repr
        assert str(descriptor) not in context_repr


class BrokenModule(XModule):  # lint-amnesty, pylint: disable=abstract-method
    def __init__(self, *args, **kwargs):
        super(BrokenModule, self).__init__(*args, **kwargs)  # lint-amnesty, pylint: disable=super-with-arguments
        raise Exception("This is a broken xmodule")


class BrokenDescriptor(XModuleDescriptor):  # lint-amnesty, pylint: disable=abstract-method
    module_class = BrokenModule


class TestException(Exception):
    """An exception type to use to verify raises in tests"""
    pass  # lint-amnesty, pylint: disable=unnecessary-pass


@unabc("Tests should not call {}")
class TestRuntime(Runtime):  # lint-amnesty, pylint: disable=abstract-method
    pass


class TestErrorBlockConstruction(unittest.TestCase):
    """
    Test that error block construction happens correctly
    """

    def setUp(self):
        # pylint: disable=abstract-class-instantiated
        super().setUp()
        field_data = DictFieldData({})
        self.descriptor = BrokenDescriptor(
            TestRuntime(Mock(spec=IdReader), field_data),
            field_data,
            ScopeIds(None, None, None,
                     BlockUsageLocator(CourseLocator('org', 'course', 'run'), 'broken', 'name'))
        )
        self.descriptor.xmodule_runtime = TestRuntime(Mock(spec=IdReader), field_data)
        self.descriptor.xmodule_runtime.error_descriptor_class = ErrorBlock
        self.descriptor.xmodule_runtime.xmodule_instance = None

    def test_broken_block(self):
        """
        Test that when an XModule throws an block during __init__, we
        get an ErrorBlock back from XModuleDescriptor._xmodule
        """
        module = self.descriptor._xmodule  # lint-amnesty, pylint: disable=protected-access
        assert isinstance(module, ErrorBlock)

    @patch.object(ErrorBlock, '__init__', Mock(side_effect=TestException))
    def test_broken_error_descriptor(self):
        """
        Test that a broken block descriptor doesn't cause an infinite loop
        """
        with pytest.raises(TestException):
            module = self.descriptor._xmodule  # lint-amnesty, pylint: disable=protected-access, unused-variable

    @patch.object(ErrorBlock, '__init__', Mock(side_effect=TestException))
    def test_broken_error_block(self):
        """
        Test that a broken block module doesn't cause an infinite loop
        """
        with pytest.raises(TestException):
            module = self.descriptor._xmodule  # lint-amnesty, pylint: disable=protected-access, unused-variable
