"""
Tests for the wrapping layer that provides the XBlock API using XModule/Descriptor
functionality
"""

from nose.tools import assert_equal
from unittest.case import SkipTest
from mock import Mock

from xmodule.annotatable_module import AnnotatableDescriptor
from xmodule.capa_module import CapaDescriptor
from xmodule.course_module import CourseDescriptor
from xmodule.combined_open_ended_module import CombinedOpenEndedDescriptor
from xmodule.discussion_module import DiscussionDescriptor
from xmodule.gst_module import GraphicalSliderToolDescriptor
from xmodule.html_module import HtmlDescriptor
from xmodule.peer_grading_module import PeerGradingDescriptor
from xmodule.poll_module import PollDescriptor
from xmodule.video_module import VideoDescriptor
from xmodule.word_cloud_module import WordCloudDescriptor
from xmodule.crowdsource_hinter import CrowdsourceHinterDescriptor
from xmodule.videoalpha_module import VideoAlphaDescriptor
from xmodule.seq_module import SequenceDescriptor
from xmodule.conditional_module import ConditionalDescriptor
from xmodule.randomize_module import RandomizeDescriptor
from xmodule.vertical_module import VerticalDescriptor
from xmodule.wrapper_module import WrapperDescriptor

LEAF_XMODULES = (
    AnnotatableDescriptor,
    CapaDescriptor,
    CombinedOpenEndedDescriptor,
    DiscussionDescriptor,
    GraphicalSliderToolDescriptor,
    HtmlDescriptor,
    PeerGradingDescriptor,
    PollDescriptor,
    VideoDescriptor,
    # This is being excluded because it has dependencies on django
    #VideoAlphaDescriptor,
    WordCloudDescriptor,
)


CONTAINER_XMODULES = (
    CrowdsourceHinterDescriptor,
    CourseDescriptor,
    SequenceDescriptor,
    ConditionalDescriptor,
    RandomizeDescriptor,
    VerticalDescriptor,
    WrapperDescriptor,
    CourseDescriptor,
)


class TestXBlockWrapper(object):

    @property
    def leaf_module_runtime(self):
        runtime = Mock()
        runtime.render_template = lambda *args, **kwargs: unicode((args, kwargs))
        runtime.anonymous_student_id = 'anonymous_student_id'
        runtime.open_ended_grading_interface = {}
        runtime.seed = 5
        runtime.get = lambda x: getattr(runtime, x)
        runtime.position = 2
        runtime.ajax_url = 'ajax_url'
        runtime.xblock_model_data = lambda d: d._model_data
        return runtime

    @property
    def leaf_descriptor_runtime(self):
        runtime = Mock()
        runtime.render_template = lambda *args, **kwargs: unicode((args, kwargs))
        return runtime

    def leaf_descriptor(self, descriptor_cls):
        return descriptor_cls(
            self.leaf_descriptor_runtime,
            {'location': 'i4x://org/course/catagory/name'}
        )

    def leaf_module(self, descriptor_cls):
        return self.leaf_descriptor(descriptor_cls).xmodule(self.leaf_module_runtime)

    def container_module_runtime(self, depth):
        runtime = self.leaf_module_runtime
        if depth == 0:
            runtime.get_module.side_effect = lambda x: self.leaf_module(HtmlDescriptor)
        else:
            runtime.get_module.side_effect = lambda x: self.container_module(VerticalDescriptor, depth-1)
        return runtime

    @property
    def container_descriptor_runtime(self):
        runtime = Mock()
        runtime.render_template = lambda *args, **kwargs: unicode((args, kwargs))
        return runtime

    def container_descriptor(self, descriptor_cls):
        return descriptor_cls(
            self.container_descriptor_runtime,
            {
                'location': 'i4x://org/course/catagory/name',
                'children': range(3)
            }
        )

    def container_module(self, descriptor_cls, depth):
        return self.container_descriptor(descriptor_cls).xmodule(self.container_module_runtime(depth))

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
        xmodule = self.leaf_module(descriptor_cls)
        assert_equal(xmodule.get_html(), xmodule.student_view(None).content)


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
        xmodule = self.container_module(descriptor_cls, 2)
        assert_equal(xmodule.get_html(), xmodule.student_view(None).content)

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

