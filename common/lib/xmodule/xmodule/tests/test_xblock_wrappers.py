"""
Tests for the wrapping layer that provides the XBlock API using XModule/Descriptor
functionality
"""
# For tests, ignore access to protected members
# pylint: disable=protected-access

from nose.tools import assert_equal  # pylint: disable=E0611
from unittest.case import SkipTest
from mock import Mock

from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds

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
from xmodule.tests import get_test_descriptor_system, mock_render_template

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


class TestXBlockWrapper(object):
    """Helper methods used in test case classes below."""

    @property
    def leaf_module_runtime(self):
        runtime = ModuleSystem(
            render_template=mock_render_template,
            anonymous_student_id='dummy_anonymous_student_id',
            open_ended_grading_interface={},
            static_url='/static',
            ajax_url='dummy_ajax_url',
            get_module=Mock(),
            replace_urls=Mock(),
            track_function=Mock(),
            error_descriptor_class=ErrorDescriptor,
        )
        return runtime

    def leaf_descriptor(self, descriptor_cls):
        location = 'i4x://org/course/category/name'
        runtime = get_test_descriptor_system()
        return runtime.construct_xblock_from_class(
            descriptor_cls,
            ScopeIds(None, descriptor_cls.__name__, location, location),
            DictFieldData({}),
        )

    def leaf_module(self, descriptor_cls):
        """Returns a descriptor that is ready to proxy as an xmodule"""
        descriptor = self.leaf_descriptor(descriptor_cls)
        descriptor.xmodule_runtime = self.leaf_module_runtime
        return descriptor

    def container_module_runtime(self, depth):
        runtime = self.leaf_module_runtime
        if depth == 0:
            runtime.get_module.side_effect = lambda x: self.leaf_module(HtmlDescriptor)
        else:
            runtime.get_module.side_effect = lambda x: self.container_module(VerticalDescriptor, depth - 1)
        runtime.position = 2
        return runtime

    def container_descriptor(self, descriptor_cls, depth):
        """Return an instance of `descriptor_cls` with `depth` levels of children"""
        location = 'i4x://org/course/category/name'
        runtime = get_test_descriptor_system()

        if depth == 0:
            runtime.load_item.side_effect = lambda x: self.leaf_module(HtmlDescriptor)
        else:
            runtime.load_item.side_effect = lambda x: self.container_module(VerticalDescriptor, depth - 1)

        return runtime.construct_xblock_from_class(
            descriptor_cls,
            ScopeIds(None, descriptor_cls.__name__, location, location),
            DictFieldData({
                'children': range(3)
            }),
        )

    def container_module(self, descriptor_cls, depth):
        """Returns a descriptor that is ready to proxy as an xmodule"""
        descriptor = self.container_descriptor(descriptor_cls, depth)
        descriptor.xmodule_runtime = self.container_module_runtime(depth)
        return descriptor

class TestStudentView(TestXBlockWrapper):

    # Test that for all of the leaf XModule Descriptors,
    # the student_view wrapper returns the same thing in its content
    # as get_html returns
    def test_student_view_leaf_node(self):
        for descriptor_cls in LEAF_XMODULES:
            yield self.check_student_view_leaf_node, descriptor_cls

    # Check that when an xmodule is instantiated from descriptor_cls
    # it generates the same thing from student_view that it does from get_html
    def check_student_view_leaf_node(self, descriptor_cls):

        if descriptor_cls.module_class.student_view != XModule.student_view:
            raise SkipTest(descriptor_cls.__name__ + " implements student_view")

        descriptor = self.leaf_module(descriptor_cls)
        assert_equal(
            descriptor._xmodule.get_html(),
            descriptor.render('student_view').content
        )

    # Test that for all container XModule Descriptors,
    # their corresponding XModule renders the same thing using student_view
    # as it does using get_html, under the following conditions:
    # a) All of its descendents are xmodules
    # b) Some of its descendents are xmodules and some are xblocks
    # c) All of its descendents are xblocks
    def test_student_view_container_node(self):
        for descriptor_cls in CONTAINER_XMODULES:
            yield self.check_student_view_container_node_xmodules_only, descriptor_cls
            yield self.check_student_view_container_node_mixed, descriptor_cls
            yield self.check_student_view_container_node_xblocks_only, descriptor_cls

    # Check that when an xmodule is generated from descriptor_cls
    # with only xmodule children, it generates the same html from student_view
    # as it does using get_html
    def check_student_view_container_node_xmodules_only(self, descriptor_cls):

        if descriptor_cls.module_class.student_view != XModule.student_view:
            raise SkipTest(descriptor_cls.__name__ + " implements student_view")

        descriptor = self.container_module(descriptor_cls, 2)
        assert_equal(
            descriptor._xmodule.get_html(),
            descriptor.render('student_view').content
        )

    # Check that when an xmodule is generated from descriptor_cls
    # with mixed xmodule and xblock children, it generates the same html from student_view
    # as it does using get_html
    def check_student_view_container_node_mixed(self, descriptor_cls):
        raise SkipTest("XBlock support in XDescriptor not yet fully implemented")

    # Check that when an xmodule is generated from descriptor_cls
    # with only xblock children, it generates the same html from student_view
    # as it does using get_html
    def check_student_view_container_node_xblocks_only(self, descriptor_cls):
        raise SkipTest("XBlock support in XModules not yet fully implemented")


