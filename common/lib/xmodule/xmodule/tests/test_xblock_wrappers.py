# -*- coding: utf-8 -*-
"""
Tests for the wrapping layer that provides the XBlock API using XModule/Descriptor
functionality
"""
# For tests, ignore access to protected members
# pylint: disable=protected-access


from unittest.case import SkipTest, TestCase

import ddt
import webob
from webob.multidict import MultiDict
from factory import (
    BUILD_STRATEGY,
    Factory,
    LazyAttributeSequence,
    SubFactory,
    lazy_attribute,
    post_generation,
    use_strategy
)
from fs.memoryfs import MemoryFS
from lxml import etree
from mock import Mock
from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator
from six.moves import range
from xblock.core import XBlock
from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds

from xmodule.annotatable_module import AnnotatableBlock
from xmodule.conditional_module import ConditionalBlock
from xmodule.course_module import CourseDescriptor
from xmodule.html_module import HtmlBlock
from xmodule.poll_module import PollDescriptor
from xmodule.randomize_module import RandomizeBlock
from xmodule.seq_module import SequenceDescriptor
from xmodule.tests import get_test_descriptor_system, get_test_system
from xmodule.vertical_block import VerticalBlock
from xmodule.word_cloud_module import WordCloudBlock
from xmodule.wrapper_module import WrapperBlock
from xmodule.x_module import (
    PUBLIC_VIEW,
    STUDENT_VIEW,
    STUDIO_VIEW,
    DescriptorSystem,
    ModuleSystem,
    XModule,
    XModuleDescriptor
)

# A dictionary that maps specific XModuleDescriptor classes without children
# to a list of sample field values to test with.
# TODO: Add more types of sample data
LEAF_XMODULES = {
    AnnotatableBlock: [{}],
    HtmlBlock: [{}],
    PollDescriptor: [{'display_name': 'Poll Display Name'}],
    WordCloudBlock: [{}],
}


# A dictionary that maps specific XModuleDescriptor classes with children
# to a list of sample field values to test with.
# TODO: Add more types of sample data
CONTAINER_XMODULES = {
    ConditionalBlock: [{}],
    CourseDescriptor: [{}],
    RandomizeBlock: [{'display_name': 'Test String Display'}],
    SequenceDescriptor: [{'display_name': u'Test Unicode हिंदी Display'}],
    VerticalBlock: [{}],
    WrapperBlock: [{}],
}

# These modules are not editable in studio yet
NOT_STUDIO_EDITABLE = (
    PollDescriptor,
)


def flatten(class_dict):
    """
    Flatten a dict from cls -> [fields, ...] and yields values of the form (cls, fields)
    for each entry in the dictionary value.
    """
    for cls in sorted(class_dict, key=lambda err: err.__name__):
        fields_list = class_dict[cls]
        for fields in fields_list:
            yield (cls, fields)


@use_strategy(BUILD_STRATEGY)
class ModuleSystemFactory(Factory):
    """
    Factory to build a test ModuleSystem. Creation is
    performed by :func:`xmodule.tests.get_test_system`, so
    arguments for that function are valid factory attributes.
    """
    class Meta(object):
        model = ModuleSystem

    @classmethod
    def _build(cls, target_class, *args, **kwargs):  # pylint: disable=unused-argument
        """See documentation from :meth:`factory.Factory._build`"""
        return get_test_system(*args, **kwargs)


@use_strategy(BUILD_STRATEGY)
class DescriptorSystemFactory(Factory):
    """
    Factory to build a test DescriptorSystem. Creation is
    performed by :func:`xmodule.tests.get_test_descriptor_system`, so
    arguments for that function are valid factory attributes.
    """
    class Meta(object):
        model = DescriptorSystem

    @classmethod
    def _build(cls, target_class, *args, **kwargs):  # pylint: disable=unused-argument
        """See documentation from :meth:`factory.Factory._build`"""
        return get_test_descriptor_system(*args, **kwargs)


