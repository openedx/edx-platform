# -*- coding: utf-8 -*-
""" Tests for transcripts_utils. """


import copy
import json
import tempfile
import textwrap
import unittest
from uuid import uuid4

import ddt
import pytest
from django.conf import settings
from django.test.utils import override_settings
from django.utils import translation
from mock import Mock, patch
from six import text_type

from cms.djangoapps.contentstore.tests.utils import mock_requests_get
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.contentstore.content import StaticContent
from xmodule.contentstore.django import contentstore
from xmodule.exceptions import NotFoundError
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.video_module import transcripts_utils

TEST_DATA_CONTENTSTORE = copy.deepcopy(settings.CONTENTSTORE)
TEST_DATA_CONTENTSTORE['DOC_STORE_CONFIG']['db'] = 'test_xcontent_%s' % uuid4().hex


class TestGenerateSubs(unittest.TestCase):
    """Tests for `generate_subs` function."""
    def setUp(self):
        super(TestGenerateSubs, self).setUp()

        self.source_subs = {
            'start': [100, 200, 240, 390, 1000],
            'end': [200, 240, 380, 1000, 1500],
            'text': [
                'subs #1',
                'subs #2',
                'subs #3',
                'subs #4',
                'subs #5'
            ]
        }

    def test_generate_subs_increase_speed(self):
        subs = transcripts_utils.generate_subs(2, 1, self.source_subs)
        self.assertDictEqual(
            subs,
            {
                'start': [200, 400, 480, 780, 2000],
                'end': [400, 480, 760, 2000, 3000],
                'text': ['subs #1', 'subs #2', 'subs #3', 'subs #4', 'subs #5']
            }
        )

    def test_generate_subs_decrease_speed_1(self):
        subs = transcripts_utils.generate_subs(0.5, 1, self.source_subs)
        self.assertDictEqual(
            subs,
            {
                'start': [50, 100, 120, 195, 500],
                'end': [100, 120, 190, 500, 750],
                'text': ['subs #1', 'subs #2', 'subs #3', 'subs #4', 'subs #5']
            }
        )

    def test_generate_subs_decrease_speed_2(self):
        """Test for correct devision during `generate_subs` process."""
        subs = transcripts_utils.generate_subs(1, 2, self.source_subs)
        self.assertDictEqual(
            subs,
            {
                'start': [50, 100, 120, 195, 500],
                'end': [100, 120, 190, 500, 750],
                'text': ['subs #1', 'subs #2', 'subs #3', 'subs #4', 'subs #5']
            }
        )


@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE)
class TestSaveSubsToStore(SharedModuleStoreTestCase):
    """Tests for `save_subs_to_store` function."""

    org = 'MITx'
    number = '999'
    display_name = 'Test course'

    def clear_subs_content(self):
        """Remove, if subtitles content exists."""
        for content_location in [self.content_location, self.content_copied_location]:
            try:
                content = contentstore().find(content_location)
                contentstore().delete(content.location)
            except NotFoundError:
                pass

    @classmethod
    def sub_id_to_location(cls, sub_id):
        """
        A helper to compute a static file location from a subtitle id.
        """
        return StaticContent.compute_location(cls.course.id, u'subs_{0}.srt.sjson'.format(sub_id))

    @classmethod
    def setUpClass(cls):
        super(TestSaveSubsToStore, cls).setUpClass()
        cls.course = CourseFactory.create(
            org=cls.org, number=cls.number, display_name=cls.display_name)

        cls.subs = {
            'start': [100, 200, 240, 390, 1000],
            'end': [200, 240, 380, 1000, 1500],
            'text': [
                'subs #1',
                'subs #2',
                'subs #3',
                'subs #4',
                'subs #5'
            ]
        }

        # Prefix it to ensure that unicode filenames are allowed
        cls.subs_id = u'uniçøde_{}'.format(uuid4())
        cls.subs_copied_id = u'cøpy_{}'.format(uuid4())

        cls.content_location = cls.sub_id_to_location(cls.subs_id)
        cls.content_copied_location = cls.sub_id_to_location(cls.subs_copied_id)

        # incorrect subs
        cls.unjsonable_subs = {1}  # set can't be serialized

        cls.unjsonable_subs_id = str(uuid4())
        cls.content_location_unjsonable = cls.sub_id_to_location(cls.unjsonable_subs_id)

    def setUp(self):
        super(TestSaveSubsToStore, self).setUp()
        self.addCleanup(self.clear_subs_content)
        self.clear_subs_content()

    def test_save_unicode_filename(self):
        # Mock a video item
        item = Mock(location=Mock(course_key=self.course.id))
        transcripts_utils.save_subs_to_store(self.subs, self.subs_id, self.course)
        transcripts_utils.copy_or_rename_transcript(self.subs_copied_id, self.subs_id, item)
        self.assertTrue(contentstore().find(self.content_copied_location))

    def test_save_subs_to_store(self):
        with self.assertRaises(NotFoundError):
            contentstore().find(self.content_location)

        result_location = transcripts_utils.save_subs_to_store(
            self.subs,
            self.subs_id,
            self.course)

        self.assertTrue(contentstore().find(self.content_location))
        self.assertEqual(result_location, self.content_location)

    def test_save_unjsonable_subs_to_store(self):
        """
        Ensures that subs, that can't be dumped, can't be found later.
        """
        with self.assertRaises(NotFoundError):
            contentstore().find(self.content_location_unjsonable)

        with self.assertRaises(TypeError):
            transcripts_utils.save_subs_to_store(
                self.unjsonable_subs,
                self.unjsonable_subs_id,
                self.course)

        with self.assertRaises(NotFoundError):
            contentstore().find(self.content_location_unjsonable)


