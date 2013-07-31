# -*- coding: utf-8 -*-
"""Test for VideoAlpha Xmodule functional logic.
These tests data readed from xml, not from mongo.

We have a ModuleStoreTestCase class defined in
common/lib/xmodule/xmodule/modulestore/tests/django_utils.py.
You can search for usages of this in the cms and lms tests for examples.
You use this so that it will do things like point the modulestore
setting to mongo, flush the contentstore before and after, load the
templates, etc.
You can then use the CourseFactory and XModuleItemFactory as defined in
common/lib/xmodule/xmodule/modulestore/tests/factories.py to create the
course, section, subsection, unit, etc.
"""

import json
import unittest
from mock import Mock
from lxml import etree

from django.conf import settings

from xmodule.videoalpha_module import VideoAlphaDescriptor, VideoAlphaModule
from xmodule.modulestore import Location
from xmodule.tests import get_test_system
from xmodule.tests.test_logic import LogicTest


SOURCE_XML = """
    <videoalpha show_captions="true"
    youtube="0.75:jNCf2gIqpeE,1.0:ZwkTiUPN0mg,1.25:rsq9auxASqI,1.50:kMyNdzVHHgg"
    data_dir=""
    caption_asset_path=""
    autoplay="true"
    start_time="01:00:03" end_time="01:00:10"
    >
        <source src=".../mit-3091x/M-3091X-FA12-L21-3_100.mp4"/>
        <source src=".../mit-3091x/M-3091X-FA12-L21-3_100.webm"/>
        <source src=".../mit-3091x/M-3091X-FA12-L21-3_100.ogv"/>
    </videoalpha>
"""


class VideoAlphaFactory(object):
    """A helper class to create videoalpha modules with various parameters
    for testing.
    """

    # tag that uses youtube videos
    sample_problem_xml_youtube = SOURCE_XML

    @staticmethod
    def create():
        """Method return VideoAlpha Xmodule instance."""
        location = Location(["i4x", "edX", "videoalpha", "default",
                             "SampleProblem1"])
        model_data = {'data': VideoAlphaFactory.sample_problem_xml_youtube}

        descriptor = Mock(weight="1")

        system = get_test_system()
        system.render_template = lambda template, context: context
        VideoAlphaModule.location = location
        module = VideoAlphaModule(system, descriptor, model_data)

        return module


class VideoAlphaModuleTest(LogicTest):
    """Tests for logic of VideoAlpha Xmodule."""

    descriptor_class = VideoAlphaDescriptor

    raw_model_data = {
        'data': '<videoalpha />'
    }

    def test_get_timeframe_no_parameters(self):
        xmltree = etree.fromstring('<videoalpha>test</videoalpha>')
        output = self.xmodule.get_timeframe(xmltree)
        self.assertEqual(output, ('', ''))

    def test_get_timeframe_with_one_parameter(self):
        xmltree = etree.fromstring(
            '<videoalpha start_time="00:04:07">test</videoalpha>'
        )
        output = self.xmodule.get_timeframe(xmltree)
        self.assertEqual(output, (247, ''))

    def test_get_timeframe_with_two_parameters(self):
        xmltree = etree.fromstring(
            '''<videoalpha
                    start_time="00:04:07"
                    end_time="13:04:39"
                >test</videoalpha>'''
        )
        output = self.xmodule.get_timeframe(xmltree)
        self.assertEqual(output, (247, 47079))


class VideoAlphaModuleUnitTest(unittest.TestCase):
    """Unit tests for VideoAlpha Xmodule."""

    def test_videoalpha_constructor(self):
        """Make sure that all parameters extracted correclty from xml"""
        module = VideoAlphaFactory.create()
        module.runtime.render_template = lambda template, context: unicode((template, sorted(context.items())))

        fragment = module.runtime.render(module, None, 'student_view')
        expected_context = {
            'caption_asset_path': '/static/subs/',
            'sub': module.sub,
            'data_dir': getattr(self, 'data_dir', None),
            'display_name': module.display_name_with_default,
            'end': module.end_time,
            'start': module.start_time,
            'id': module.location.html_id(),
            'show_captions': module.show_captions,
            'sources': module.sources,
            'youtube_streams': module.youtube_streams,
            'track': module.track,
            'autoplay': settings.MITX_FEATURES.get('AUTOPLAY_VIDEOS', True)
        }
        self.assertEqual(fragment.content, module.runtime.render_template('videoalpha.html', expected_context))

        self.assertDictEqual(
            json.loads(module.get_instance_state()),
            {'position': 0})
