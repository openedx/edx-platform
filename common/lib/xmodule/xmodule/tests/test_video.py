# -*- coding: utf-8 -*-
# pylint: disable=W0212
"""Test for Video Xmodule functional logic.
These test data read from xml, not from mongo.

We have a ModuleStoreTestCase class defined in
common/lib/xmodule/xmodule/modulestore/tests/django_utils.py. You can
search for usages of this in the cms and lms tests for examples. You use
this so that it will do things like point the modulestore setting to mongo,
flush the contentstore before and after, load the templates, etc.
You can then use the CourseFactory and XModuleItemFactory as defined
in common/lib/xmodule/xmodule/modulestore/tests/factories.py to create
the course, section, subsection, unit, etc.
"""
import unittest
import datetime
from mock import Mock, patch

from . import LogicTest
from lxml import etree
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xmodule.video_module import (VideoDescriptor, create_youtube_string,
                                    get_video_from_cdn, get_s3_transient_url)
from .test_import import DummySystem
from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds

from xmodule.tests import get_test_descriptor_system


def instantiate_descriptor(**field_data):
    """
    Instantiate descriptor with most properties.
    """
    system = get_test_descriptor_system()
    course_key = SlashSeparatedCourseKey('org', 'course', 'run')
    usage_key = course_key.make_usage_key('video', 'SampleProblem')
    return system.construct_xblock_from_class(
        VideoDescriptor,
        scope_ids=ScopeIds(None, None, usage_key, usage_key),
        field_data=DictFieldData(field_data),
    )


class VideoModuleTest(LogicTest):
    """Logic tests for Video Xmodule."""
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

    def test_parse_youtube_invalid(self):
        """Ensure that ids that are invalid return an empty dict"""

        # invalid id
        youtube_str = 'thisisaninvalidid'
        output = VideoDescriptor._parse_youtube(youtube_str)
        self.assertEqual(output, {'0.75': '',
                                  '1.00': '',
                                  '1.25': '',
                                  '1.50': ''})
        # another invalid id
        youtube_str = ',::,:,,'
        output = VideoDescriptor._parse_youtube(youtube_str)
        self.assertEqual(output, {'0.75': '',
                                  '1.00': '',
                                  '1.25': '',
                                  '1.50': ''})

        # and another one, partially invalid
        youtube_str = '0.75_BAD!!!,1.0:AXdE34_U,1.25:KLHF9K_Y,1.5:VO3SxfeD,'
        output = VideoDescriptor._parse_youtube(youtube_str)
        self.assertEqual(output, {'0.75': '',
                                  '1.00': 'AXdE34_U',
                                  '1.25': 'KLHF9K_Y',
                                  '1.50': 'VO3SxfeD'})

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
        self.assertEqual(
            VideoDescriptor._parse_youtube(''),
            {'0.75': '',
             '1.00': '',
             '1.25': '',
             '1.50': ''}
        )


class VideoDescriptorTestBase(unittest.TestCase):
    """
    Base class for tests for VideoDescriptor
    """

    def setUp(self):
        self.descriptor = instantiate_descriptor()


class TestCreateYoutubeString(VideoDescriptorTestBase):
    """
    Checks that create_youtube_string correcty extracts information from Video descriptor.
    """
    def test_create_youtube_string(self):
        """
        Test that Youtube ID strings are correctly created when writing back out to XML.
        """
        self.descriptor.youtube_id_0_75 = 'izygArpw-Qo'
        self.descriptor.youtube_id_1_0 = 'p2Q6BrNhdh8'
        self.descriptor.youtube_id_1_25 = '1EeWXzPdhSA'
        self.descriptor.youtube_id_1_5 = 'rABDYkeK0x8'
        expected = "0.75:izygArpw-Qo,1.00:p2Q6BrNhdh8,1.25:1EeWXzPdhSA,1.50:rABDYkeK0x8"
        self.assertEqual(create_youtube_string(self.descriptor), expected)

    def test_create_youtube_string_missing(self):
        """
        Test that Youtube IDs which aren't explicitly set aren't included in the output string.
        """
        self.descriptor.youtube_id_0_75 = 'izygArpw-Qo'
        self.descriptor.youtube_id_1_0 = 'p2Q6BrNhdh8'
        self.descriptor.youtube_id_1_25 = '1EeWXzPdhSA'
        expected = "0.75:izygArpw-Qo,1.00:p2Q6BrNhdh8,1.25:1EeWXzPdhSA"
        self.assertEqual(create_youtube_string(self.descriptor), expected)