class TestYoutubeSubsBase(SharedModuleStoreTestCase):
    """
    Base class for tests of Youtube subs.  Using override_settings and
    a setUpClass() override in a test class which is inherited by another
    test class doesn't work well with pytest-django.
    """
    @classmethod
    def setUpClass(cls):
        super(TestYoutubeSubsBase, cls).setUpClass()
        cls.course = CourseFactory.create(
            org=cls.org, number=cls.number, display_name=cls.display_name)


@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE)
class TestDownloadYoutubeSubs(TestYoutubeSubsBase):
    """
    Tests for `download_youtube_subs` function.
    """

    org = 'MITx'
    number = '999'
    display_name = 'Test course'

    def clear_sub_content(self, subs_id):
        """
        Remove, if subtitle content exists.
        """
        filename = 'subs_{0}.srt.sjson'.format(subs_id)
        content_location = StaticContent.compute_location(self.course.id, filename)
        try:
            content = contentstore().find(content_location)
            contentstore().delete(content.location)
        except NotFoundError:
            pass

    def clear_subs_content(self, youtube_subs):
        """
        Remove, if subtitles content exists.

        youtube_subs: dict of '{speed: youtube_id}' format for different speeds.
        """
        for subs_id in youtube_subs.values():
            self.clear_sub_content(subs_id)

    def test_success_downloading_subs(self):

        response = textwrap.dedent("""<?xml version="1.0" encoding="utf-8" ?>
                <transcript>
                    <text start="0" dur="0.27"></text>
                    <text start="0.27" dur="2.45">Test text 1.</text>
                    <text start="2.72">Test text 2.</text>
                    <text start="5.43" dur="1.73">Test text 3.</text>
                </transcript>
        """)
        good_youtube_sub = 'good_id_2'
        self.clear_sub_content(good_youtube_sub)

        with patch('xmodule.video_module.transcripts_utils.requests.get') as mock_get:
            mock_get.return_value = Mock(status_code=200, text=response, content=response.encode('utf-8'))
            # Check transcripts_utils.GetTranscriptsFromYouTubeException not thrown
            transcripts_utils.download_youtube_subs(good_youtube_sub, self.course, settings)

        mock_get.assert_any_call('http://video.google.com/timedtext', params={'lang': 'en', 'v': 'good_id_2'})

    def test_subs_for_html5_vid_with_periods(self):
        """
        This is to verify a fix whereby subtitle files uploaded against
        a HTML5 video that contains periods in the name causes
        incorrect subs name parsing
        """
        html5_ids = transcripts_utils.get_html5_ids(['foo.mp4', 'foo.1.bar.mp4', 'foo/bar/baz.1.4.mp4', 'foo'])
        self.assertEqual(4, len(html5_ids))
        self.assertEqual(html5_ids[0], 'foo')
        self.assertEqual(html5_ids[1], 'foo.1.bar')
        self.assertEqual(html5_ids[2], 'baz.1.4')
        self.assertEqual(html5_ids[3], 'foo')

    @patch('xmodule.video_module.transcripts_utils.requests.get')
    def test_fail_downloading_subs(self, mock_get):

        mock_get.return_value = Mock(status_code=404, text='Error 404')

        bad_youtube_sub = 'BAD_YOUTUBE_ID2'
        self.clear_sub_content(bad_youtube_sub)

        with self.assertRaises(transcripts_utils.GetTranscriptsFromYouTubeException):
            transcripts_utils.download_youtube_subs(bad_youtube_sub, self.course, settings)

    def test_success_downloading_chinese_transcripts(self):

        # Disabled 11/14/13
        # This test is flaky because it performs an HTTP request on an external service
        # Re-enable when `requests.get` is patched using `mock.patch`
        pytest.skip()

        good_youtube_sub = 'j_jEn79vS3g'  # Chinese, utf-8
        self.clear_sub_content(good_youtube_sub)

        # Check transcripts_utils.GetTranscriptsFromYouTubeException not thrown
        transcripts_utils.download_youtube_subs(good_youtube_sub, self.course, settings)

        # Check assets status after importing subtitles.
        for subs_id in good_youtube_subs.values():
            filename = 'subs_{0}.srt.sjson'.format(subs_id)
            content_location = StaticContent.compute_location(
                self.course.id, filename
            )
            self.assertTrue(contentstore().find(content_location))

        self.clear_sub_content(good_youtube_sub)

    @patch('xmodule.video_module.transcripts_utils.requests.get')
    def test_get_transcript_name_youtube_server_success(self, mock_get):
        """
        Get transcript name from transcript_list fetch from youtube server api
        depends on language code, default language in YOUTUBE Text Api is "en"
        """
        youtube_text_api = copy.deepcopy(settings.YOUTUBE['TEXT_API'])
        youtube_text_api['params']['v'] = 'dummy_video_id'
        response_success = """
        <transcript_list>
            <track id="1" name="Custom" lang_code="en" />
            <track id="0" name="Custom1" lang_code="en-GB"/>
        </transcript_list>
        """
        mock_get.return_value = Mock(status_code=200, text=response_success, content=response_success.encode('utf-8'))

        transcript_name = transcripts_utils.youtube_video_transcript_name(youtube_text_api)
        self.assertEqual(transcript_name, 'Custom')

    @patch('xmodule.video_module.transcripts_utils.requests.get')
    def test_get_transcript_name_youtube_server_no_transcripts(self, mock_get):
        """
        When there are no transcripts of video transcript name will be None
        """
        youtube_text_api = copy.deepcopy(settings.YOUTUBE['TEXT_API'])
        youtube_text_api['params']['v'] = 'dummy_video_id'
        response_success = "<transcript_list></transcript_list>"
        mock_get.return_value = Mock(status_code=200, text=response_success, content=response_success.encode('utf-8'))

        transcript_name = transcripts_utils.youtube_video_transcript_name(youtube_text_api)
        self.assertIsNone(transcript_name)

    @patch('xmodule.video_module.transcripts_utils.requests.get')
    def test_get_transcript_name_youtube_server_language_not_exist(self, mock_get):
        """
        When the language does not exist in transcript_list transcript name will be None
        """
        youtube_text_api = copy.deepcopy(settings.YOUTUBE['TEXT_API'])
        youtube_text_api['params']['v'] = 'dummy_video_id'
        youtube_text_api['params']['lang'] = 'abc'
        response_success = """
        <transcript_list>
            <track id="1" name="Custom" lang_code="en" />
            <track id="0" name="Custom1" lang_code="en-GB"/>
        </transcript_list>
        """
        mock_get.return_value = Mock(status_code=200, text=response_success, content=response_success.encode('utf-8'))

        transcript_name = transcripts_utils.youtube_video_transcript_name(youtube_text_api)
        self.assertIsNone(transcript_name)

    @patch('xmodule.video_module.transcripts_utils.requests.get', side_effect=mock_requests_get)
    def test_downloading_subs_using_transcript_name(self, mock_get):
        """
        Download transcript using transcript name in url
        """
        good_youtube_sub = 'good_id_2'
        self.clear_sub_content(good_youtube_sub)

        transcripts_utils.download_youtube_subs(good_youtube_sub, self.course, settings)
        mock_get.assert_any_call(
            'http://video.google.com/timedtext',
            params={'lang': 'en', 'v': 'good_id_2', 'name': 'Custom'}
        )


