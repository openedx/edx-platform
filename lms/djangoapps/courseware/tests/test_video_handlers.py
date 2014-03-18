# -*- coding: utf-8 -*-
"""Video xmodule tests in mongo."""

from mock import patch
import os
import tempfile
import textwrap
import json
from datetime import timedelta
from webob import Request

from xmodule.contentstore.content import StaticContent
from xmodule.modulestore import Location
from xmodule.contentstore.django import contentstore
from . import BaseTestXmodule
from .test_video_xml import SOURCE_XML
from cache_toolbox.core import del_cached_content
from xmodule.exceptions import NotFoundError


def _create_srt_file(content=None):
    """
    Create srt file in filesystem.
    """
    content = content or textwrap.dedent("""
        0
        00:00:00,12 --> 00:00:00,100
        Привіт, edX вітає вас.
    """)
    srt_file = tempfile.NamedTemporaryFile(suffix=".srt")
    srt_file.content_type = 'application/x-subrip'
    srt_file.write(content)
    srt_file.seek(0)
    return srt_file


def _clear_assets(location):
    """
    Clear all assets for location.
    """
    store = contentstore()

    content_location = StaticContent.compute_location(
        location.org, location.course, location.name
    )

    assets, __ = store.get_all_content_for_course(content_location)
    for asset in assets:
        asset_location = Location(asset["_id"])
        del_cached_content(asset_location)
        id = StaticContent.get_id_from_location(asset_location)
        store.delete(id)


def _get_subs_id(filename):
    basename = os.path.splitext(os.path.basename(filename))[0]
    return basename.replace('subs_', '').replace('.srt', '')


def _create_file(content=''):
    """
    Create temporary subs_somevalue.srt.sjson file.
    """
    sjson_file = tempfile.NamedTemporaryFile(prefix="subs_", suffix=".srt.sjson")
    sjson_file.content_type = 'application/json'
    sjson_file.write(textwrap.dedent(content))
    sjson_file.seek(0)
    return sjson_file


def _upload_sjson_file(subs_file, location, default_filename='subs_{}.srt.sjson'):
    filename = default_filename.format(_get_subs_id(subs_file.name))
    _upload_file(subs_file, location, filename)


def _upload_file(subs_file, location, filename):
    mime_type = subs_file.content_type
    content_location = StaticContent.compute_location(
        location.org, location.course, filename
    )
    content = StaticContent(content_location, filename, mime_type, subs_file.read())
    contentstore().save(content)
    del_cached_content(content.location)


