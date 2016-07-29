# -*- coding: utf-8 -*-
# pylint: disable=protected-access
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
from uuid import uuid4

from lxml import etree
from mock import ANY, Mock, patch
import ddt

from django.conf import settings

from opaque_keys.edx.locations import SlashSeparatedCourseKey
from opaque_keys.edx.keys import CourseKey
from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds

from xmodule.tests import get_test_descriptor_system
from xmodule.video_module import VideoDescriptor, create_youtube_string
from xmodule.video_module.transcripts_utils import download_youtube_subs, save_to_store
from . import LogicTest
from .test_import import DummySystem

SRT_FILEDATA = '''
0
00:00:00,270 --> 00:00:02,720
sprechen sie deutsch?

1
00:00:02,720 --> 00:00:05,430
Ja, ich spreche Deutsch
'''

CRO_SRT_FILEDATA = '''
0
00:00:00,270 --> 00:00:02,720
Dobar dan!

1
00:00:02,720 --> 00:00:05,430
Kako ste danas?
'''

YOUTUBE_SUBTITLES = (
    "LILA FISHER: Hi, welcome to Edx. I'm Lila Fisher, an Edx fellow helping to put together these"
    " courses. As you know, our courses are entirely online. So before we start learning about the"
    " subjects that brought you here, let's learn about the tools that you will use to navigate through"
    " the course material. Let's start with what is on your screen right now. You are watching a video"
    " of me talking. You have several tools associated with these videos. Some of them are standard"
    " video buttons, like the play Pause Button on the bottom left. Like most video players, you can see"
    " how far you are into this particular video segment and how long the entire video segment is."
    " Something that you might not be used to is the speed option. While you are going through the"
    " videos, you can speed up or slow down the video player with these buttons. Go ahead and try that"
    " now. Make me talk faster and slower. If you ever get frustrated by the pace of speech, you can"
    " adjust it this way. Another great feature is the transcript on the side. This will follow along"
    " with everything that I am saying as I am saying it, so you can read along if you like. You can"
    " also click on any of the words, and you will notice that the video jumps to that word. The video"
    " slider at the bottom of the video will let you navigate through the video quickly. If you ever"
    " find the transcript distracting, you can toggle the captioning button in order to make it go away"
    " or reappear. Now that you know about the video player, I want to point out the sequence navigator."
    " Right now you're in a lecture sequence, which interweaves many videos and practice exercises. You"
    " can see how far you are in a particular sequence by observing which tab you're on. You can"
    " navigate directly to any video or exercise by clicking on the appropriate tab. You can also"
    " progress to the next element by pressing the Arrow button, or by clicking on the next tab. Try"
    " that now. The tutorial will continue in the next video."
)


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


# Because of the way xmodule.video_module.video_module imports edxval.api, we
# must mock the entire module, which requires making mock exception classes.

class _MockValVideoNotFoundError(Exception):
    """Mock ValVideoNotFoundError exception"""
    pass


class _MockValCannotCreateError(Exception):
    """Mock ValCannotCreateError exception"""
    pass


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
        super(VideoDescriptorTestBase, self).setUp()
        self.descriptor = instantiate_descriptor()

    def assertXmlEqual(self, expected, xml):
        """
        Assert that the given XML fragments have the same attributes, text, and
        (recursively) children
        """
        def get_child_tags(elem):
            """Extract the list of tag names for children of elem"""
            return [child.tag for child in elem]

        for attr in ['tag', 'attrib', 'text', 'tail']:
            self.assertEqual(getattr(expected, attr), getattr(xml, attr))
        self.assertEqual(get_child_tags(expected), get_child_tags(xml))
        for left, right in zip(expected, xml):
            self.assertXmlEqual(left, right)


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

class TestCreateYouTubeUrl(VideoDescriptorTestBase):
    """
    Tests for helper method `create_youtube_url`.
    """
    def test_create_youtube_url_unicode(self):
        """
        Test that passing unicode to `create_youtube_url` doesn't throw
        an error.
        """
        self.descriptor.create_youtube_url(u"üñîçø∂é")