class TestGenerateSubsFromSource(TestDownloadYoutubeSubs):
    """Tests for `generate_subs_from_source` function."""

    def test_success_generating_subs(self):
        youtube_subs = {
            0.5: 'JMD_ifUUfsU',
            1.0: 'hI10vDNYz4M',
            2.0: 'AKqURZnYqpk'
        }
        srt_filedata = textwrap.dedent("""
            1
            00:00:10,500 --> 00:00:13,000
            Elephant's Dream

            2
            00:00:15,000 --> 00:00:18,000
            At the left we can see...
        """)
        self.clear_subs_content(youtube_subs)

        # Check transcripts_utils.TranscriptsGenerationException not thrown.
        # Also checks that uppercase file extensions are supported.
        transcripts_utils.generate_subs_from_source(youtube_subs, 'SRT', srt_filedata, self.course)

        # Check assets status after importing subtitles.
        for subs_id in youtube_subs.values():
            filename = 'subs_{0}.srt.sjson'.format(subs_id)
            content_location = StaticContent.compute_location(
                self.course.id, filename
            )
            self.assertTrue(contentstore().find(content_location))

        self.clear_subs_content(youtube_subs)

    def test_fail_bad_subs_type(self):
        youtube_subs = {
            0.5: 'JMD_ifUUfsU',
            1.0: 'hI10vDNYz4M',
            2.0: 'AKqURZnYqpk'
        }

        srt_filedata = textwrap.dedent("""
            1
            00:00:10,500 --> 00:00:13,000
            Elephant's Dream

            2
            00:00:15,000 --> 00:00:18,000
            At the left we can see...
        """)

        with self.assertRaises(transcripts_utils.TranscriptsGenerationException) as cm:
            transcripts_utils.generate_subs_from_source(youtube_subs, 'BAD_FORMAT', srt_filedata, self.course)
        exception_message = text_type(cm.exception)
        self.assertEqual(exception_message, "We support only SubRip (*.srt) transcripts format.")

    def test_fail_bad_subs_filedata(self):
        youtube_subs = {
            0.5: 'JMD_ifUUfsU',
            1.0: 'hI10vDNYz4M',
            2.0: 'AKqURZnYqpk'
        }

        srt_filedata = """BAD_DATA"""

        with self.assertRaises(transcripts_utils.TranscriptsGenerationException) as cm:
            transcripts_utils.generate_subs_from_source(youtube_subs, 'srt', srt_filedata, self.course)
        exception_message = text_type(cm.exception)
        self.assertEqual(exception_message, "Something wrong with SubRip transcripts file during parsing.")


