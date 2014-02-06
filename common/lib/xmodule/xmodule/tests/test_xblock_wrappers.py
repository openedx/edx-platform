"""
Tests for the wrapping layer that provides the XBlock API using XModule/Descriptor
functionality
"""
# For tests, ignore access to protected members
# pylint: disable=protected-access

import webob
import ddt
from mock import Mock
from unittest.case import SkipTest, TestCase

from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds

from xmodule.modulestore import Location

from xmodule.x_module import ModuleSystem, XModule, XModuleDescriptor
from xmodule.mako_module import MakoDescriptorSystem
from xmodule.annotatable_module import AnnotatableDescriptor
from xmodule.capa_module import CapaDescriptor
from xmodule.course_module import CourseDescriptor
from xmodule.combined_open_ended_module import CombinedOpenEndedDescriptor
from xmodule.discussion_module import DiscussionDescriptor
from xmodule.error_module import ErrorDescriptor
from xmodule.gst_module import GraphicalSliderToolDescriptor
from xmodule.html_module import HtmlDescriptor
from xmodule.peer_grading_module import PeerGradingDescriptor
from xmodule.poll_module import PollDescriptor
from xmodule.word_cloud_module import WordCloudDescriptor
from xmodule.crowdsource_hinter import CrowdsourceHinterDescriptor
from xmodule.video_module import VideoDescriptor
from xmodule.seq_module import SequenceDescriptor
from xmodule.conditional_module import ConditionalDescriptor
from xmodule.randomize_module import RandomizeDescriptor
from xmodule.vertical_module import VerticalDescriptor
from xmodule.wrapper_module import WrapperDescriptor
from xmodule.tests import get_test_descriptor_system, get_test_system

LEAF_XMODULES = (
    AnnotatableDescriptor,
    CapaDescriptor,
    CombinedOpenEndedDescriptor,
    DiscussionDescriptor,
    GraphicalSliderToolDescriptor,
    HtmlDescriptor,
    PeerGradingDescriptor,
    PollDescriptor,
    WordCloudDescriptor,
    # This is being excluded because it has dependencies on django
    #VideoDescriptor,
)


CONTAINER_XMODULES = (
    ConditionalDescriptor,
    CourseDescriptor,
    CrowdsourceHinterDescriptor,
    RandomizeDescriptor,
    SequenceDescriptor,
    VerticalDescriptor,
    WrapperDescriptor,
)

# These modules are editable in studio yet
NOT_STUDIO_EDITABLE = (
    CrowdsourceHinterDescriptor,
    GraphicalSliderToolDescriptor,
    PollDescriptor
)


def leaf_module_runtime():
    return get_test_system()


def leaf_descriptor(descriptor_cls, idx=0):
    location = Location('i4x://org/course/category/name')
    runtime = get_test_descriptor_system()
    return runtime.construct_xblock_from_class(
        descriptor_cls,
        ScopeIds(None, descriptor_cls.__name__, location, location),
        DictFieldData({'url_name': '{}_{}'.format(descriptor_cls, idx)}),
    )


def leaf_module(descriptor_cls, idx=0):
    """Returns a descriptor that is ready to proxy as an xmodule"""
    descriptor = leaf_descriptor(descriptor_cls, idx)
    descriptor.xmodule_runtime = leaf_module_runtime()
    return descriptor


def container_module_runtime(depth):
    runtime = leaf_module_runtime()
    if depth == 0:
        runtime.get_module.side_effect = lambda x: leaf_module(HtmlDescriptor)
    else:
        runtime.get_module.side_effect = lambda x: container_module(VerticalDescriptor, depth - 1)
    runtime.position = 2
    return runtime


def container_descriptor(descriptor_cls, depth):
    """Return an instance of `descriptor_cls` with `depth` levels of children"""
    location = Location('i4x://org/course/category/name')
    runtime = get_test_descriptor_system()

    if depth == 0:
        runtime.load_item.side_effect = lambda x: leaf_module(HtmlDescriptor)
    else:
        runtime.load_item.side_effect = lambda x: container_module(VerticalDescriptor, depth - 1)

    return runtime.construct_xblock_from_class(
        descriptor_cls,
        ScopeIds(None, descriptor_cls.__name__, location, location),
        DictFieldData({
            'children': range(3)
        }),
    )

def container_module(descriptor_cls, depth):
    """Returns a descriptor that is ready to proxy as an xmodule"""
    descriptor = container_descriptor(descriptor_cls, depth)
    descriptor.xmodule_runtime = container_module_runtime(depth)
    return descriptor


@ddt.ddt
class TestXBlockWrapper(object):

    __test__ = False

    def skip_if_invalid(self, descriptor_cls):
        """
        Raise SkipTest if this descriptor_cls shouldn't be tested.
        """
        pass

    def check_property(self, descriptor):
        raise SkipTest("check_property not defined")

    # Test that for all of the leaf XModule Descriptors,
    # the test property holds
    @ddt.data(*LEAF_XMODULES)
    def test_leaf_node(self, descriptor_cls):
        self.skip_if_invalid(descriptor_cls)
        descriptor = leaf_module(descriptor_cls)
        self.check_property(descriptor)

    # Test that when an xmodule is generated from descriptor_cls
    # with only xmodule children, the test property holds
    @ddt.data(*CONTAINER_XMODULES)
    def test_container_node_xmodules_only(self, descriptor_cls):
        self.skip_if_invalid(descriptor_cls)
        descriptor = container_module(descriptor_cls, 2)
        self.check_property(descriptor)

    # Test that when an xmodule is generated from descriptor_cls
    # with mixed xmodule and xblock children, the test property holds
    @ddt.data(*CONTAINER_XMODULES)
    def test_container_node_mixed(self, descriptor_cls):
        raise SkipTest("XBlock support in XDescriptor not yet fully implemented")

    # Test that when an xmodule is generated from descriptor_cls
    # with only xblock children, the test property holds
    @ddt.data(*CONTAINER_XMODULES)
    def test_container_node_xblocks_only(self, descriptor_cls):
        raise SkipTest("XBlock support in XModules not yet fully implemented")


class TestStudentView(TestXBlockWrapper, TestCase):
    __test__ = True

    def skip_if_invalid(self, descriptor_cls):
        if descriptor_cls.module_class.student_view != XModule.student_view:
            raise SkipTest(descriptor_cls.__name__ + " implements student_view")

    def check_property(self, descriptor):
        """
        Assert that both student_view and get_html render the same.
        """
        self.assertEqual(
            descriptor._xmodule.get_html(),
            descriptor.render('student_view').content
        )


class TestStudioView(TestXBlockWrapper, TestCase):
    __test__ = True

    def skip_if_invalid(self, descriptor_cls):
        if descriptor_cls in NOT_STUDIO_EDITABLE:
            raise SkipTest(descriptor_cls.__name__ + " is not editable in studio")

        if descriptor_cls.studio_view != XModuleDescriptor.studio_view:
            raise SkipTest(descriptor_cls.__name__ + " implements studio_view")

    def check_property(self, descriptor):
        """
        Assert that studio_view and get_html render the same.
        """
        self.assertEqual(descriptor.get_html(), descriptor.render('studio_view').content)


class TestXModuleHandler(TestCase):
    """
    Tests that the xmodule_handler function correctly wraps handle_ajax
    """

    def setUp(self):
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