class ContainerModuleRuntimeFactory(ModuleSystemFactory):
    """
    Factory to generate a ModuleRuntime that generates children when asked
    for them, for testing container XModules.
    """
    @post_generation
    def depth(self, create, depth, **kwargs):  # pylint: disable=unused-argument
        """
        When `depth` is specified as a Factory parameter, creates a
        tree of children with that many levels.
        """
        # pylint: disable=no-member
        if depth == 0:
            self.get_module.side_effect = lambda x: LeafModuleFactory(descriptor_cls=HtmlBlock)
        else:
            self.get_module.side_effect = lambda x: ContainerModuleFactory(
                descriptor_cls=VerticalBlock,
                depth=depth - 1
            )

    @post_generation
    def position(self, create, position=2, **kwargs):  # pylint: disable=unused-argument, method-hidden
        """
        Update the position attribute of the generated ModuleRuntime.
        """
        self.position = position


class ContainerDescriptorRuntimeFactory(DescriptorSystemFactory):
    """
    Factory to generate a DescriptorRuntime that generates children when asked
    for them, for testing container XModuleDescriptors.
    """
    @post_generation
    def depth(self, create, depth, **kwargs):  # pylint: disable=unused-argument
        """
        When `depth` is specified as a Factory parameter, creates a
        tree of children with that many levels.
        """
        # pylint: disable=no-member
        if depth == 0:
            self.load_item.side_effect = lambda x: LeafModuleFactory(descriptor_cls=HtmlBlock)
        else:
            self.load_item.side_effect = lambda x: ContainerModuleFactory(
                descriptor_cls=VerticalBlock,
                depth=depth - 1
            )

    @post_generation
    def position(self, create, position=2, **kwargs):  # pylint: disable=unused-argument, method-hidden
        """
        Update the position attribute of the generated ModuleRuntime.
        """
        self.position = position


@use_strategy(BUILD_STRATEGY)
class LeafDescriptorFactory(Factory):
    """
    Factory to generate leaf XModuleDescriptors.
    """

    class Meta(object):
        model = XModuleDescriptor

    runtime = SubFactory(DescriptorSystemFactory)
    url_name = LazyAttributeSequence('{.block_type}_{}'.format)

    @lazy_attribute
    def location(self):
        return BlockUsageLocator(CourseLocator('org', 'course', 'run'), 'category', self.url_name)

    @lazy_attribute
    def block_type(self):
        return self.descriptor_cls.__name__  # pylint: disable=no-member

    @lazy_attribute
    def definition_id(self):
        return self.location

    @lazy_attribute
    def usage_id(self):
        return self.location

    @classmethod
    def _build(cls, target_class, *args, **kwargs):  # pylint: disable=unused-argument
        runtime = kwargs.pop('runtime')
        desc_cls = kwargs.pop('descriptor_cls')
        block_type = kwargs.pop('block_type')
        def_id = kwargs.pop('definition_id')
        usage_id = kwargs.pop('usage_id')

        block = runtime.construct_xblock_from_class(
            desc_cls,
            ScopeIds(None, block_type, def_id, usage_id),
            DictFieldData(dict(**kwargs))
        )
        block.save()
        return block


class LeafModuleFactory(LeafDescriptorFactory):
    """
    Factory to generate leaf XModuleDescriptors that are prepped to be
    used as XModules.
    """
    @post_generation
    def xmodule_runtime(self, create, xmodule_runtime, **kwargs):  # pylint: disable=method-hidden, unused-argument
        """
        Set the xmodule_runtime to make this XModuleDescriptor usable
        as an XModule.
        """
        if xmodule_runtime is None:
            xmodule_runtime = ModuleSystemFactory()

        self.xmodule_runtime = xmodule_runtime


class ContainerDescriptorFactory(LeafDescriptorFactory):
    """
    Factory to generate XModuleDescriptors that are containers.
    """
    runtime = SubFactory(ContainerDescriptorRuntimeFactory)
    children = list(range(3))


class ContainerModuleFactory(LeafModuleFactory):
    """
    Factory to generate XModuleDescriptors that are containers
    and are ready to act as XModules.
    """
    @lazy_attribute
    def xmodule_runtime(self):
        return ContainerModuleRuntimeFactory(depth=self.depth)  # pylint: disable=no-member