class TestGenerateSrtFromSjson(TestDownloadYoutubeSubs):
    """Tests for `generate_srt_from_sjson` function."""

    def test_success_generating_subs(self):
        sjson_subs = {
            'start': [100, 200, 240, 390, 54000],
            'end': [200, 240, 380, 1000, 78400],
            'text': [
                'subs #1',
                'subs #2',
                'subs #3',
                'subs #4',
                'subs #5'
            ]
        }
        srt_subs = transcripts_utils.generate_srt_from_sjson(sjson_subs, 1)
        self.assertTrue(srt_subs)
        expected_subs = [
            '00:00:00,100 --> 00:00:00,200\nsubs #1',
            '00:00:00,200 --> 00:00:00,240\nsubs #2',
            '00:00:00,240 --> 00:00:00,380\nsubs #3',
            '00:00:00,390 --> 00:00:01,000\nsubs #4',
            '00:00:54,000 --> 00:01:18,400\nsubs #5',
        ]

        for sub in expected_subs:
            self.assertIn(sub, srt_subs)

    def test_success_generating_subs_speed_up(self):
        sjson_subs = {
            'start': [100, 200, 240, 390, 54000],
            'end': [200, 240, 380, 1000, 78400],
            'text': [
                'subs #1',
                'subs #2',
                'subs #3',
                'subs #4',
                'subs #5'
            ]
        }
        srt_subs = transcripts_utils.generate_srt_from_sjson(sjson_subs, 0.5)
        self.assertTrue(srt_subs)
        expected_subs = [
            '00:00:00,050 --> 00:00:00,100\nsubs #1',
            '00:00:00,100 --> 00:00:00,120\nsubs #2',
            '00:00:00,120 --> 00:00:00,190\nsubs #3',
            '00:00:00,195 --> 00:00:00,500\nsubs #4',
            '00:00:27,000 --> 00:00:39,200\nsubs #5',
        ]
        for sub in expected_subs:
            self.assertIn(sub, srt_subs)

    def test_success_generating_subs_speed_down(self):
        sjson_subs = {
            'start': [100, 200, 240, 390, 54000],
            'end': [200, 240, 380, 1000, 78400],
            'text': [
                'subs #1',
                'subs #2',
                'subs #3',
                'subs #4',
                'subs #5'
            ]
        }
        srt_subs = transcripts_utils.generate_srt_from_sjson(sjson_subs, 2)
        self.assertTrue(srt_subs)

        expected_subs = [
            '00:00:00,200 --> 00:00:00,400\nsubs #1',
            '00:00:00,400 --> 00:00:00,480\nsubs #2',
            '00:00:00,480 --> 00:00:00,760\nsubs #3',
            '00:00:00,780 --> 00:00:02,000\nsubs #4',
            '00:01:48,000 --> 00:02:36,800\nsubs #5',
        ]
        for sub in expected_subs:
            self.assertIn(sub, srt_subs)

    def test_fail_generating_subs(self):
        sjson_subs = {
            'start': [100, 200],
            'end': [100],
            'text': [
                'subs #1',
                'subs #2'
            ]
        }
        srt_subs = transcripts_utils.generate_srt_from_sjson(sjson_subs, 1)
        self.assertFalse(srt_subs)


