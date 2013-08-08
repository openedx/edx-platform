# -*- coding: utf-8 -*-
# pylint: disable=W0212

"""Test for VideoAlpha Xmodule functional logic.
These test data read from xml, not from mongo.

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

from django.conf import settings

from xmodule.videoalpha_module import (
    VideoAlphaDescriptor, _create_youtube_string)
from xmodule.modulestore import Location
from xmodule.tests import get_test_system, LogicTest


SOURCE_XML = """
    <videoalpha show_captions="true"
    display_name="A Name"
    youtube="0.75:jNCf2gIqpeE,1.0:ZwkTiUPN0mg,1.25:rsq9auxASqI,1.50:kMyNdzVHHgg"
    sub="a_sub_file.srt.sjson"
    start_time="01:00:03" end_time="01:00:10"
    >
        <source src="example.mp4"/>
        <source src="example.webm"/>
        <source src="example.ogv"/>
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
        model_data = {'data': VideoAlphaFactory.sample_problem_xml_youtube,
                      'location': location}

        system = get_test_system()
        system.render_template = lambda template, context: context

        descriptor = VideoAlphaDescriptor(system, model_data)

        module = descriptor.xmodule(system)

        return module


class VideoAlphaModuleUnitTest(unittest.TestCase):
    """Unit tests for VideoAlpha Xmodule."""

    def test_videoalpha_get_html(self):
        """Make sure that all parameters extracted correclty from xml"""
        module = VideoAlphaFactory.create()
        module.runtime.render_template = lambda template, context: context

        sources = {
            'main': 'example.mp4',
            'mp4': 'example.mp4',
            'webm': 'example.webm',
            'ogv': 'example.ogv'
        }

        expected_context = {
            'caption_asset_path': '/static/subs/',
            'sub': 'a_sub_file.srt.sjson',
            'data_dir': getattr(self, 'data_dir', None),
            'display_name': 'A Name',
            'end': 3610.0,
            'start': 3603.0,
            'id': module.location.html_id(),
            'show_captions': 'true',
            'sources': sources,
            'youtube_streams': _create_youtube_string(module),
            'track': '',
            'autoplay': settings.MITX_FEATURES.get('AUTOPLAY_VIDEOS', True)
        }

        self.assertEqual(module.get_html(), expected_context)

    def test_videoalpha_instance_state(self):
        module = VideoAlphaFactory.create()

        self.assertDictEqual(
            json.loads(module.get_instance_state()),
            {'position': 0})


class VideoAlphaModuleLogicTest(LogicTest):
    """Tests for logic of VideoAlpha Xmodule."""

    descriptor_class = VideoAlphaDescriptor

    raw_model_data = {
        'data': '<video />'
    }

    def test_parse_time(self):
        """Ensure that times are parsed correctly into seconds."""
        output = VideoAlphaDescriptor._parse_time('00:04:07')
        self.assertEqual(output, 247)

    def test_parse_time_none(self):
        """Check parsing of None."""
        output = VideoAlphaDescriptor._parse_time(None)
        self.assertEqual(output, '')

    def test_parse_time_empty(self):
        """Check parsing of the empty string."""
        output = VideoAlphaDescriptor._parse_time('')
        self.assertEqual(output, '')

    def test_parse_youtube(self):
        """Test parsing old-style Youtube ID strings into a dict."""
        youtube_str = '0.75:jNCf2gIqpeE,1.00:ZwkTiUPN0mg,1.25:rsq9auxASqI,1.50:kMyNdzVHHgg'
        output = VideoAlphaDescriptor._parse_youtube(youtube_str)
        self.assertEqual(output, {'0.75': 'jNCf2gIqpeE',
                                  '1.00': 'ZwkTiUPN0mg',
                                  '1.25': 'rsq9auxASqI',
                                  '1.50': 'kMyNdzVHHgg'})

    def test_parse_youtube_one_video(self):
        """
        Ensure that all keys are present and missing speeds map to the
        empty string.
        """
        youtube_str = '0.75:jNCf2gIqpeE'
        output = VideoAlphaDescriptor._parse_youtube(youtube_str)
        self.assertEqual(output, {'0.75': 'jNCf2gIqpeE',
                                  '1.00': '',
                                  '1.25': '',
                                  '1.50': ''})

    def test_parse_youtube_key_format(self):
        """
        Make sure that inconsistent speed keys are parsed correctly.
        """
        youtube_str = '1.00:p2Q6BrNhdh8'
        youtube_str_hack = '1.0:p2Q6BrNhdh8'
        self.assertEqual(
            VideoAlphaDescriptor._parse_youtube(youtube_str),
            VideoAlphaDescriptor._parse_youtube(youtube_str_hack)
        )

    def test_parse_youtube_empty(self):
        """
        Some courses have empty youtube attributes, so we should handle
        that well.
        """
        self.assertEqual(VideoAlphaDescriptor._parse_youtube(''),
                         {'0.75': '',
                          '1.00': '',
                          '1.25': '',
                          '1.50': ''})