@ddt.ddt
class XBlockWrapperTestMixin(object):
    """
    This is a mixin for building tests of the implementation of the XBlock
    api by wrapping XModule native functions.

    You can create an actual test case by inheriting from this class and UnitTest,
    and implement skip_if_invalid and check_property.
    """

    def skip_if_invalid(self, descriptor_cls):
        """
        Raise SkipTest if this descriptor_cls shouldn't be tested.
        """
        pass

    def check_property(self, descriptor):
        """
        Execute assertions to verify that the property under test is true for
        the supplied descriptor.
        """
        raise SkipTest("check_property not defined")

    # Test that for all of the leaf XModule Descriptors,
    # the test property holds
    @ddt.data(*flatten(LEAF_XMODULES))
    def test_leaf_node(self, cls_and_fields):
        descriptor_cls, fields = cls_and_fields
        self.skip_if_invalid(descriptor_cls)
        descriptor = LeafModuleFactory(descriptor_cls=descriptor_cls, **fields)
        mocked_course = Mock()
        modulestore = Mock()
        modulestore.get_course.return_value = mocked_course
        # pylint: disable=no-member
        descriptor.runtime.id_reader.get_definition_id = Mock(return_value='a')
        descriptor.runtime.modulestore = modulestore
        if hasattr(descriptor, '_xmodule'):
            descriptor._xmodule.graded = 'False'
        self.check_property(descriptor)

    # Test that when an xmodule is generated from descriptor_cls
    # with only xmodule children, the test property holds
    @ddt.data(*flatten(CONTAINER_XMODULES))
    def test_container_node_xmodules_only(self, cls_and_fields):
        descriptor_cls, fields = cls_and_fields
        self.skip_if_invalid(descriptor_cls)
        descriptor = ContainerModuleFactory(descriptor_cls=descriptor_cls, depth=2, **fields)
        descriptor.runtime.id_reader.get_definition_id = Mock(return_value='a')
        self.check_property(descriptor)

    # Test that when an xmodule is generated from descriptor_cls
    # with mixed xmodule and xblock children, the test property holds
    @ddt.data(*flatten(CONTAINER_XMODULES))
    def test_container_node_mixed(self, cls_and_fields):
        raise SkipTest("XBlock support in XDescriptor not yet fully implemented")

    # Test that when an xmodule is generated from descriptor_cls
    # with only xblock children, the test property holds
    @ddt.data(*flatten(CONTAINER_XMODULES))
    def test_container_node_xblocks_only(self, cls_and_fields):
        raise SkipTest("XBlock support in XModules not yet fully implemented")


class TestStudentView(XBlockWrapperTestMixin, TestCase):
    """
    This tests that student_view and XModule.get_html produce the same results.
    """

    def skip_if_invalid(self, descriptor_cls):
        pure_xblock_class = issubclass(descriptor_cls, XBlock) and not issubclass(descriptor_cls, XModuleDescriptor)
        if pure_xblock_class:
            student_view = descriptor_cls.student_view
        else:
            student_view = descriptor_cls.module_class.student_view
        if student_view != XModule.student_view:
            raise SkipTest(descriptor_cls.__name__ + " implements student_view")

    def check_property(self, descriptor):
        """
        Assert that both student_view and get_html render the same.
        """
        self.assertEqual(
            descriptor._xmodule.get_html(),
            descriptor.render(STUDENT_VIEW).content
        )


class TestStudioView(XBlockWrapperTestMixin, TestCase):
    """
    This tests that studio_view and XModuleDescriptor.get_html produce the same results
    """

    def skip_if_invalid(self, descriptor_cls):
        if descriptor_cls in NOT_STUDIO_EDITABLE:
            raise SkipTest(descriptor_cls.__name__ + " is not editable in studio")

        pure_xblock_class = issubclass(descriptor_cls, XBlock) and not issubclass(descriptor_cls, XModuleDescriptor)
        if pure_xblock_class:
            raise SkipTest(descriptor_cls.__name__ + " is a pure XBlock and implements studio_view")
        elif descriptor_cls.studio_view != XModuleDescriptor.studio_view:
            raise SkipTest(descriptor_cls.__name__ + " implements studio_view")

    def check_property(self, descriptor):
        """
        Assert that studio_view and get_html render the same.
        """
        html = descriptor.get_html()
        rendered_content = descriptor.render(STUDIO_VIEW).content
        self.assertEqual(html, rendered_content)