class TestYoutubeTranscripts(unittest.TestCase):
    """
    Tests for checking right datastructure returning when using youtube api.
    """
    @patch('xmodule.video_module.transcripts_utils.requests.get')
    def test_youtube_bad_status_code(self, mock_get):
        mock_get.return_value = Mock(status_code=404, text='test')
        youtube_id = 'bad_youtube_id'
        with self.assertRaises(transcripts_utils.GetTranscriptsFromYouTubeException):
            transcripts_utils.get_transcripts_from_youtube(youtube_id, settings, translation)

    @patch('xmodule.video_module.transcripts_utils.requests.get')
    def test_youtube_empty_text(self, mock_get):
        mock_get.return_value = Mock(status_code=200, text='')
        youtube_id = 'bad_youtube_id'
        with self.assertRaises(transcripts_utils.GetTranscriptsFromYouTubeException):
            transcripts_utils.get_transcripts_from_youtube(youtube_id, settings, translation)

    def test_youtube_good_result(self):
        response = textwrap.dedent("""<?xml version="1.0" encoding="utf-8" ?>
                <transcript>
                    <text start="0" dur="0.27"></text>
                    <text start="0.27" dur="2.45">Test text 1.</text>
                    <text start="2.72">Test text 2.</text>
                    <text start="5.43" dur="1.73">Test text 3.</text>
                </transcript>
        """)
        expected_transcripts = {
            'start': [270, 2720, 5430],
            'end': [2720, 2720, 7160],
            'text': ['Test text 1.', 'Test text 2.', 'Test text 3.']
        }
        youtube_id = 'good_youtube_id'
        with patch('xmodule.video_module.transcripts_utils.requests.get') as mock_get:
            mock_get.return_value = Mock(status_code=200, text=response, content=response.encode('utf-8'))
            transcripts = transcripts_utils.get_transcripts_from_youtube(youtube_id, settings, translation)
        self.assertEqual(transcripts, expected_transcripts)
        mock_get.assert_called_with('http://video.google.com/timedtext', params={'lang': 'en', 'v': 'good_youtube_id'})


class TestTranscript(unittest.TestCase):
    """
    Tests for Transcript class e.g. different transcript conversions.
    """
    def setUp(self):
        super(TestTranscript, self).setUp()

        self.srt_transcript = textwrap.dedent("""\
            0
            00:00:10,500 --> 00:00:13,000
            Elephant&#39;s Dream

            1
            00:00:15,000 --> 00:00:18,000
            At the left we can see...

        """)

        self.sjson_transcript = textwrap.dedent("""\
            {
                "start": [
                    10500,
                    15000
                ],
                "end": [
                    13000,
                    18000
                ],
                "text": [
                    "Elephant&#39;s Dream",
                    "At the left we can see..."
                ]
            }
        """)

        self.txt_transcript = u"Elephant's Dream\nAt the left we can see..."

    def test_convert_srt_to_txt(self):
        """
        Tests that the srt transcript is successfully converted into txt format.
        """
        expected = self.txt_transcript
        actual = transcripts_utils.Transcript.convert(self.srt_transcript, 'srt', 'txt')
        self.assertEqual(actual, expected)

    def test_convert_srt_to_srt(self):
        """
        Tests that srt to srt conversion works as expected.
        """
        expected = self.srt_transcript
        actual = transcripts_utils.Transcript.convert(self.srt_transcript, 'srt', 'srt')
        self.assertEqual(actual, expected)

    def test_convert_sjson_to_txt(self):
        """
        Tests that the sjson transcript is successfully converted into txt format.
        """
        expected = self.txt_transcript
        actual = transcripts_utils.Transcript.convert(self.sjson_transcript, 'sjson', 'txt')
        self.assertEqual(actual, expected)

    def test_convert_sjson_to_srt(self):
        """
        Tests that the sjson transcript is successfully converted into srt format.
        """
        expected = self.srt_transcript
        actual = transcripts_utils.Transcript.convert(self.sjson_transcript, 'sjson', 'srt')
        self.assertEqual(actual, expected)

    def test_convert_srt_to_sjson(self):
        """
        Tests that the srt transcript is successfully converted into sjson format.
        """
        expected = self.sjson_transcript
        actual = transcripts_utils.Transcript.convert(self.srt_transcript, 'srt', 'sjson')
        self.assertDictEqual(json.loads(actual), json.loads(expected))

    def test_convert_invalid_srt_to_sjson(self):
        """
        Tests that TranscriptsGenerationException was raises on trying
        to convert invalid srt transcript to sjson.
        """
        invalid_srt_transcript = 'invalid SubRip file content'
        with self.assertRaises(transcripts_utils.TranscriptsGenerationException):
            transcripts_utils.Transcript.convert(invalid_srt_transcript, 'srt', 'sjson')

    def test_dummy_non_existent_transcript(self):
        """
        Test `Transcript.asset` raises `NotFoundError` for dummy non-existent transcript.
        """
        with self.assertRaises(NotFoundError):
            transcripts_utils.Transcript.asset(None, transcripts_utils.NON_EXISTENT_TRANSCRIPT)

        with self.assertRaises(NotFoundError):
            transcripts_utils.Transcript.asset(None, None, filename=transcripts_utils.NON_EXISTENT_TRANSCRIPT)


