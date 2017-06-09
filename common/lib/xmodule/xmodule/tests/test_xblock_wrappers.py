"""
Tests for the wrapping layer that provides the XBlock API using XModule/Descriptor
functionality
"""
# For tests, ignore access to protected members
# pylint: disable=protected-access

import webob
import ddt
from factory import (
    BUILD_STRATEGY,
    Factory,
    lazy_attribute,
    LazyAttributeSequence,
    post_generation,
    SubFactory,
    use_strategy,
)
from fs.memoryfs import MemoryFS
from lxml import etree
from mock import Mock
from unittest.case import SkipTest, TestCase

from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds
from xblock.core import XBlock

from opaque_keys.edx.locations import Location

from xmodule.x_module import ModuleSystem, XModule, XModuleDescriptor, DescriptorSystem, STUDENT_VIEW, STUDIO_VIEW
from xmodule.annotatable_module import AnnotatableDescriptor
from xmodule.capa_module import CapaDescriptor
from xmodule.course_module import CourseDescriptor
from xmodule.html_module import HtmlDescriptor
from xmodule.poll_module import PollDescriptor
from xmodule.word_cloud_module import WordCloudDescriptor
#from xmodule.video_module import VideoDescriptor
from xmodule.seq_module import SequenceDescriptor
from xmodule.conditional_module import ConditionalDescriptor
from xmodule.randomize_module import RandomizeDescriptor
from xmodule.vertical_block import VerticalBlock
from xmodule.wrapper_module import WrapperBlock
from xmodule.tests import get_test_descriptor_system, get_test_system


# A dictionary that maps specific XModuleDescriptor classes without children
# to a list of sample field values to test with.
# TODO: Add more types of sample data
LEAF_XMODULES = {
    AnnotatableDescriptor: [{}],
    CapaDescriptor: [{}],
    HtmlDescriptor: [{}],
    PollDescriptor: [{'display_name': 'Poll Display Name'}],
    WordCloudDescriptor: [{}],
    # This is being excluded because it has dependencies on django
    #VideoDescriptor,
}


# A dictionary that maps specific XModuleDescriptor classes with children
# to a list of sample field values to test with.
# TODO: Add more types of sample data
CONTAINER_XMODULES = {
    ConditionalDescriptor: [{}],
    CourseDescriptor: [{}],
    RandomizeDescriptor: [{}],
    SequenceDescriptor: [{}],
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
    for cls, fields_list in class_dict.items():
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
            self.get_module.side_effect = lambda x: LeafModuleFactory(descriptor_cls=HtmlDescriptor)
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
            self.load_item.side_effect = lambda x: LeafModuleFactory(descriptor_cls=HtmlDescriptor)
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
    # pylint: disable=missing-docstring

    class Meta(object):
        model = XModuleDescriptor

    runtime = SubFactory(DescriptorSystemFactory)
    url_name = LazyAttributeSequence('{.block_type}_{}'.format)

    @lazy_attribute
    def location(self):
        return Location('org', 'course', 'run', 'category', self.url_name, None)

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
    children = range(3)


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

    def check_property(self, descriptor):  # pylint: disable=unused-argument
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
        descriptor._xmodule.graded = 'False'
        self.check_property(descriptor)

    # Test that when an xmodule is generated from descriptor_cls
    # with only xmodule children, the test property holds
    @ddt.data(*flatten(CONTAINER_XMODULES))
    def test_container_node_xmodules_only(self, cls_and_fields):
        descriptor_cls, fields = cls_and_fields
        self.skip_if_invalid(descriptor_cls)
        descriptor = ContainerModuleFactory(descriptor_cls=descriptor_cls, depth=2, **fields)
        # pylint: disable=no-member
        descriptor.runtime.id_reader.get_definition_id = Mock(return_value='a')
        self.check_property(descriptor)

    # Test that when an xmodule is generated from descriptor_cls
    # with mixed xmodule and xblock children, the test property holds
    @ddt.data(*flatten(CONTAINER_XMODULES))
    def test_container_node_mixed(self, cls_and_fields):  # pylint: disable=unused-argument
        raise SkipTest("XBlock support in XDescriptor not yet fully implemented")

    # Test that when an xmodule is generated from descriptor_cls
    # with only xblock children, the test property holds
    @ddt.data(*flatten(CONTAINER_XMODULES))
    def test_container_node_xblocks_only(self, cls_and_fields):  # pylint: disable=unused-argument
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
        self.module.handle_ajax.assert_called_with(None, self.request.POST)

    def test_xmodule_handler_dispatch(self):
        self.module.xmodule_handler(self.request, 'dispatch')
        self.module.handle_ajax.assert_called_with('dispatch', self.request.POST)

    def test_xmodule_handler_return_value(self):
        response = self.module.xmodule_handler(self.request)
        self.assertIsInstance(response, webob.Response)
        self.assertEqual(response.body, '{}')


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

        self.assertEquals(list(xmodule_api_fs.walk()), list(xblock_api_fs.walk()))
        self.assertEquals(etree.tostring(xmodule_node), etree.tostring(xblock_node))