class TestVideo(BaseTestXmodule):
    """Integration tests: web client + mongo."""
    CATEGORY = "video"
    DATA = SOURCE_XML
    METADATA = {}

    def test_handle_ajax_wrong_dispatch(self):
        responses = {
            user.username: self.clients[user.username].post(
                self.get_url('whatever'),
                {},
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            for user in self.users
        }

        self.assertEqual(
            set([
                response.status_code
                for _, response in responses.items()
                ]).pop(),
            404)

    def test_handle_ajax(self):

        data = [
            {'speed': 2.0},
            {'saved_video_position': "00:00:10"},
            {'transcript_language': 'uk'},
        ]
        for sample in data:
            response = self.clients[self.users[0].username].post(
                self.get_url('save_user_state'),
                sample,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(response.status_code, 200)

        self.assertEqual(self.item_descriptor.speed, None)
        self.item_descriptor.handle_ajax('save_user_state', {'speed': json.dumps(2.0)})
        self.assertEqual(self.item_descriptor.speed, 2.0)
        self.assertEqual(self.item_descriptor.global_speed, 2.0)

        self.assertEqual(self.item_descriptor.saved_video_position, timedelta(0))
        self.item_descriptor.handle_ajax('save_user_state', {'saved_video_position': "00:00:10"})
        self.assertEqual(self.item_descriptor.saved_video_position, timedelta(0, 10))

        self.assertEqual(self.item_descriptor.transcript_language, 'en')
        self.item_descriptor.handle_ajax('save_user_state', {'transcript_language': "uk"})
        self.assertEqual(self.item_descriptor.transcript_language, 'uk')

    def tearDown(self):
        _clear_assets(self.item_descriptor.location)

class TestTranscriptAvailableTranslationsDispatch(TestVideo):
    """
    Test video handler that provide available translations info.

    Tests for `available_translations` dispatch.
    """
    non_en_file = _create_srt_file()
    DATA = """
        <video show_captions="true"
        display_name="A Name"
        >
            <source src="example.mp4"/>
            <source src="example.webm"/>
            <transcript language="uk" src="{}"/>
        </video>
    """.format(os.path.split(non_en_file.name)[1])

    MODEL_DATA = {
        'data': DATA
    }

    def setUp(self):
        super(TestTranscriptAvailableTranslationsDispatch, self).setUp()
        self.item_descriptor.render('student_view')
        self.item = self.item_descriptor.xmodule_runtime.xmodule_instance
        self.subs = {"start": [10], "end": [100], "text": ["Hi, welcome to Edx."]}

    def test_available_translation_en(self):
        good_sjson = _create_file(json.dumps(self.subs))
        _upload_sjson_file(good_sjson, self.item_descriptor.location)
        self.item.sub = _get_subs_id(good_sjson.name)

        request = Request.blank('/translation')
        response = self.item.transcript(request=request, dispatch='available_translations')
        self.assertEqual(json.loads(response.body), ['en'])

    def test_available_translation_non_en(self):
        _upload_file(self.non_en_file, self.item_descriptor.location, os.path.split(self.non_en_file.name)[1])

        request = Request.blank('/translation')
        response = self.item.transcript(request=request, dispatch='available_translations')
        self.assertEqual(json.loads(response.body), ['uk'])

    def test_multiple_available_translations(self):
        good_sjson = _create_file(json.dumps(self.subs))
        
        # Upload english transcript.
        _upload_sjson_file(good_sjson, self.item_descriptor.location)

        # Upload non-english transcript.
        _upload_file(self.non_en_file, self.item_descriptor.location, os.path.split(self.non_en_file.name)[1])
        
        self.item.sub = _get_subs_id(good_sjson.name)  

        request = Request.blank('/translation')
        response = self.item.transcript(request=request, dispatch='available_translations')
        self.assertEqual(json.loads(response.body), ['en', 'uk'])

class TestTranscriptDownloadDispatch(TestVideo):
    """
    Test video handler that provide translation transcripts.

    Tests for `download` dispatch.
    """

    non_en_file = _create_srt_file()
    DATA = """
        <video show_captions="true"
        display_name="A Name"
        >
            <source src="example.mp4"/>
            <source src="example.webm"/>
            <transcript language="uk" src="{}"/>
        </video>
    """.format(os.path.split(non_en_file.name)[1])

    MODEL_DATA = {
        'data': DATA
    }

    def setUp(self):
        super(TestTranscriptDownloadDispatch, self).setUp()
        self.item_descriptor.render('student_view')
        self.item = self.item_descriptor.xmodule_runtime.xmodule_instance


    def test_language_is_not_supported(self):
        request = Request.blank('/download?language=ru')
        response = self.item.transcript(request=request, dispatch='download')
        self.assertEqual(response.status, '404 Not Found')

    def test_download_transcript_not_exist(self):
        request = Request.blank('/download?language=en')
        response = self.item.transcript(request=request, dispatch='download')
        self.assertEqual(response.status, '404 Not Found')

    @patch('xmodule.video_module.VideoModule.get_transcript', return_value=('Subs!', 'test_filename.srt', 'application/x-subrip'))
    def test_download_srt_exist(self, __):
        request = Request.blank('/download?language=en')
        response = self.item.transcript(request=request, dispatch='download')
        self.assertEqual(response.body, 'Subs!')
        self.assertEqual(response.headers['Content-Type'], 'application/x-subrip')

    @patch('xmodule.video_module.VideoModule.get_transcript', return_value=('Subs!', 'txt', 'text/plain'))
    def test_download_txt_exist(self, __):
        self.item.transcript_format = 'txt'
        request = Request.blank('/download?language=en')
        response = self.item.transcript(request=request, dispatch='download')
        self.assertEqual(response.body, 'Subs!')
        self.assertEqual(response.headers['Content-Type'], 'text/plain')

    def test_download_en_no_sub(self):
        request = Request.blank('/download?language=en')
        response = self.item.transcript(request=request, dispatch='download')
        self.assertEqual(response.status, '404 Not Found')
        with self.assertRaises(NotFoundError):
            self.item.get_transcript()

class TestTranscriptTranslationDispatch(TestVideo):
    """
    Test video handler that provide translation transcripts.

    Tests for `translation` dispatch.
    """

    non_en_file = _create_srt_file()
    DATA = """
        <video show_captions="true"
        display_name="A Name"
        >
            <source src="example.mp4"/>
            <source src="example.webm"/>
            <transcript language="uk" src="{}"/>
        </video>
    """.format(os.path.split(non_en_file.name)[1])

    MODEL_DATA = {
        'data': DATA
    }

    def setUp(self):
        super(TestTranscriptTranslationDispatch, self).setUp()
        self.item_descriptor.render('student_view')
        self.item = self.item_descriptor.xmodule_runtime.xmodule_instance

    def test_translation_fails(self):
        # No language
        request = Request.blank('/translation')
        response = self.item.transcript(request=request, dispatch='translation')
        self.assertEqual(response.status, '400 Bad Request')

        # No videoId - HTML5 video with language that is not in available languages
        request = Request.blank('/translation?language=ru')
        response = self.item.transcript(request=request, dispatch='translation')
        self.assertEqual(response.status, '404 Not Found')

        # Language is not in available languages
        request = Request.blank('/translation?language=ru&videoId=12345')
        response = self.item.transcript(request=request, dispatch='translation')
        self.assertEqual(response.status, '404 Not Found')

    def test_translaton_en_youtube_success(self):
        subs = {"start": [10], "end": [100], "text": ["Hi, welcome to Edx."]}
        good_sjson = _create_file(json.dumps(subs))
        _upload_sjson_file(good_sjson, self.item_descriptor.location)
        subs_id = _get_subs_id(good_sjson.name)

        self.item.sub = subs_id
        request = Request.blank('/translation?language=en&videoId={}'.format(subs_id))
        response = self.item.transcript(request=request, dispatch='translation')
        self.assertDictEqual(json.loads(response.body), subs)

    def test_translation_non_en_youtube_success(self):
        subs = {
            u'end': [100],
            u'start': [12],
            u'text': [
            u'\u041f\u0440\u0438\u0432\u0456\u0442, edX \u0432\u0456\u0442\u0430\u0454 \u0432\u0430\u0441.'
        ]}
        self.non_en_file.seek(0)
        _upload_file(self.non_en_file, self.item_descriptor.location, os.path.split(self.non_en_file.name)[1])
        subs_id = _get_subs_id(self.non_en_file.name)

        # youtube 1_0 request, will generate for all speeds for existing ids
        self.item.youtube_id_1_0 = subs_id
        self.item.youtube_id_0_75 = '0_75'
        request = Request.blank('/translation?language=uk&videoId={}'.format(subs_id))
        response = self.item.transcript(request=request, dispatch='translation')
        self.assertDictEqual(json.loads(response.body), subs)

        # 0_75 subs are exist
        request = Request.blank('/translation?language=uk&videoId={}'.format('0_75'))
        response = self.item.transcript(request=request, dispatch='translation')
        calculated_0_75 = {
            u'end': [75],
            u'start': [9],
            u'text': [
            u'\u041f\u0440\u0438\u0432\u0456\u0442, edX \u0432\u0456\u0442\u0430\u0454 \u0432\u0430\u0441.'
            ]
        }
        self.assertDictEqual(json.loads(response.body), calculated_0_75)
        # 1_5 will be generated from 1_0
        self.item.youtube_id_1_5 = '1_5'
        request = Request.blank('/translation?language=uk&videoId={}'.format('1_5'))
        response = self.item.transcript(request=request, dispatch='translation')
        calculated_1_5 = {
            u'end': [150],
            u'start': [18],
            u'text': [
            u'\u041f\u0440\u0438\u0432\u0456\u0442, edX \u0432\u0456\u0442\u0430\u0454 \u0432\u0430\u0441.'
            ]
        }
        self.assertDictEqual(json.loads(response.body), calculated_1_5)

    def test_translaton_en_html5_success(self):
        subs = {"start": [10], "end": [100], "text": ["Hi, welcome to Edx."]}
        good_sjson = _create_file(json.dumps(subs))
        _upload_sjson_file(good_sjson, self.item_descriptor.location)
        subs_id = _get_subs_id(good_sjson.name)

        self.item.sub = subs_id
        request = Request.blank('/translation?language=en')
        response = self.item.transcript(request=request, dispatch='translation')
        self.assertDictEqual(json.loads(response.body), subs)

    def test_translaton_non_en_html5_success(self):
        subs = {
            u'end': [100],
            u'start': [12],
            u'text': [
            u'\u041f\u0440\u0438\u0432\u0456\u0442, edX \u0432\u0456\u0442\u0430\u0454 \u0432\u0430\u0441.'
            ]
        }
        self.non_en_file.seek(0)
        _upload_file(self.non_en_file, self.item_descriptor.location, os.path.split(self.non_en_file.name)[1])

        # manually clean youtube_id_1_0, as it has default value
        self.item.youtube_id_1_0 = ""
        request = Request.blank('/translation?language=uk')
        response = self.item.transcript(request=request, dispatch='translation')
        self.assertDictEqual(json.loads(response.body), subs)


class TestGetTranscript(TestVideo):
    """
    Make sure that `get_transcript` method works correctly
    """
    non_en_file = _create_srt_file()
    DATA = """
        <video show_captions="true"
        display_name="A Name"
        >
            <source src="example.mp4"/>
            <source src="example.webm"/>
            <transcript language="uk" src="{}"/>
        </video>
    """.format(os.path.split(non_en_file.name)[1])

    MODEL_DATA = {
        'data': DATA
    }
    METADATA = {}

    def setUp(self):
        super(TestGetTranscript, self).setUp()
        self.item_descriptor.render('student_view')
        self.item = self.item_descriptor.xmodule_runtime.xmodule_instance

    def test_good_transcript(self):
        """
        Test for download 'en' sub with html5 video and self.sub has correct non-empty value.
        """
        good_sjson = _create_file(content=textwrap.dedent("""\
                {
                  "start": [
                    270,
                    2720
                  ],
                  "end": [
                    2720,
                    5430
                  ],
                  "text": [
                    "Hi, welcome to Edx.",
                    "Let&#39;s start with what is on your screen right now."
                  ]
                }
            """))

        _upload_sjson_file(good_sjson, self.item.location)
        self.item.sub = _get_subs_id(good_sjson.name)

        text, filename, mime_type = self.item.get_transcript()

        expected_text = textwrap.dedent("""\
            0
            00:00:00,270 --> 00:00:02,720
            Hi, welcome to Edx.

            1
            00:00:02,720 --> 00:00:05,430
            Let&#39;s start with what is on your screen right now.

            """)

        self.assertEqual(text, expected_text)
        self.assertEqual(filename[:-4], self.item.sub)
        self.assertEqual(mime_type, 'application/x-subrip')

    def test_good_txt_transcript(self):
        good_sjson = _create_file(content=textwrap.dedent("""\
                {
                  "start": [
                    270,
                    2720
                  ],
                  "end": [
                    2720,
                    5430
                  ],
                  "text": [
                    "Hi, welcome to Edx.",
                    "Let&#39;s start with what is on your screen right now."
                  ]
                }
            """))

        _upload_sjson_file(good_sjson, self.item.location)
        self.item.sub = _get_subs_id(good_sjson.name)
        text, filename, mime_type = self.item.get_transcript("txt")
        expected_text = textwrap.dedent("""\
            Hi, welcome to Edx.
            Let's start with what is on your screen right now.""")

        self.assertEqual(text, expected_text)
        self.assertEqual(filename, self.item.sub + '.txt')
        self.assertEqual(mime_type, 'text/plain')

    def test_en_with_empty_sub(self):

        # no self.sub, self.youttube_1_0 exist, but no file in assets
        with self.assertRaises(NotFoundError):
            self.item.get_transcript()

        # no self.sub and no self.youtube_1_0
        self.item.youtube_id_1_0 = None
        with self.assertRaises(ValueError):
            self.item.get_transcript()

        # no self.sub but youtube_1_0 exists with file in assets
        good_sjson = _create_file(content=textwrap.dedent("""\
                {
                  "start": [
                    270,
                    2720
                  ],
                  "end": [
                    2720,
                    5430
                  ],
                  "text": [
                    "Hi, welcome to Edx.",
                    "Let&#39;s start with what is on your screen right now."
                  ]
                }
            """))
        _upload_sjson_file(good_sjson, self.item.location)
        self.item.youtube_id_1_0 = _get_subs_id(good_sjson.name)

        text, filename, mime_type = self.item.get_transcript()
        expected_text = textwrap.dedent("""\
            0
            00:00:00,270 --> 00:00:02,720
            Hi, welcome to Edx.

            1
            00:00:02,720 --> 00:00:05,430
            Let&#39;s start with what is on your screen right now.

            """)

        self.assertEqual(text, expected_text)
        self.assertEqual(filename, self.item.youtube_id_1_0 + '.srt')
        self.assertEqual(mime_type, 'application/x-subrip')

    def test_non_en(self):
        self.item.transcript_language = 'uk'
        self.non_en_file.seek(0)
        _upload_file(self.non_en_file, self.item_descriptor.location, os.path.split(self.non_en_file.name)[1])

        text, filename, mime_type = self.item.get_transcript()
        expected_text = textwrap.dedent("""
        0
        00:00:00,12 --> 00:00:00,100
        Привіт, edX вітає вас.
        """)
        self.assertEqual(text, expected_text)
        self.assertEqual(filename, os.path.split(self.non_en_file.name)[1])
        self.assertEqual(mime_type, 'application/x-subrip')
        
    def test_value_error(self):
        good_sjson = _create_file(content='bad content')

        _upload_sjson_file(good_sjson, self.item.location)
        self.item.sub = _get_subs_id(good_sjson.name)

        with self.assertRaises(ValueError):
            self.item.get_transcript()

    def test_key_error(self):
        good_sjson = _create_file(content="""
                {
                  "start": [
                    270,
                    2720
                  ],
                  "end": [
                    2720,
                    5430
                  ]
                }
            """)

        _upload_sjson_file(good_sjson, self.item.location)
        self.item.sub = _get_subs_id(good_sjson.name)

        with self.assertRaises(KeyError):
            self.item.get_transcript()