class TestSubsFilename(unittest.TestCase):
    """
    Tests for subs_filename funtion.
    """

    def test_unicode(self):
        name = transcripts_utils.subs_filename(u"˙∆©ƒƒƒ")
        self.assertEqual(name, u'subs_˙∆©ƒƒƒ.srt.sjson')
        name = transcripts_utils.subs_filename(u"˙∆©ƒƒƒ", 'uk')
        self.assertEqual(name, u'uk_subs_˙∆©ƒƒƒ.srt.sjson')


@ddt.ddt
class TestVideoIdsInfo(unittest.TestCase):
    """
    Tests for `get_video_ids_info`.
    """
    @ddt.data(
        {
            'edx_video_id': '000-000-000',
            'youtube_id_1_0': '12as34',
            'html5_sources': [
                'www.abc.com/foo.mp4', 'www.abc.com/bar.webm', 'foo/bar/baz.m3u8'
            ],
            'expected_result': (False, ['000-000-000', '12as34', 'foo', 'bar', 'baz'])
        },
        {
            'edx_video_id': '',
            'youtube_id_1_0': '12as34',
            'html5_sources': [
                'www.abc.com/foo.mp4', 'www.abc.com/bar.webm', 'foo/bar/baz.m3u8'
            ],
            'expected_result': (True, ['12as34', 'foo', 'bar', 'baz'])
        },
        {
            'edx_video_id': '',
            'youtube_id_1_0': '',
            'html5_sources': [
                'www.abc.com/foo.mp4', 'www.abc.com/bar.webm',
            ],
            'expected_result': (True, ['foo', 'bar'])
        },
    )
    @ddt.unpack
    def test_get_video_ids_info(self, edx_video_id, youtube_id_1_0, html5_sources, expected_result):
        """
        Verify that `get_video_ids_info` works as expected.
        """
        actual_result = transcripts_utils.get_video_ids_info(edx_video_id, youtube_id_1_0, html5_sources)
        self.assertEqual(actual_result, expected_result)