class VideoDescriptorImportTestCase(unittest.TestCase):
    """
    Make sure that VideoDescriptor can import an old XML-based video correctly.
    """
    def assert_attributes_equal(self, video, attrs):
        """
        Assert that `video` has the correct attributes. `attrs` is a map of {metadata_field: value}.
        """
        for key, value in attrs.items():
            self.assertEquals(getattr(video, key), value)

    def test_constructor(self):
        sample_xml = '''
            <video display_name="Test Video"
                   youtube="1.0:p2Q6BrNhdh8,0.75:izygArpw-Qo,1.25:1EeWXzPdhSA,1.5:rABDYkeK0x8"
                   show_captions="false"
                   download_track="true"
                   download_video="true"
                   start_time="00:00:01"
                   end_time="00:01:00">
              <source src="http://www.example.com/source.mp4"/>
              <source src="http://www.example.com/source.ogg"/>
              <track src="http://www.example.com/track"/>
              <handout src="http://www.example.com/handout"/>
              <transcript language="ua" src="ukrainian_translation.srt" />
              <transcript language="ge" src="german_translation.srt" />
            </video>
        '''
        descriptor = instantiate_descriptor(data=sample_xml)
        self.assert_attributes_equal(descriptor, {
            'youtube_id_0_75': 'izygArpw-Qo',
            'youtube_id_1_0': 'p2Q6BrNhdh8',
            'youtube_id_1_25': '1EeWXzPdhSA',
            'youtube_id_1_5': 'rABDYkeK0x8',
            'download_video': True,
            'show_captions': False,
            'start_time': datetime.timedelta(seconds=1),
            'end_time': datetime.timedelta(seconds=60),
            'track': 'http://www.example.com/track',
            'handout': 'http://www.example.com/handout',
            'download_track': True,
            'html5_sources': ['http://www.example.com/source.mp4', 'http://www.example.com/source.ogg'],
            'data': '',
            'transcripts': {'ua': 'ukrainian_translation.srt', 'ge': 'german_translation.srt'}
        })

    def test_from_xml(self):
        module_system = DummySystem(load_error_modules=True)
        xml_data = '''
            <video display_name="Test Video"
                   youtube="1.0:p2Q6BrNhdh8,0.75:izygArpw-Qo,1.25:1EeWXzPdhSA,1.5:rABDYkeK0x8"
                   show_captions="false"
                   download_track="false"
                   start_time="00:00:01"
                   download_video="false"
                   end_time="00:01:00">
              <source src="http://www.example.com/source.mp4"/>
              <track src="http://www.example.com/track"/>
              <handout src="http://www.example.com/handout"/>
              <transcript language="uk" src="ukrainian_translation.srt" />
              <transcript language="de" src="german_translation.srt" />
            </video>
        '''
        output = VideoDescriptor.from_xml(xml_data, module_system, Mock())
        self.assert_attributes_equal(output, {
            'youtube_id_0_75': 'izygArpw-Qo',
            'youtube_id_1_0': 'p2Q6BrNhdh8',
            'youtube_id_1_25': '1EeWXzPdhSA',
            'youtube_id_1_5': 'rABDYkeK0x8',
            'show_captions': False,
            'start_time': datetime.timedelta(seconds=1),
            'end_time': datetime.timedelta(seconds=60),
            'track': 'http://www.example.com/track',
            'handout': 'http://www.example.com/handout',
            'download_track': False,
            'download_video': False,
            'html5_sources': ['http://www.example.com/source.mp4'],
            'data': '',
            'transcripts': {'uk': 'ukrainian_translation.srt', 'de': 'german_translation.srt'},
        })

    def test_from_xml_missing_attributes(self):
        """
        Ensure that attributes have the right values if they aren't
        explicitly set in XML.
        """
        module_system = DummySystem(load_error_modules=True)
        xml_data = '''
            <video display_name="Test Video"
                   youtube="1.0:p2Q6BrNhdh8,1.25:1EeWXzPdhSA"
                   show_captions="true">
              <source src="http://www.example.com/source.mp4"/>
            </video>
        '''
        output = VideoDescriptor.from_xml(xml_data, module_system, Mock())
        self.assert_attributes_equal(output, {
            'youtube_id_0_75': '',
            'youtube_id_1_0': 'p2Q6BrNhdh8',
            'youtube_id_1_25': '1EeWXzPdhSA',
            'youtube_id_1_5': '',
            'show_captions': True,
            'start_time': datetime.timedelta(seconds=0.0),
            'end_time': datetime.timedelta(seconds=0.0),
            'track': '',
            'handout': None,
            'download_track': False,
            'download_video': True,
            'html5_sources': ['http://www.example.com/source.mp4'],
            'data': ''
        })

    def test_from_xml_missing_download_track(self):
        """
        Ensure that attributes have the right values if they aren't
        explicitly set in XML.
        """
        module_system = DummySystem(load_error_modules=True)
        xml_data = '''
            <video display_name="Test Video"
                   youtube="1.0:p2Q6BrNhdh8,1.25:1EeWXzPdhSA"
                   show_captions="true">
              <source src="http://www.example.com/source.mp4"/>
              <track src="http://www.example.com/track"/>
            </video>
        '''
        output = VideoDescriptor.from_xml(xml_data, module_system, Mock())
        self.assert_attributes_equal(output, {
            'youtube_id_0_75': '',
            'youtube_id_1_0': 'p2Q6BrNhdh8',
            'youtube_id_1_25': '1EeWXzPdhSA',
            'youtube_id_1_5': '',
            'show_captions': True,
            'start_time': datetime.timedelta(seconds=0.0),
            'end_time': datetime.timedelta(seconds=0.0),
            'track': 'http://www.example.com/track',
            'download_track': True,
            'download_video': True,
            'html5_sources': ['http://www.example.com/source.mp4'],
            'data': '',
            'transcripts': {},
        })

    def test_from_xml_no_attributes(self):
        """
        Make sure settings are correct if none are explicitly set in XML.
        """
        module_system = DummySystem(load_error_modules=True)
        xml_data = '<video></video>'
        output = VideoDescriptor.from_xml(xml_data, module_system, Mock())
        self.assert_attributes_equal(output, {
            'youtube_id_0_75': '',
            'youtube_id_1_0': 'OEoXaMPEzfM',
            'youtube_id_1_25': '',
            'youtube_id_1_5': '',
            'show_captions': True,
            'start_time': datetime.timedelta(seconds=0.0),
            'end_time': datetime.timedelta(seconds=0.0),
            'track': '',
            'handout': None,
            'download_track': False,
            'download_video': False,
            'html5_sources': [],
            'data': '',
            'transcripts': {},
        })

    def test_from_xml_double_quotes(self):
        """
        Make sure we can handle the double-quoted string format (which was used for exporting for
        a few weeks).
        """
        module_system = DummySystem(load_error_modules=True)
        xml_data = '''
            <video display_name="&quot;display_name&quot;"
                html5_sources="[&quot;source_1&quot;, &quot;source_2&quot;]"
                show_captions="false"
                download_video="true"
                sub="&quot;html5_subtitles&quot;"
                track="&quot;http://www.example.com/track&quot;"
                handout="&quot;http://www.example.com/handout&quot;"
                download_track="true"
                youtube_id_0_75="&quot;OEoXaMPEzf65&quot;"
                youtube_id_1_25="&quot;OEoXaMPEzf125&quot;"
                youtube_id_1_5="&quot;OEoXaMPEzf15&quot;"
                youtube_id_1_0="&quot;OEoXaMPEzf10&quot;"
                />
        '''
        output = VideoDescriptor.from_xml(xml_data, module_system, Mock())
        self.assert_attributes_equal(output, {
            'youtube_id_0_75': 'OEoXaMPEzf65',
            'youtube_id_1_0': 'OEoXaMPEzf10',
            'youtube_id_1_25': 'OEoXaMPEzf125',
            'youtube_id_1_5': 'OEoXaMPEzf15',
            'show_captions': False,
            'start_time': datetime.timedelta(seconds=0.0),
            'end_time': datetime.timedelta(seconds=0.0),
            'track': 'http://www.example.com/track',
            'handout': 'http://www.example.com/handout',
            'download_track': True,
            'download_video': True,
            'html5_sources': ["source_1", "source_2"],
            'data': ''
        })

    def test_from_xml_double_quote_concatenated_youtube(self):
        module_system = DummySystem(load_error_modules=True)
        xml_data = '''
            <video display_name="Test Video"
                   youtube="1.0:&quot;p2Q6BrNhdh8&quot;,1.25:&quot;1EeWXzPdhSA&quot;">
            </video>
        '''
        output = VideoDescriptor.from_xml(xml_data, module_system, Mock())
        self.assert_attributes_equal(output, {
            'youtube_id_0_75': '',
            'youtube_id_1_0': 'p2Q6BrNhdh8',
            'youtube_id_1_25': '1EeWXzPdhSA',
            'youtube_id_1_5': '',
            'show_captions': True,
            'start_time': datetime.timedelta(seconds=0.0),
            'end_time': datetime.timedelta(seconds=0.0),
            'track': '',
            'handout': None,
            'download_track': False,
            'download_video': False,
            'html5_sources': [],
            'data': ''
        })

    def test_old_video_format(self):
        """
        Test backwards compatibility with VideoModule's XML format.
        """
        module_system = DummySystem(load_error_modules=True)
        xml_data = """
            <video display_name="Test Video"
                   youtube="1.0:p2Q6BrNhdh8,0.75:izygArpw-Qo,1.25:1EeWXzPdhSA,1.5:rABDYkeK0x8"
                   show_captions="false"
                   source="http://www.example.com/source.mp4"
                   from="00:00:01"
                   to="00:01:00">
              <source src="http://www.example.com/source.mp4"/>
              <track src="http://www.example.com/track"/>
            </video>
        """
        output = VideoDescriptor.from_xml(xml_data, module_system, Mock())
        self.assert_attributes_equal(output, {
            'youtube_id_0_75': 'izygArpw-Qo',
            'youtube_id_1_0': 'p2Q6BrNhdh8',
            'youtube_id_1_25': '1EeWXzPdhSA',
            'youtube_id_1_5': 'rABDYkeK0x8',
            'show_captions': False,
            'start_time': datetime.timedelta(seconds=1),
            'end_time': datetime.timedelta(seconds=60),
            'track': 'http://www.example.com/track',
            # 'download_track': True,
            'html5_sources': ['http://www.example.com/source.mp4'],
            'data': '',
        })

    def test_old_video_data(self):
        """
        Ensure that Video is able to read VideoModule's model data.
        """
        module_system = DummySystem(load_error_modules=True)
        xml_data = """
            <video display_name="Test Video"
                   youtube="1.0:p2Q6BrNhdh8,0.75:izygArpw-Qo,1.25:1EeWXzPdhSA,1.5:rABDYkeK0x8"
                   show_captions="false"
                   from="00:00:01"
                   to="00:01:00">
              <source src="http://www.example.com/source.mp4"/>
              <track src="http://www.example.com/track"/>
            </video>
        """
        video = VideoDescriptor.from_xml(xml_data, module_system, Mock())
        self.assert_attributes_equal(video, {
            'youtube_id_0_75': 'izygArpw-Qo',
            'youtube_id_1_0': 'p2Q6BrNhdh8',
            'youtube_id_1_25': '1EeWXzPdhSA',
            'youtube_id_1_5': 'rABDYkeK0x8',
            'show_captions': False,
            'start_time': datetime.timedelta(seconds=1),
            'end_time': datetime.timedelta(seconds=60),
            'track': 'http://www.example.com/track',
            # 'download_track': True,
            'html5_sources': ['http://www.example.com/source.mp4'],
            'data': ''
        })

    def test_import_with_float_times(self):
        """
        Ensure that Video is able to read VideoModule's model data.
        """
        module_system = DummySystem(load_error_modules=True)
        xml_data = """
            <video display_name="Test Video"
                   youtube="1.0:p2Q6BrNhdh8,0.75:izygArpw-Qo,1.25:1EeWXzPdhSA,1.5:rABDYkeK0x8"
                   show_captions="false"
                   from="1.0"
                   to="60.0">
              <source src="http://www.example.com/source.mp4"/>
              <track src="http://www.example.com/track"/>
            </video>
        """
        video = VideoDescriptor.from_xml(xml_data, module_system, Mock())
        self.assert_attributes_equal(video, {
            'youtube_id_0_75': 'izygArpw-Qo',
            'youtube_id_1_0': 'p2Q6BrNhdh8',
            'youtube_id_1_25': '1EeWXzPdhSA',
            'youtube_id_1_5': 'rABDYkeK0x8',
            'show_captions': False,
            'start_time': datetime.timedelta(seconds=1),
            'end_time': datetime.timedelta(seconds=60),
            'track': 'http://www.example.com/track',
            # 'download_track': True,
            'html5_sources': ['http://www.example.com/source.mp4'],
            'data': ''
        })


