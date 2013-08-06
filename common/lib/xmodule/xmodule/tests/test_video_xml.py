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

from mock import Mock

from xmodule.video_module import VideoDescriptor, VideoModule, _parse_time, _parse_youtube
from xmodule.modulestore import Location
from xmodule.tests import get_test_system
from xmodule.tests import LogicTest


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
                             "SampleProblem1"])
        model_data = {'data': VideoFactory.sample_problem_xml_youtube, 'location': location}

        descriptor = Mock(weight="1", url_name="SampleProblem1")

        system = get_test_system()
        system.render_template = lambda template, context: context
        module = VideoModule(system, descriptor, model_data)

        return module


class VideoModuleLogicTest(LogicTest):
    """Tests for logic of Video Xmodule."""

    descriptor_class = VideoDescriptor

    raw_model_data = {
        'data': '<video />'
    }

    def test_parse_time(self):
        """Ensure that times are parsed correctly into seconds."""
        output = _parse_time('00:04:07')
        self.assertEqual(output, 247)

    def test_parse_time_none(self):
        """Check parsing of None."""
        output = _parse_time(None)
        self.assertEqual(output, '')

    def test_parse_time_empty(self):
        """Check parsing of the empty string."""
        output = _parse_time('')
        self.assertEqual(output, '')

    def test_parse_youtube(self):
        """Test parsing old-style Youtube ID strings into a dict."""
        youtube_str = '0.75:jNCf2gIqpeE,1.00:ZwkTiUPN0mg,1.25:rsq9auxASqI,1.50:kMyNdzVHHgg'
        output = _parse_youtube(youtube_str)
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
        output = _parse_youtube(youtube_str)
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
        self.assertEqual(_parse_youtube(youtube_str), _parse_youtube(youtube_str_hack))

    def test_parse_youtube_empty(self):
        """
        Some courses have empty youtube attributes, so we should handle
        that well.
        """
        self.assertEqual(_parse_youtube(''),
                         {'0.75': '',
                          '1.00': '',
                          '1.25': '',
                          '1.50': ''})