@ddt.ddt
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

    @ddt.data(
        ('course-v1:test_org+test_course+test_run',
         '/asset-v1:test_org+test_course+test_run+type@asset+block@test.png'),
        ('test_org/test_course/test_run', '/c4x/test_org/test_course/asset/test.png')
    )
    @ddt.unpack
    def test_from_xml_when_handout_is_course_asset(self, course_id_string, expected_handout_link):
        """
        Test that if handout link is course_asset then it will contain targeted course_id in handout link.
        """
        module_system = DummySystem(load_error_modules=True)
        course_id = CourseKey.from_string(course_id_string)
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
              <handout src="/asset-v1:test_org_1+test_course_1+test_run_1+type@asset+block@test.png"/>
              <transcript language="uk" src="ukrainian_translation.srt" />
              <transcript language="de" src="german_translation.srt" />
            </video>
        '''
        id_generator = Mock()
        id_generator.target_course_id = course_id

        output = VideoDescriptor.from_xml(xml_data, module_system, id_generator)
        self.assert_attributes_equal(output, {
            'youtube_id_0_75': 'izygArpw-Qo',
            'youtube_id_1_0': 'p2Q6BrNhdh8',
            'youtube_id_1_25': '1EeWXzPdhSA',
            'youtube_id_1_5': 'rABDYkeK0x8',
            'show_captions': False,
            'start_time': datetime.timedelta(seconds=1),
            'end_time': datetime.timedelta(seconds=60),
            'track': 'http://www.example.com/track',
            'handout': expected_handout_link,
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
            'youtube_id_1_0': '3_yD_cEKoCk',
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

    @patch('xmodule.video_module.video_module.edxval_api')
    def test_import_val_data(self, mock_val_api):
        def mock_val_import(xml, edx_video_id, course_id):
            """Mock edxval.api.import_from_xml"""
            self.assertEqual(xml.tag, 'video_asset')
            self.assertEqual(dict(xml.items()), {'mock_attr': ''})
            self.assertEqual(edx_video_id, 'test_edx_video_id')
            self.assertEqual(course_id, 'test_course_id')

        mock_val_api.import_from_xml = Mock(wraps=mock_val_import)
        module_system = DummySystem(load_error_modules=True)

        # import new edx_video_id
        xml_data = """
            <video edx_video_id="test_edx_video_id">
                <video_asset mock_attr=""/>
            </video>
        """
        id_generator = Mock()
        id_generator.target_course_id = 'test_course_id'
        video = VideoDescriptor.from_xml(xml_data, module_system, id_generator)

        self.assert_attributes_equal(video, {'edx_video_id': 'test_edx_video_id'})
        mock_val_api.import_from_xml.assert_called_once_with(ANY, 'test_edx_video_id', course_id='test_course_id')

    @patch('xmodule.video_module.video_module.edxval_api')
    def test_import_val_data_invalid(self, mock_val_api):
        mock_val_api.ValCannotCreateError = _MockValCannotCreateError
        mock_val_api.import_from_xml = Mock(side_effect=mock_val_api.ValCannotCreateError)
        module_system = DummySystem(load_error_modules=True)

        # Negative duration is invalid
        xml_data = """
            <video edx_video_id="test_edx_video_id">
                <video_asset client_video_id="test_client_video_id" duration="-1"/>
            </video>
        """
        with self.assertRaises(mock_val_api.ValCannotCreateError):
            VideoDescriptor.from_xml(xml_data, module_system, id_generator=Mock())


class VideoExportTestCase(VideoDescriptorTestBase):
    """
    Make sure that VideoDescriptor can export itself to XML correctly.
    """
    @patch('xmodule.video_module.video_module.edxval_api')
    def test_export_to_xml(self, mock_val_api):
        """
        Test that we write the correct XML on export.
        """
        def mock_val_export(edx_video_id):
            """Mock edxval.api.export_to_xml"""
            return etree.Element(
                'video_asset',
                attrib={'export_edx_video_id': edx_video_id}
            )

        mock_val_api.export_to_xml = mock_val_export
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
        self.descriptor.edx_video_id = 'test_edx_video_id'

        xml = self.descriptor.definition_to_xml(None)  # We don't use the `resource_fs` parameter
        parser = etree.XMLParser(remove_blank_text=True)
        xml_string = '''\
         <video url_name="SampleProblem" start_time="0:00:01" youtube="0.75:izygArpw-Qo,1.00:p2Q6BrNhdh8,1.25:1EeWXzPdhSA,1.50:rABDYkeK0x8" show_captions="false" end_time="0:01:00" download_video="true" download_track="true">
           <source src="http://www.example.com/source.mp4"/>
           <source src="http://www.example.com/source.ogg"/>
           <track src="http://www.example.com/track"/>
           <handout src="http://www.example.com/handout"/>
           <transcript language="ge" src="german_translation.srt" />
           <transcript language="ua" src="ukrainian_translation.srt" />
           <video_asset export_edx_video_id="test_edx_video_id"/>
         </video>
        '''
        expected = etree.XML(xml_string, parser=parser)
        self.assertXmlEqual(expected, xml)

    @patch('xmodule.video_module.video_module.edxval_api')
    def test_export_to_xml_val_error(self, mock_val_api):
        # Export should succeed without VAL data if video does not exist
        mock_val_api.ValVideoNotFoundError = _MockValVideoNotFoundError
        mock_val_api.export_to_xml = Mock(side_effect=mock_val_api.ValVideoNotFoundError)
        self.descriptor.edx_video_id = 'test_edx_video_id'

        xml = self.descriptor.definition_to_xml(None)
        parser = etree.XMLParser(remove_blank_text=True)
        xml_string = '<video url_name="SampleProblem" download_video="false"/>'
        expected = etree.XML(xml_string, parser=parser)
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
        parser = etree.XMLParser(remove_blank_text=True)
        xml_string = '''\
         <video url_name="SampleProblem" start_time="0:00:05" youtube="0.75:izygArpw-Qo,1.00:p2Q6BrNhdh8,1.25:1EeWXzPdhSA,1.50:rABDYkeK0x8" show_captions="false" download_video="true" download_track="true">
           <source src="http://www.example.com/source.mp4"/>
           <source src="http://www.example.com/source.ogg"/>
           <track src="http://www.example.com/track"/>
         </video>
        '''
        expected = etree.XML(xml_string, parser=parser)
        self.assertXmlEqual(expected, xml)

    def test_export_to_xml_empty_parameters(self):
        """
        Test XML export with defaults.
        """
        xml = self.descriptor.definition_to_xml(None)
        # Check that download_video field is also set to default (False) in xml for backward compatibility
        expected = '<video url_name="SampleProblem" download_video="false"/>\n'
        self.assertEquals(expected, etree.tostring(xml, pretty_print=True))

    def test_export_to_xml_with_transcripts_as_none(self):
        """
        Test XML export with transcripts being overridden to None.
        """
        self.descriptor.transcripts = None
        xml = self.descriptor.definition_to_xml(None)
        expected = '<video url_name="SampleProblem" download_video="false"/>\n'
        self.assertEquals(expected, etree.tostring(xml, pretty_print=True))

    def test_export_to_xml_invalid_characters_in_attributes(self):
        """
        Test XML export will *not* raise TypeError by lxml library if contains illegal characters.
        The illegal characters in a String field are removed from the string instead.
        """
        self.descriptor.display_name = 'Display\x1eName'
        xml = self.descriptor.definition_to_xml(None)
        self.assertEqual(xml.get('display_name'), 'DisplayName')

    def test_export_to_xml_unicode_characters(self):
        """
        Test XML export handles the unicode characters.
        """
        self.descriptor.display_name = '这是文'
        xml = self.descriptor.definition_to_xml(None)
        self.assertEqual(xml.get('display_name'), u'\u8fd9\u662f\u6587')


class VideoDescriptorIndexingTestCase(unittest.TestCase):
    """
    Make sure that VideoDescriptor can format data for indexing as expected.
    """
    def setUp(self):
        """
        Overrides YOUTUBE and CONTENTSTORE settings
        """
        super(VideoDescriptorIndexingTestCase, self).setUp()
        self.youtube_setting = getattr(settings, "YOUTUBE", None)
        self.contentstore_setting = getattr(settings, "CONTENTSTORE", None)
        settings.YOUTUBE = {
            # YouTube JavaScript API
            'API': 'www.youtube.com/iframe_api',

            # URL to get YouTube metadata
            'METADATA_URL': 'www.googleapis.com/youtube/v3/videos/',

            # Current youtube api for requesting transcripts.
            # For example: http://video.google.com/timedtext?lang=en&v=j_jEn79vS3g.
            'TEXT_API': {
                'url': 'video.google.com/timedtext',
                'params': {
                    'lang': 'en',
                    'v': 'set_youtube_id_of_11_symbols_here',
                },
            },
        }

        settings.CONTENTSTORE = {
            'ENGINE': 'xmodule.contentstore.mongo.MongoContentStore',
            'DOC_STORE_CONFIG': {
                'host': 'localhost',
                'db': 'test_xcontent_%s' % uuid4().hex,
            },
            # allow for additional options that can be keyed on a name, e.g. 'trashcan'
            'ADDITIONAL_OPTIONS': {
                'trashcan': {
                    'bucket': 'trash_fs'
                }
            }
        }

        self.addCleanup(self.cleanup)

    def cleanup(self):
        """
        Returns YOUTUBE and CONTENTSTORE settings to a default value
        """
        if self.youtube_setting:
            settings.YOUTUBE = self.youtube_setting
            self.youtube_setting = None
        else:
            del settings.YOUTUBE

        if self.contentstore_setting:
            settings.CONTENTSTORE = self.contentstore_setting
            self.contentstore_setting = None
        else:
            del settings.CONTENTSTORE

    def test_video_with_no_subs_index_dictionary(self):
        """
        Test index dictionary of a video module without subtitles.
        """
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
            </video>
        '''
        descriptor = instantiate_descriptor(data=xml_data)
        self.assertEqual(descriptor.index_dictionary(), {
            "content": {"display_name": "Test Video"},
            "content_type": "Video"
        })

    def test_video_with_youtube_subs_index_dictionary(self):
        """
        Test index dictionary of a video module with YouTube subtitles.
        """
        xml_data_sub = '''
            <video display_name="Test Video"
                   youtube="1.0:p2Q6BrNhdh8,0.75:izygArpw-Qo,1.25:1EeWXzPdhSA,1.5:rABDYkeK0x8"
                   show_captions="false"
                   download_track="false"
                   sub="OEoXaMPEzfM"
                   start_time="00:00:01"
                   download_video="false"
                   end_time="00:01:00">
              <source src="http://www.example.com/source.mp4"/>
              <track src="http://www.example.com/track"/>
              <handout src="http://www.example.com/handout"/>
            </video>
        '''

        descriptor = instantiate_descriptor(data=xml_data_sub)
        download_youtube_subs('OEoXaMPEzfM', descriptor, settings)
        self.assertEqual(descriptor.index_dictionary(), {
            "content": {
                "display_name": "Test Video",
                "transcript_en": YOUTUBE_SUBTITLES
            },
            "content_type": "Video"
        })

    def test_video_with_subs_and_transcript_index_dictionary(self):
        """
        Test index dictionary of a video module with
        YouTube subtitles and German transcript uploaded by a user.
        """
        xml_data_sub_transcript = '''
            <video display_name="Test Video"
                   youtube="1.0:p2Q6BrNhdh8,0.75:izygArpw-Qo,1.25:1EeWXzPdhSA,1.5:rABDYkeK0x8"
                   show_captions="false"
                   download_track="false"
                   sub="OEoXaMPEzfM"
                   start_time="00:00:01"
                   download_video="false"
                   end_time="00:01:00">
              <source src="http://www.example.com/source.mp4"/>
              <track src="http://www.example.com/track"/>
              <handout src="http://www.example.com/handout"/>
              <transcript language="ge" src="subs_grmtran1.srt" />
            </video>
        '''

        descriptor = instantiate_descriptor(data=xml_data_sub_transcript)
        download_youtube_subs('OEoXaMPEzfM', descriptor, settings)
        save_to_store(SRT_FILEDATA, "subs_grmtran1.srt", 'text/srt', descriptor.location)
        self.assertEqual(descriptor.index_dictionary(), {
            "content": {
                "display_name": "Test Video",
                "transcript_en": YOUTUBE_SUBTITLES,
                "transcript_ge": "sprechen sie deutsch? Ja, ich spreche Deutsch",
            },
            "content_type": "Video"
        })

    def test_video_with_multiple_transcripts_index_dictionary(self):
        """
        Test index dictionary of a video module with
        two transcripts uploaded by a user.
        """
        xml_data_transcripts = '''
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
              <transcript language="ge" src="subs_grmtran1.srt" />
              <transcript language="hr" src="subs_croatian1.srt" />
            </video>
        '''

        descriptor = instantiate_descriptor(data=xml_data_transcripts)
        save_to_store(SRT_FILEDATA, "subs_grmtran1.srt", 'text/srt', descriptor.location)
        save_to_store(CRO_SRT_FILEDATA, "subs_croatian1.srt", 'text/srt', descriptor.location)
        self.assertEqual(descriptor.index_dictionary(), {
            "content": {
                "display_name": "Test Video",
                "transcript_ge": "sprechen sie deutsch? Ja, ich spreche Deutsch",
                "transcript_hr": "Dobar dan! Kako ste danas?"
            },
            "content_type": "Video"
        })

    def test_video_with_multiple_transcripts_translation_retrieval(self):
        """
        Test translation retrieval of a video module with
        multiple transcripts uploaded by a user.
        """
        xml_data_transcripts = '''
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
              <transcript language="ge" src="subs_grmtran1.srt" />
              <transcript language="hr" src="subs_croatian1.srt" />
            </video>
        '''

        descriptor = instantiate_descriptor(data=xml_data_transcripts)
        translations = descriptor.available_translations(descriptor.get_transcripts_info(), verify_assets=False)
        self.assertEqual(translations, ['hr', 'ge'])

    def test_video_with_no_transcripts_translation_retrieval(self):
        """
        Test translation retrieval of a video module with
        no transcripts uploaded by a user- ie, that retrieval
        does not throw an exception.
        """
        descriptor = instantiate_descriptor(data=None)
        translations = descriptor.available_translations(descriptor.get_transcripts_info(), verify_assets=False)
        self.assertEqual(translations, ['en'])