class VideoExportTestCase(VideoDescriptorTestBase):
    """
    Make sure that VideoDescriptor can export itself to XML correctly.
    """
    def assertXmlEqual(self, expected, xml):
        for attr in ['tag', 'attrib', 'text', 'tail']:
            self.assertEqual(getattr(expected, attr), getattr(xml, attr))
        for left, right in zip(expected, xml):
            self.assertXmlEqual(left, right)

    def test_export_to_xml(self):
        """
        Test that we write the correct XML on export.
        """
        self.descriptor.youtube_id_0_75 = 'izygArpw-Qo'
        self.descriptor.youtube_id_1_0 = 'p2Q6BrNhdh8'
        self.descriptor.youtube_id_1_25 = '1EeWXzPdhSA'
        self.descriptor.youtube_id_1_5 = 'rABDYkeK0x8'
        self.descriptor.show_captions = False
        self.descriptor.start_time = datetime.timedelta(seconds=1.0)
        self.descriptor.end_time = datetime.timedelta(seconds=60)
        self.descriptor.track = 'http://www.example.com/track'
        self.descriptor.handout = 'http://www.example.com/handout'
        self.descriptor.download_track = True
        self.descriptor.html5_sources = ['http://www.example.com/source.mp4', 'http://www.example.com/source.ogg']
        self.descriptor.download_video = True
        self.descriptor.transcripts = {'ua': 'ukrainian_translation.srt', 'ge': 'german_translation.srt'}

        xml = self.descriptor.definition_to_xml(None)  # We don't use the `resource_fs` parameter
        expected = etree.fromstring('''\
         <video url_name="SampleProblem" start_time="0:00:01" youtube="0.75:izygArpw-Qo,1.00:p2Q6BrNhdh8,1.25:1EeWXzPdhSA,1.50:rABDYkeK0x8" show_captions="false" end_time="0:01:00" download_video="true" download_track="true">
           <source src="http://www.example.com/source.mp4"/>
           <source src="http://www.example.com/source.ogg"/>
           <track src="http://www.example.com/track"/>
           <handout src="http://www.example.com/handout"/>
           <transcript language="ge" src="german_translation.srt" />
           <transcript language="ua" src="ukrainian_translation.srt" />
         </video>
        ''')
        self.assertXmlEqual(expected, xml)

    def test_export_to_xml_empty_end_time(self):
        """
        Test that we write the correct XML on export.
        """
        self.descriptor.youtube_id_0_75 = 'izygArpw-Qo'
        self.descriptor.youtube_id_1_0 = 'p2Q6BrNhdh8'
        self.descriptor.youtube_id_1_25 = '1EeWXzPdhSA'
        self.descriptor.youtube_id_1_5 = 'rABDYkeK0x8'
        self.descriptor.show_captions = False
        self.descriptor.start_time = datetime.timedelta(seconds=5.0)
        self.descriptor.end_time = datetime.timedelta(seconds=0.0)
        self.descriptor.track = 'http://www.example.com/track'
        self.descriptor.download_track = True
        self.descriptor.html5_sources = ['http://www.example.com/source.mp4', 'http://www.example.com/source.ogg']
        self.descriptor.download_video = True

        xml = self.descriptor.definition_to_xml(None)  # We don't use the `resource_fs` parameter
        expected = etree.fromstring('''\
         <video url_name="SampleProblem" start_time="0:00:05" youtube="0.75:izygArpw-Qo,1.00:p2Q6BrNhdh8,1.25:1EeWXzPdhSA,1.50:rABDYkeK0x8" show_captions="false" download_video="true" download_track="true">
           <source src="http://www.example.com/source.mp4"/>
           <source src="http://www.example.com/source.ogg"/>
           <track src="http://www.example.com/track"/>
         </video>
        ''')

        self.assertXmlEqual(expected, xml)

    def test_export_to_xml_empty_parameters(self):
        """
        Test XML export with defaults.
        """
        xml = self.descriptor.definition_to_xml(None)
        expected = '<video url_name="SampleProblem"/>\n'
        self.assertEquals(expected, etree.tostring(xml, pretty_print=True))


