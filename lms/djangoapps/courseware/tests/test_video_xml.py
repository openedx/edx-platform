# -*- coding: utf-8 -*-
# pylint: disable=protected-access

"""Test for Video Xmodule functional logic.
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
from nose.plugins.attrib import attr

from xmodule.video_module import VideoDescriptor
from xmodule.tests import LogicTest


SOURCE_XML = """
    <video show_captions="true"
    display_name="A Name"
    youtube="0.75:jNCf2gIqpeE,1.0:ZwkTiUPN0mg,1.25:rsq9auxASqI,1.50:kMyNdzVHHgg"
    sub="a_sub_file.srt.sjson"
    download_video="true"
    start_time="01:00:03" end_time="01:00:10"
    >
        <source src="example.mp4"/>
        <source src="example.webm"/>
        <transcript language="uk" src="ukrainian_translation.srt" />
    </video>
"""


@attr(shard=1)
class VideoModuleLogicTest(LogicTest):
    """Tests for logic of Video Xmodule."""

    descriptor_class = VideoDescriptor

    raw_field_data = {
        'data': '<video />'
    }

    def test_parse_youtube(self):
        """Test parsing old-style Youtube ID strings into a dict."""
        youtube_str = '0.75:jNCf2gIqpeE,1.00:ZwkTiUPN0mg,1.25:rsq9auxASqI,1.50:kMyNdzVHHgg'
        output = VideoDescriptor._parse_youtube(youtube_str)
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
        output = VideoDescriptor._parse_youtube(youtube_str)
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
            VideoDescriptor._parse_youtube(youtube_str),
            VideoDescriptor._parse_youtube(youtube_str_hack)
        )

    def test_parse_youtube_empty(self):
        """
        Some courses have empty youtube attributes, so we should handle
        that well.
        """
        self.assertEqual(VideoDescriptor._parse_youtube(''),
                         {'0.75': '',
                          '1.00': '',
                          '1.25': '',
                          '1.50': ''})
