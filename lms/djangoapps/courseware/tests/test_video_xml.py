# -*- coding: utf-8 -*-
"""Test for Video Xmodule functional logic.
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

from xmodule.video_module import VideoDescriptor, VideoModule
from xmodule.modulestore import Location
from xmodule.tests import test_system
from xmodule.tests.test_logic import LogicTest


class VideoFactory(object):
    """A helper class to create video modules with various parameters
    for testing.
    """

    # tag that uses youtube videos
    sample_problem_xml_youtube = """
        <video show_captions="true"
        youtube="0.75:jNCf2gIqpeE,1.0:ZwkTiUPN0mg,1.25:rsq9auxASqI,1.50:kMyNdzVHHgg"
        data_dir=""
        caption_asset_path=""
        autoplay="true"
        from="01:00:03" to="01:00:10"
        >
            <source src=".../mit-3091x/M-3091X-FA12-L21-3_100.mp4"/>
        </video>
    """

    @staticmethod
    def create():
        """Method return Video Xmodule instance."""
        location = Location(["i4x", "edX", "video", "default",
                             "SampleProblem{0}".format(1)])
        model_data = {'data': VideoFactory.sample_problem_xml_youtube}

        descriptor = Mock(weight="1")

        system = test_system()
        system.render_template = lambda template, context: context
        module = VideoModule(system, location, descriptor, model_data)

        return module


class VideoModuleLogicTest(LogicTest):
    """Tests for logic of Video Xmodule."""

    descriptor_class = VideoDescriptor

    raw_model_data = {
        'data': '<video />'
    }

    def test_get_timeframe_no_parameters(self):
        """Make sure that timeframe() works correctly w/o parameters"""
        xmltree = etree.fromstring('<video>test</video>')
        output = self.xmodule.get_timeframe(xmltree)
        self.assertEqual(output, ('', ''))

    def test_get_timeframe_with_one_parameter(self):
        """Make sure that timeframe() works correctly with one parameter"""
        xmltree = etree.fromstring(
            '<video from="00:04:07">test</video>'
        )
        output = self.xmodule.get_timeframe(xmltree)
        self.assertEqual(output, (247, ''))

    def test_get_timeframe_with_two_parameters(self):
        """Make sure that timeframe() works correctly with two parameters"""
        xmltree = etree.fromstring(
            '''<video
                    from="00:04:07"
                    to="13:04:39"
                >test</video>'''
        )
        output = self.xmodule.get_timeframe(xmltree)
        self.assertEqual(output, (247, 47079))


class VideoModuleUnitTest(unittest.TestCase):
    """Unit tests for Video Xmodule."""

    def test_video_constructor(self):
        """Make sure that all parameters extracted correclty from xml"""
        module = VideoFactory.create()

        # `get_html` return only context, cause we
        # overwrite `system.render_template`
        context = module.get_html()
        expected_context = {
            'track': None,
            'show_captions': 'true',
            'display_name': 'SampleProblem1',
            'id': 'i4x-edX-video-default-SampleProblem1',
            'end': 3610.0,
            'caption_asset_path': '/static/subs/',
            'source': '.../mit-3091x/M-3091X-FA12-L21-3_100.mp4',
            'streams': '0.75:jNCf2gIqpeE,1.0:ZwkTiUPN0mg,1.25:rsq9auxASqI,1.50:kMyNdzVHHgg',
            'normal_speed_video_id': 'ZwkTiUPN0mg',
            'position': 0,
            'start': 3603.0
        }
        self.assertDictEqual(context, expected_context)

        self.assertEqual(
            module.youtube,
            '0.75:jNCf2gIqpeE,1.0:ZwkTiUPN0mg,1.25:rsq9auxASqI,1.50:kMyNdzVHHgg')

        self.assertEqual(
            module.video_list(),
            module.youtube)

        self.assertEqual(
            module.position,
            0)

        self.assertDictEqual(
            json.loads(module.get_instance_state()),
            {'position': 0})