class VideoCdnTest(unittest.TestCase):
    """
    Tests for Video CDN.
    """
    @patch('requests.get')
    def test_get_video_success(self, cdn_response):
        """
        Test successful CDN request.
        """
        original_video_url = "http://www.original_video.com/original_video.mp4"
        cdn_response_video_url = "http://www.cdn_video.com/cdn_video.mp4"
        cdn_response_content = '{{"sources":["{cdn_url}"]}}'.format(cdn_url=cdn_response_video_url)
        cdn_response.return_value=Mock(status_code=200, content=cdn_response_content)
        fake_cdn_url = 'http://fake_cdn.com/'
        self.assertEqual(
            get_video_from_cdn(fake_cdn_url, original_video_url),
            cdn_response_video_url
        )

    @patch('requests.get')
    def test_get_no_video_exists(self, cdn_response):
        """
        Test if no alternative video in CDN exists.
        """
        original_video_url = "http://www.original_video.com/original_video.mp4"
        cdn_response.return_value=Mock(status_code=404)
        fake_cdn_url = 'http://fake_cdn.com/'
        self.assertIsNone(get_video_from_cdn(fake_cdn_url, original_video_url))

class VideoLinkTransienceTest(unittest.TestCase):
    """
    Tests for temporary video links.
    """

    def test_url_create(self):
        """
        Test if bucket name and object name is present in transient URL..
        """
        aws_access_key = "test_key"
        aws_secret_key = "test_secret"
        expires_in = 10
        origin_video_urls = [
            "http://s3.amazonaws.com/bucket/video.mp4",
            "http://bucket.s3.amazonaws.com/video.mp4",
        ]
        for origin_url in origin_video_urls:
            url = get_s3_transient_url(origin_url, aws_access_key, aws_secret_key, expires_in)
            self.assertIn('https://bucket.s3.amazonaws.com/video.mp4', url)

        origin_video_urls = [
            "http://s3.amazonaws.com/bucket/subfolder/video.mp4",
            "http://bucket.s3.amazonaws.com/subfolder/video.mp4",
        ]
        for origin_url in origin_video_urls:
            url = get_s3_transient_url(origin_url, aws_access_key, aws_secret_key, expires_in)
            self.assertIn('https://bucket.s3.amazonaws.com/subfolder/video.mp4', url)
