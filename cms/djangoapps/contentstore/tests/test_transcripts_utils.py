# -*- coding: utf-8 -*-
""" Tests for transcripts_utils. """
import unittest
from uuid import uuid4
import copy
import textwrap
from mock import patch, Mock

from django.test.utils import override_settings
from django.conf import settings
from django.utils import translation

from nose.plugins.skip import SkipTest

from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.contentstore.content import StaticContent
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.exceptions import NotFoundError
from xmodule.contentstore.django import contentstore
from xmodule.video_module import transcripts_utils
from contentstore.tests.utils import mock_requests_get

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
class TestSaveSubsToStore(ModuleStoreTestCase):
    """Tests for `save_subs_to_store` function."""

    org = 'MITx'
    number = '999'
    display_name = 'Test course'

    def clear_subs_content(self):
        """Remove, if subtitles content exists."""
        try:
            content = contentstore().find(self.content_location)
            contentstore().delete(content.location)
        except NotFoundError:
            pass

    def setUp(self):

        super(TestSaveSubsToStore, self).setUp()
        self.course = CourseFactory.create(
            org=self.org, number=self.number, display_name=self.display_name)

        self.subs = {
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

        self.subs_id = str(uuid4())
        filename = 'subs_{0}.srt.sjson'.format(self.subs_id)
        self.content_location = StaticContent.compute_location(self.course.id, filename)
        self.addCleanup(self.clear_subs_content)

        # incorrect subs
        self.unjsonable_subs = set([1])  # set can't be serialized

        self.unjsonable_subs_id = str(uuid4())
        filename_unjsonable = 'subs_{0}.srt.sjson'.format(self.unjsonable_subs_id)
        self.content_location_unjsonable = StaticContent.compute_location(self.course.id, filename_unjsonable)

        self.clear_subs_content()

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
        Assures that subs, that can't be dumped, can't be found later.
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


@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE)
class TestDownloadYoutubeSubs(ModuleStoreTestCase):
    """Tests for `download_youtube_subs` function."""

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

    def setUp(self):
        super(TestDownloadYoutubeSubs, self).setUp()
        self.course = CourseFactory.create(
            org=self.org, number=self.number, display_name=self.display_name)

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
            mock_get.return_value = Mock(status_code=200, text=response, content=response)
            # Check transcripts_utils.GetTranscriptsFromYouTubeException not thrown
            transcripts_utils.download_youtube_subs(good_youtube_sub, self.course, settings)

        mock_get.assert_any_call('http://video.google.com/timedtext', params={'lang': 'en', 'v': 'good_id_2'})

        # Check asset status after import of transcript.
        filename = 'subs_{0}.srt.sjson'.format(good_youtube_sub)
        content_location = StaticContent.compute_location(self.course.id, filename)
        self.assertTrue(contentstore().find(content_location))

        self.clear_sub_content(good_youtube_sub)

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

        # Check asset status after import of transcript.
        filename = 'subs_{0}.srt.sjson'.format(bad_youtube_sub)
        content_location = StaticContent.compute_location(
            self.course.id, filename
        )
        with self.assertRaises(NotFoundError):
            contentstore().find(content_location)

        self.clear_sub_content(bad_youtube_sub)

    def test_success_downloading_chinese_transcripts(self):

        # Disabled 11/14/13
        # This test is flakey because it performs an HTTP request on an external service
        # Re-enable when `requests.get` is patched using `mock.patch`
        raise SkipTest

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
        mock_get.return_value = Mock(status_code=200, text=response_success, content=response_success)

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
        mock_get.return_value = Mock(status_code=200, text=response_success, content=response_success)

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
        mock_get.return_value = Mock(status_code=200, text=response_success, content=response_success)

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

        # Check asset status after import of transcript.
        filename = 'subs_{0}.srt.sjson'.format(good_youtube_sub)
        content_location = StaticContent.compute_location(self.course.id, filename)
        self.assertTrue(contentstore().find(content_location))

        self.clear_sub_content(good_youtube_sub)


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
        exception_message = cm.exception.message
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
        exception_message = cm.exception.message
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
            mock_get.return_value = Mock(status_code=200, text=response, content=response)
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
        expected = self.txt_transcript
        actual = transcripts_utils.Transcript.convert(self.srt_transcript, 'srt', 'txt')
        self.assertEqual(actual, expected)

    def test_convert_srt_to_srt(self):
        expected = self.srt_transcript
        actual = transcripts_utils.Transcript.convert(self.srt_transcript, 'srt', 'srt')
        self.assertEqual(actual, expected)

    def test_convert_sjson_to_txt(self):
        expected = self.txt_transcript
        actual = transcripts_utils.Transcript.convert(self.sjson_transcript, 'sjson', 'txt')
        self.assertEqual(actual, expected)

    def test_convert_sjson_to_srt(self):
        expected = self.srt_transcript
        actual = transcripts_utils.Transcript.convert(self.sjson_transcript, 'sjson', 'srt')
        self.assertEqual(actual, expected)

    def test_convert_srt_to_sjson(self):
        with self.assertRaises(NotImplementedError):
            transcripts_utils.Transcript.convert(self.srt_transcript, 'srt', 'sjson')


class TestSubsFilename(unittest.TestCase):
    """
    Tests for subs_filename funtion.
    """

    def test_unicode(self):
        name = transcripts_utils.subs_filename(u"˙∆©ƒƒƒ")
        self.assertEqual(name, u'subs_˙∆©ƒƒƒ.srt.sjson')
        name = transcripts_utils.subs_filename(u"˙∆©ƒƒƒ", 'uk')
        self.assertEqual(name, u'uk_subs_˙∆©ƒƒƒ.srt.sjson')