class TestStudioView(TestXBlockWrapper):

    # Test that for all of the Descriptors listed in LEAF_XMODULES,
    # the studio_view wrapper returns the same thing in its content
    # as get_html returns
    def test_studio_view_leaf_node(self):
        for descriptor_cls in LEAF_XMODULES:
            yield self.check_studio_view_leaf_node, descriptor_cls

    # Check that when a descriptor is instantiated from descriptor_cls
    # it generates the same thing from studio_view that it does from get_html
    def check_studio_view_leaf_node(self, descriptor_cls):
        if descriptor_cls in NOT_STUDIO_EDITABLE:
            raise SkipTest(descriptor_cls.__name__ + " is not editable in studio")

        if descriptor_cls.studio_view != XModuleDescriptor.studio_view:
            raise SkipTest(descriptor_cls.__name__ + " implements studio_view")

        descriptor = self.leaf_descriptor(descriptor_cls)
        assert_equal(descriptor.get_html(), descriptor.render('studio_view').content)


    # Test that for all of the Descriptors listed in CONTAINER_XMODULES
    # render the same thing using studio_view as they do using get_html, under the following conditions:
    # a) All of its descendants are xmodules
    # b) Some of its descendants are xmodules and some are xblocks
    # c) All of its descendants are xblocks
    def test_studio_view_container_node(self):
        for descriptor_cls in CONTAINER_XMODULES:
            yield self.check_studio_view_container_node_xmodules_only, descriptor_cls
            yield self.check_studio_view_container_node_mixed, descriptor_cls
            yield self.check_studio_view_container_node_xblocks_only, descriptor_cls


    # Check that when a descriptor is generated from descriptor_cls
    # with only xmodule children, it generates the same html from studio_view
    # as it does using get_html
    def check_studio_view_container_node_xmodules_only(self, descriptor_cls):
        if descriptor_cls in NOT_STUDIO_EDITABLE:
            raise SkipTest(descriptor_cls.__name__ + "is not editable in studio")

        if descriptor_cls.studio_view != XModuleDescriptor.studio_view:
            raise SkipTest(descriptor_cls.__name__ + " implements studio_view")

        descriptor = self.container_descriptor(descriptor_cls, 2)
        assert_equal(descriptor.get_html(), descriptor.render('studio_view').content)

    # Check that when a descriptor is generated from descriptor_cls
    # with mixed xmodule and xblock children, it generates the same html from studio_view
    # as it does using get_html
    def check_studio_view_container_node_mixed(self, descriptor_cls):
        if descriptor_cls in NOT_STUDIO_EDITABLE:
            raise SkipTest(descriptor_cls.__name__ + "is not editable in studio")

        raise SkipTest("XBlock support in XDescriptor not yet fully implemented")

    # Check that when a descriptor is generated from descriptor_cls
    # with only xblock children, it generates the same html from studio_view
    # as it does using get_html
    def check_studio_view_container_node_xblocks_only(self, descriptor_cls):
        if descriptor_cls in NOT_STUDIO_EDITABLE:
            raise SkipTest(descriptor_cls.__name__ + "is not editable in studio")

        raise SkipTest("XBlock support in XModules not yet fully implemented")