@ddt.ddt
class TestGetTranscript(SharedModuleStoreTestCase):
    """Tests for `get_transcript` function."""

    def setUp(self):
        super(TestGetTranscript, self).setUp()

        self.course = CourseFactory.create()

        self.subs_id = 'video_101'

        self.subs_sjson = {
            'start': [100, 200, 240, 390, 1000],
            'end': [200, 240, 380, 1000, 1500],
            'text': [
                'subs #1',
                'subs #2',
                'subs #3',
                'subs #4',
                'subs #5'
            ]
        }

        self.subs_srt = transcripts_utils.Transcript.convert(json.dumps(self.subs_sjson), 'sjson', 'srt')

        self.subs = {
            u'en': self.subs_srt,
            u'ur': transcripts_utils.Transcript.convert(json.dumps(self.subs_sjson), 'sjson', 'srt'),
        }

        self.srt_mime_type = transcripts_utils.Transcript.mime_types[transcripts_utils.Transcript.SRT]
        self.sjson_mime_type = transcripts_utils.Transcript.mime_types[transcripts_utils.Transcript.SJSON]

        self.user = UserFactory.create()
        self.vertical = ItemFactory.create(category='vertical', parent_location=self.course.location)
        self.video = ItemFactory.create(
            category='video',
            parent_location=self.vertical.location,
            edx_video_id=u'1234-5678-90'
        )

    def create_transcript(self, subs_id, language=u'en', filename='video.srt', youtube_id_1_0='', html5_sources=None):
        """
        create transcript.
        """
        transcripts = {}
        if language != u'en':
            transcripts = {language: filename}

        html5_sources = html5_sources or []
        self.video = ItemFactory.create(
            category='video',
            parent_location=self.vertical.location,
            sub=subs_id,
            youtube_id_1_0=youtube_id_1_0,
            transcripts=transcripts,
            edx_video_id=u'1234-5678-90',
            html5_sources=html5_sources
        )

        possible_subs = [subs_id, youtube_id_1_0] + transcripts_utils.get_html5_ids(html5_sources)
        for possible_sub in possible_subs:
            if possible_sub:
                transcripts_utils.save_subs_to_store(
                    self.subs_sjson,
                    possible_sub,
                    self.video,
                    language=language,
                )

    def create_srt_file(self, content):
        """
        Create srt file.
        """
        srt_file = tempfile.NamedTemporaryFile(suffix=".srt")
        srt_file.content_type = transcripts_utils.Transcript.SRT
        srt_file.write(content)
        srt_file.seek(0)
        return srt_file

    def upload_file(self, subs_file, location, filename):
        """
        Upload a file in content store.

        Arguments:
            subs_file (File): pointer to file to be uploaded
            location (Locator): Item location
            filename (unicode): Name of file to be uploaded
        """
        mime_type = subs_file.content_type
        content_location = StaticContent.compute_location(
            location.course_key, filename
        )
        content = StaticContent(content_location, filename, mime_type, subs_file.read())
        contentstore().save(content)

    @ddt.data(
        # en lang does not exist so NotFoundError will be raised
        (u'en',),
        # ur lang does not exist so KeyError and then NotFoundError will be raised
        (u'ur',),
    )
    @ddt.unpack
    def test_get_transcript_not_found(self, lang):
        """
        Verify that `NotFoundError` exception is raised when transcript is not found in both the content store and val.
        """
        with self.assertRaises(NotFoundError):
            transcripts_utils.get_transcript(
                self.video,
                lang=lang
            )

    @ddt.data(
        # video.sub transcript
        {
            'language': u'en',
            'subs_id': 'video_101',
            'youtube_id_1_0': '',
            'html5_sources': [],
            'expected_filename': 'en_video_101.srt',
        },
        # if video.sub is present, rest will be skipped.
        {
            'language': u'en',
            'subs_id': 'video_101',
            'youtube_id_1_0': 'test_yt_id',
            'html5_sources': ['www.abc.com/foo.mp4'],
            'expected_filename': 'en_video_101.srt',
        },
        # video.youtube_id_1_0 transcript
        {
            'language': u'en',
            'subs_id': '',
            'youtube_id_1_0': 'test_yt_id',
            'html5_sources': [],
            'expected_filename': 'en_test_yt_id.srt',
        },
        # video.html5_sources transcript
        {
            'language': u'en',
            'subs_id': '',
            'youtube_id_1_0': '',
            'html5_sources': ['www.abc.com/foo.mp4'],
            'expected_filename': 'en_foo.srt',
        },
        # non-english transcript
        {
            'language': u'ur',
            'subs_id': '',
            'youtube_id_1_0': '',
            'html5_sources': [],
            'expected_filename': 'ur_video_101.srt',
        },
    )
    @ddt.unpack
    def test_get_transcript_from_contentstore(
        self,
        language,
        subs_id,
        youtube_id_1_0,
        html5_sources,
        expected_filename
    ):
        """
        Verify that `get_transcript` function returns correct data when transcript is in content store.
        """
        base_filename = 'video_101.srt'
        self.upload_file(self.create_srt_file(self.subs_srt.encode('utf-8')), self.video.location, base_filename)
        self.create_transcript(subs_id, language, base_filename, youtube_id_1_0, html5_sources)
        content, file_name, mimetype = transcripts_utils.get_transcript(
            self.video,
            language
        )

        self.assertEqual(content, self.subs[language])
        self.assertEqual(file_name, expected_filename)
        self.assertEqual(mimetype, self.srt_mime_type)

    def test_get_transcript_from_content_store_for_ur(self):
        """
        Verify that `get_transcript` function returns correct data for non-english when transcript is in content store.
        """
        language = u'ur'
        self.create_transcript(self.subs_id, language)
        content, filename, mimetype = transcripts_utils.get_transcript(
            self.video,
            language,
            output_format=transcripts_utils.Transcript.SJSON
        )

        self.assertEqual(json.loads(content), self.subs_sjson)
        self.assertEqual(filename, 'ur_video_101.sjson')
        self.assertEqual(mimetype, self.sjson_mime_type)

    @patch('xmodule.video_module.transcripts_utils.get_video_transcript_content')
    def test_get_transcript_from_val(self, mock_get_video_transcript_content):
        """
        Verify that `get_transcript` function returns correct data when transcript is in val.
        """
        mock_get_video_transcript_content.return_value = {
            'content': json.dumps(self.subs_sjson),
            'file_name': 'edx.sjson'
        }

        content, filename, mimetype = transcripts_utils.get_transcript(
            self.video,
        )
        self.assertEqual(content, self.subs_srt)
        self.assertEqual(filename, 'edx.srt')
        self.assertEqual(mimetype, self.srt_mime_type)

    def test_get_transcript_invalid_format(self):
        """
        Verify that `get_transcript` raises correct exception if transcript format is invalid.
        """
        with self.assertRaises(NotFoundError) as invalid_format_exception:
            transcripts_utils.get_transcript(
                self.video,
                'ur',
                output_format='mpeg'
            )

        exception_message = text_type(invalid_format_exception.exception)
        self.assertEqual(exception_message, 'Invalid transcript format `mpeg`')

    def test_get_transcript_no_content(self):
        """
        Verify that `get_transcript` function returns correct exception when transcript content is empty.
        """
        self.upload_file(self.create_srt_file(b''), self.video.location, 'ur_video_101.srt')
        self.create_transcript('', 'ur', 'ur_video_101.srt')

        with self.assertRaises(NotFoundError) as no_content_exception:
            transcripts_utils.get_transcript(
                self.video,
                'ur'
            )

        exception_message = text_type(no_content_exception.exception)
        self.assertEqual(exception_message, 'No transcript content')

    def test_get_transcript_no_en_transcript(self):
        """
        Verify that `get_transcript` function returns correct exception when no transcript exists for `en`.
        """
        self.video.youtube_id_1_0 = ''
        self.store.update_item(self.video, self.user.id)
        with self.assertRaises(NotFoundError) as no_en_transcript_exception:
            transcripts_utils.get_transcript(
                self.video,
                'en'
            )

        exception_message = text_type(no_en_transcript_exception.exception)
        self.assertEqual(exception_message, 'No transcript for `en` language')

    @ddt.data(
        transcripts_utils.TranscriptsGenerationException,
        UnicodeDecodeError('aliencodec', b'\x02\x01', 1, 2, 'alien codec found!')
    )
    @patch('xmodule.video_module.transcripts_utils.Transcript')
    def test_get_transcript_val_exceptions(self, exception_to_raise, mock_Transcript):
        """
        Verify that `get_transcript_from_val` function raises `NotFoundError` when specified exceptions raised.
        """
        mock_Transcript.convert.side_effect = exception_to_raise
        transcripts_info = self.video.get_transcripts_info()
        lang = self.video.get_default_transcript_language(transcripts_info)
        edx_video_id = transcripts_utils.clean_video_id(self.video.edx_video_id)
        with self.assertRaises(NotFoundError):
            transcripts_utils.get_transcript_from_val(
                edx_video_id,
                lang=lang,
                output_format=transcripts_utils.Transcript.SRT
            )

    @ddt.data(
        transcripts_utils.TranscriptsGenerationException,
        UnicodeDecodeError('aliencodec', b'\x02\x01', 1, 2, 'alien codec found!')
    )
    @patch('xmodule.video_module.transcripts_utils.Transcript')
    def test_get_transcript_content_store_exceptions(self, exception_to_raise, mock_Transcript):
        """
        Verify that `get_transcript_from_contentstore` function raises `NotFoundError` when specified exceptions raised.
        """
        mock_Transcript.asset.side_effect = exception_to_raise
        transcripts_info = self.video.get_transcripts_info()
        lang = self.video.get_default_transcript_language(transcripts_info)
        with self.assertRaises(NotFoundError):
            transcripts_utils.get_transcript_from_contentstore(
                self.video,
                language=lang,
                output_format=transcripts_utils.Transcript.SRT,
                transcripts_info=transcripts_info
            )