@ddt.ddt
class TestXModuleHandler(TestCase):
    """
    Tests that the xmodule_handler function correctly wraps handle_ajax
    """

    def setUp(self):
        super(TestXModuleHandler, self).setUp()
        self.module = XModule(descriptor=Mock(), field_data=Mock(), runtime=Mock(), scope_ids=Mock())
        self.module.handle_ajax = Mock(return_value='{}')
        self.request = webob.Request({})

    def test_xmodule_handler_passed_data(self):
        self.module.xmodule_handler(self.request)
        self.module.handle_ajax.assert_called_with(None, MultiDict(self.request.POST))

    def test_xmodule_handler_dispatch(self):
        self.module.xmodule_handler(self.request, 'dispatch')
        self.module.handle_ajax.assert_called_with('dispatch', MultiDict(self.request.POST))

    def test_xmodule_handler_return_value(self):
        response = self.module.xmodule_handler(self.request)
        self.assertIsInstance(response, webob.Response)
        self.assertEqual(response.body.decode('utf-8'), '{}')

    @ddt.data(
        u'{"test_key": "test_value"}',
        '{"test_key": "test_value"}',
    )
    def test_xmodule_handler_with_data(self, response_data):
        """
        Tests that xmodule_handler function correctly wraps handle_ajax when handle_ajax response is either
        str or unicode.
        """

        self.module.handle_ajax = Mock(return_value=response_data)
        response = self.module.xmodule_handler(self.request)
        self.assertIsInstance(response, webob.Response)
        self.assertEqual(response.body.decode('utf-8'), '{"test_key": "test_value"}')


class TestXmlExport(XBlockWrapperTestMixin, TestCase):
    """
    This tests that XModuleDescriptor.export_course_to_xml and add_xml_to_node produce the same results.
    """

    def skip_if_invalid(self, descriptor_cls):
        if descriptor_cls.add_xml_to_node != XModuleDescriptor.add_xml_to_node:
            raise SkipTest(descriptor_cls.__name__ + " implements add_xml_to_node")

    def check_property(self, descriptor):
        xmodule_api_fs = MemoryFS()
        xblock_api_fs = MemoryFS()

        descriptor.runtime.export_fs = xblock_api_fs
        xblock_node = etree.Element('unknown')
        descriptor.add_xml_to_node(xblock_node)

        xmodule_node = etree.fromstring(descriptor.export_to_xml(xmodule_api_fs))

        self.assertEqual(list(xmodule_api_fs.walk()), list(xblock_api_fs.walk()))
        self.assertEqual(etree.tostring(xmodule_node), etree.tostring(xblock_node))


class TestPublicView(XBlockWrapperTestMixin, TestCase):
    """
    This tests that default public_view shows the correct message.
    """

    def skip_if_invalid(self, descriptor_cls):
        pure_xblock_class = issubclass(descriptor_cls, XBlock) and not issubclass(descriptor_cls, XModuleDescriptor)
        if pure_xblock_class:
            public_view = descriptor_cls.public_view
        else:
            public_view = descriptor_cls.module_class.public_view
        if public_view != XModule.public_view:
            raise SkipTest(descriptor_cls.__name__ + " implements public_view")

    def check_property(self, descriptor):
        """
        Assert that public_view contains correct message.
        """
        if descriptor.display_name:
            self.assertIn(
                descriptor.display_name,
                descriptor.render(PUBLIC_VIEW).content
            )
        else:
            self.assertIn(
                "This content is only accessible",
                descriptor.render(PUBLIC_VIEW).content
            )
