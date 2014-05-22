# -*- coding: utf-8 -*-
"""Video xmodule tests in mongo."""

from mock import patch, Mock
import os
import tempfile
import textwrap
import json
from datetime import timedelta
from webob import Request

from xmodule.contentstore.content import StaticContent
from xmodule.contentstore.django import contentstore
from xmodule.modulestore import Location
from xmodule.modulestore.django import editable_modulestore
from . import BaseTestXmodule
from .test_video_xml import SOURCE_XML
from cache_toolbox.core import del_cached_content
from xmodule.exceptions import NotFoundError

from xmodule.video_module.transcripts_utils import (
    TranscriptException,
    TranscriptsGenerationException,
)
from xmodule.modulestore.locations import AssetLocation

SRT_content = textwrap.dedent("""
        0
        00:00:00,12 --> 00:00:00,100
        Привіт, edX вітає вас.
    """)


def _create_srt_file(content=None):
    """
    Create srt file in filesystem.
    """
    content = content or SRT_content
    srt_file = tempfile.NamedTemporaryFile(suffix=".srt")
    srt_file.content_type = 'application/x-subrip; charset=utf-8'
    srt_file.write(content)
    srt_file.seek(0)
    return srt_file


def _check_asset(location, asset_name):
    """
    Check that asset with asset_name exists in assets.
    """
    content_location = StaticContent.compute_location(
        location.course_key, asset_name
    )
    try:
        contentstore().find(content_location)
    except NotFoundError:
        return False
    else:
        return True

def _clear_assets(location):
    """
    Clear all assets for location.
    """
    store = contentstore()

    assets, __ = store.get_all_content_for_course(location.course_key)
    for asset in assets:
        asset_location = AssetLocation._from_deprecated_son(asset["_id"], location.course_key.run)
        del_cached_content(asset_location)
        mongo_id = asset_location.to_deprecated_son()
        store.delete(mongo_id)


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
        location.course_key, filename
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

        request = Request.blank('/available_translations')
        response = self.item.transcript(request=request, dispatch='available_translations')
        self.assertEqual(json.loads(response.body), ['en'])

    def test_available_translation_non_en(self):
        _upload_file(self.non_en_file, self.item_descriptor.location, os.path.split(self.non_en_file.name)[1])

        request = Request.blank('/available_translations')
        response = self.item.transcript(request=request, dispatch='available_translations')
        self.assertEqual(json.loads(response.body), ['uk'])

    def test_multiple_available_translations(self):
        good_sjson = _create_file(json.dumps(self.subs))

        # Upload english transcript.
        _upload_sjson_file(good_sjson, self.item_descriptor.location)

        # Upload non-english transcript.
        _upload_file(self.non_en_file, self.item_descriptor.location, os.path.split(self.non_en_file.name)[1])

        self.item.sub = _get_subs_id(good_sjson.name)

        request = Request.blank('/available_translations')
        response = self.item.transcript(request=request, dispatch='available_translations')
        self.assertEqual(json.loads(response.body), ['en', 'uk'])


class TestTranscriptDownloadDispatch(TestVideo):
    """
    Test video handler that provide translation transcripts.

    Tests for `download` dispatch.
    """

    DATA = """
        <video show_captions="true"
        display_name="A Name"
        sub='OEoXaMPEzfM'
        >
            <source src="example.mp4"/>
            <source src="example.webm"/>
        </video>
    """

    MODEL_DATA = {
        'data': DATA
    }

    def setUp(self):
        super(TestTranscriptDownloadDispatch, self).setUp()
        self.item_descriptor.render('student_view')
        self.item = self.item_descriptor.xmodule_runtime.xmodule_instance

    def test_download_transcript_not_exist(self):
        request = Request.blank('/download')
        response = self.item.transcript(request=request, dispatch='download')
        self.assertEqual(response.status, '404 Not Found')

    @patch('xmodule.video_module.VideoModule.get_transcript', return_value=('Subs!', 'test_filename.srt', 'application/x-subrip; charset=utf-8'))
    def test_download_srt_exist(self, __):
        request = Request.blank('/download')
        response = self.item.transcript(request=request, dispatch='download')
        self.assertEqual(response.body, 'Subs!')
        self.assertEqual(response.headers['Content-Type'], 'application/x-subrip; charset=utf-8')
        self.assertEqual(response.headers['Content-Language'], 'en')

    @patch('xmodule.video_module.VideoModule.get_transcript', return_value=('Subs!', 'txt', 'text/plain; charset=utf-8'))
    def test_download_txt_exist(self, __):
        self.item.transcript_format = 'txt'
        request = Request.blank('/download')
        response = self.item.transcript(request=request, dispatch='download')
        self.assertEqual(response.body, 'Subs!')
        self.assertEqual(response.headers['Content-Type'], 'text/plain; charset=utf-8')
        self.assertEqual(response.headers['Content-Language'], 'en')

    def test_download_en_no_sub(self):
        request = Request.blank('/download')
        response = self.item.transcript(request=request, dispatch='download')
        self.assertEqual(response.status, '404 Not Found')
        with self.assertRaises(NotFoundError):
            self.item.get_transcript()

    @patch('xmodule.video_module.VideoModule.get_transcript', return_value=('Subs!', u"塞.srt", 'application/x-subrip; charset=utf-8'))
    def test_download_non_en_non_ascii_filename(self, __):
        request = Request.blank('/download')
        response = self.item.transcript(request=request, dispatch='download')
        self.assertEqual(response.body, 'Subs!')
        self.assertEqual(response.headers['Content-Type'], 'application/x-subrip; charset=utf-8')
        self.assertEqual(response.headers['Content-Disposition'], 'attachment; filename="塞.srt"')


class TestTranscriptTranslationGetDispatch(TestVideo):
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
        super(TestTranscriptTranslationGetDispatch, self).setUp()
        self.item_descriptor.render('student_view')
        self.item = self.item_descriptor.xmodule_runtime.xmodule_instance

    def test_translation_fails(self):
        # No language
        request = Request.blank('/translation')
        response = self.item.transcript(request=request, dispatch='translation')
        self.assertEqual(response.status, '400 Bad Request')

        # No videoId - HTML5 video with language that is not in available languages
        request = Request.blank('/translation/ru')
        response = self.item.transcript(request=request, dispatch='translation/ru')
        self.assertEqual(response.status, '404 Not Found')

        # Language is not in available languages
        request = Request.blank('/translation/ru?videoId=12345')
        response = self.item.transcript(request=request, dispatch='translation/ru')
        self.assertEqual(response.status, '404 Not Found')

    def test_translaton_en_youtube_success(self):
        subs = {"start": [10], "end": [100], "text": ["Hi, welcome to Edx."]}
        good_sjson = _create_file(json.dumps(subs))
        _upload_sjson_file(good_sjson, self.item_descriptor.location)
        subs_id = _get_subs_id(good_sjson.name)

        self.item.sub = subs_id
        request = Request.blank('/translation/en?videoId={}'.format(subs_id))
        response = self.item.transcript(request=request, dispatch='translation/en')
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
        request = Request.blank('/translation/uk?videoId={}'.format(subs_id))
        response = self.item.transcript(request=request, dispatch='translation/uk')
        self.assertDictEqual(json.loads(response.body), subs)

        # 0_75 subs are exist
        request = Request.blank('/translation/uk?videoId={}'.format('0_75'))
        response = self.item.transcript(request=request, dispatch='translation/uk')
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
        request = Request.blank('/translation/uk?videoId={}'.format('1_5'))
        response = self.item.transcript(request=request, dispatch='translation/uk')
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
        request = Request.blank('/translation/en')
        response = self.item.transcript(request=request, dispatch='translation/en')
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
        request = Request.blank('/translation/uk')
        response = self.item.transcript(request=request, dispatch='translation/uk')
        self.assertDictEqual(json.loads(response.body), subs)

    def test_translation_static_transcript(self):
        """
        Set course static_asset_path and ensure we get redirected to that path
        if it isn't found in the contentstore
        """
        self.course.static_asset_path = 'dummy/static'
        self.course.save()
        store = editable_modulestore()
        store.update_item(self.course, 'OEoXaMPEzfM')

        # Test youtube style en
        request = Request.blank('/translation/en?videoId=12345')
        response = self.item.transcript(request=request, dispatch='translation/en')
        self.assertEqual(response.status, '307 Temporary Redirect')
        self.assertIn(
            ('Location', '/static/dummy/static/subs_12345.srt.sjson'),
            response.headerlist
        )

        # Test HTML5 video style
        self.item.sub = 'OEoXaMPEzfM'
        request = Request.blank('/translation/en')
        response = self.item.transcript(request=request, dispatch='translation/en')
        self.assertEqual(response.status, '307 Temporary Redirect')
        self.assertIn(
            ('Location', '/static/dummy/static/subs_OEoXaMPEzfM.srt.sjson'),
            response.headerlist
        )

        # Test different language to ensure we are just ignoring it since we can't
        # translate with static fallback
        request = Request.blank('/translation/uk')
        response = self.item.transcript(request=request, dispatch='translation/uk')
        self.assertEqual(response.status, '404 Not Found')

    def test_xml_transcript(self):
        """
        Set data_dir and remove runtime modulestore to simulate an XMLModuelStore course.
        Then run the same tests as static_asset_path run.
        """
        # Simulate XMLModuleStore xmodule
        self.item_descriptor.data_dir = 'dummy/static'
        del self.item_descriptor.runtime.modulestore

        self.assertFalse(self.course.static_asset_path)

        # Test youtube style en
        request = Request.blank('/translation/en?videoId=12345')
        response = self.item.transcript(request=request, dispatch='translation/en')
        self.assertEqual(response.status, '307 Temporary Redirect')
        self.assertIn(
            ('Location', '/static/dummy/static/subs_12345.srt.sjson'),
            response.headerlist
        )

        # Test HTML5 video style
        self.item.sub = 'OEoXaMPEzfM'
        request = Request.blank('/translation/en')
        response = self.item.transcript(request=request, dispatch='translation/en')
        self.assertEqual(response.status, '307 Temporary Redirect')
        self.assertIn(
            ('Location', '/static/dummy/static/subs_OEoXaMPEzfM.srt.sjson'),
            response.headerlist
        )

        # Test different language to ensure we are just ignoring it since we can't
        # translate with static fallback
        request = Request.blank('/translation/uk')
        response = self.item.transcript(request=request, dispatch='translation/uk')
        self.assertEqual(response.status, '404 Not Found')


class TestStudioTranscriptTranslationGetDispatch(TestVideo):
    """
    Test Studio video handler that provide translation transcripts.

    Tests for `translation` dispatch GET HTTP method.
    """
    non_en_file = _create_srt_file()
    DATA = """
        <video show_captions="true"
        display_name="A Name"
        >
            <source src="example.mp4"/>
            <source src="example.webm"/>
            <transcript language="uk" src="{}"/>
            <transcript language="zh" src="{}"/>
        </video>
    """.format(os.path.split(non_en_file.name)[1], u"塞.srt".encode('utf8'))

    MODEL_DATA = {'data': DATA}

    def test_translation_fails(self):
        # No language
        request = Request.blank('')
        response = self.item_descriptor.studio_transcript(request=request, dispatch='translation')
        self.assertEqual(response.status, '400 Bad Request')

        # No filename in request.GET
        request = Request.blank('')
        response = self.item_descriptor.studio_transcript(request=request, dispatch='translation/uk')
        self.assertEqual(response.status, '400 Bad Request')

        # Correct case:
        filename = os.path.split(self.non_en_file.name)[1]
        _upload_file(self.non_en_file, self.item_descriptor.location, filename)
        self.non_en_file.seek(0)
        request = Request.blank(u'translation/uk?filename={}'.format(filename))
        response = self.item_descriptor.studio_transcript(request=request, dispatch='translation/uk')
        self.assertEqual(response.body, self.non_en_file.read())
        self.assertEqual(response.headers['Content-Type'], 'application/x-subrip; charset=utf-8')
        self.assertEqual(
            response.headers['Content-Disposition'],
            'attachment; filename="{}"'.format(filename)
        )
        self.assertEqual(response.headers['Content-Language'], 'uk')

        # Non ascii file name download:
        self.non_en_file.seek(0)
        _upload_file(self.non_en_file, self.item_descriptor.location, u'塞.srt')
        self.non_en_file.seek(0)
        request = Request.blank('translation/zh?filename={}'.format(u'塞.srt'.encode('utf8')))
        response = self.item_descriptor.studio_transcript(request=request, dispatch='translation/zh')
        self.assertEqual(response.body, self.non_en_file.read())
        self.assertEqual(response.headers['Content-Type'], 'application/x-subrip; charset=utf-8')
        self.assertEqual(response.headers['Content-Disposition'], 'attachment; filename="塞.srt"')
        self.assertEqual(response.headers['Content-Language'], 'zh')


class TestStudioTranscriptTranslationPostDispatch(TestVideo):
    """
    Test Studio video handler that provide translation transcripts.

    Tests for `translation` dispatch with HTTP POST method.
    """
    DATA = """
        <video show_captions="true"
        display_name="A Name"
        >
            <source src="example.mp4"/>
            <source src="example.webm"/>

        </video>
    """

    MODEL_DATA = {
        'data': DATA
    }

    METADATA = {}

    def test_studio_transcript_post(self):
        # Check for exceptons:

        # Language is passed, bad content or filename:

        # should be first, as other tests save transcrips to store.
        request = Request.blank('/translation/uk', POST={'file': ('filename.srt', SRT_content)})
        with patch('xmodule.video_module.video_handlers.save_to_store'):
            with self.assertRaises(TranscriptException):  # transcripts were not saved to store for some reason.
                response = self.item_descriptor.studio_transcript(request=request, dispatch='translation/uk')
        request = Request.blank('/translation/uk', POST={'file': ('filename', 'content')})
        with self.assertRaises(TranscriptsGenerationException):  # Not an srt filename
            self.item_descriptor.studio_transcript(request=request, dispatch='translation/uk')

        request = Request.blank('/translation/uk', POST={'file': ('filename.srt', 'content')})
        with self.assertRaises(TranscriptsGenerationException):  # Content format is not srt.
            response = self.item_descriptor.studio_transcript(request=request, dispatch='translation/uk')

        request = Request.blank('/translation/uk', POST={'file': ('filename.srt', SRT_content.decode('utf8').encode('cp1251'))})
        with self.assertRaises(UnicodeDecodeError):  # Non-UTF8 file content encoding.
            response = self.item_descriptor.studio_transcript(request=request, dispatch='translation/uk')

        # No language is passed.
        request = Request.blank('/translation', POST={'file': ('filename', SRT_content)})
        response = self.item_descriptor.studio_transcript(request=request, dispatch='translation')
        self.assertEqual(response.status,  '400 Bad Request')

        # Language, good filename and good content.
        request = Request.blank('/translation/uk', POST={'file': ('filename.srt', SRT_content)})
        response = self.item_descriptor.studio_transcript(request=request, dispatch='translation/uk')
        self.assertEqual(response.status, '201 Created')
        self.assertDictEqual(json.loads(response.body), {'filename': u'filename.srt', 'status': 'Success'})
        self.assertDictEqual(self.item_descriptor.transcripts, {})
        self.assertTrue(_check_asset(self.item_descriptor.location, u'filename.srt'))


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
            <transcript language="zh" src="{}"/>
        </video>
    """.format(os.path.split(non_en_file.name)[1], u"塞.srt".encode('utf8'))

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
        self.assertEqual(mime_type, 'application/x-subrip; charset=utf-8')

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
        self.assertEqual(mime_type, 'text/plain; charset=utf-8')

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
        self.assertEqual(mime_type, 'application/x-subrip; charset=utf-8')

    def test_non_en_with_non_ascii_filename(self):
        self.item.transcript_language = 'zh'
        self.non_en_file.seek(0)
        _upload_file(self.non_en_file, self.item_descriptor.location, u"塞.srt")

        text, filename, mime_type = self.item.get_transcript()
        expected_text = textwrap.dedent("""
        0
        00:00:00,12 --> 00:00:00,100
        Привіт, edX вітає вас.
        """)
        self.assertEqual(text, expected_text)
        self.assertEqual(filename, u"塞.srt")
        self.assertEqual(mime_type, 'application/x-subrip; charset=utf-8')

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


class TestVideoGradeHandler(TestVideo):
    """
    Test video grade handler.
    """

    DATA = """
        <video show_captions="true"
        display_name="A Name"
        has_score="True"
        scored_on_end="True"
        scored_on_percent="75"
        >
            <source src="example.mp4"/>
            <source src="example.webm"/>
        </video>
    """

    MODEL_DATA = {
        'data': DATA
    }

    def setUp(self):
        super(TestVideoGradeHandler, self).setUp()
        self.item_descriptor.render('student_view')
        self.item = self.item_descriptor.xmodule_runtime.xmodule_instance

    def test_no_grader_name(self):
        # no grader name in graders
        request = Request.blank('')
        response = self.item.grade_handler(request=request, dispatch='')
        self.assertEqual(response.status, '400 Bad Request')

    def test_unknown_grader_name(self):
        request = Request.blank('', POST={'graderName': 'unknown_grader'})
        response = self.item.grade_handler(request=request, dispatch='')
        self.assertEqual(response.status, '400 Bad Request')

    def test_grader(self):
        self.item.runtime.get_real_user = Mock()
        self.item.runtime.publish = Mock()

        first_grader = 'scored_on_end'
        self.assertFalse(self.item.cumulative_score[first_grader]['isScored'])
        request = Request.blank('', POST={'graderName': first_grader})
        response = self.item.grade_handler(request=request, dispatch='')
        self.assertTrue(self.item.cumulative_score[first_grader]['isScored'])
        self.assertEqual(response.status_code, 200)

        second_grader = 'scored_on_percent'
        self.assertFalse(self.item.cumulative_score[second_grader]['isScored'])
        request = Request.blank('', POST={'graderName': second_grader})
        response = self.item.grade_handler(request=request, dispatch='')
        self.assertTrue(self.item.cumulative_score[second_grader]['isScored'])
        self.assertEqual(response.status_code, 200)

    def test_no_real_user(self):
        self.item.runtime.get_real_user = Mock(return_value=None)
        self.item.cumulative_score['scored_on_end']['isScored'] = True
        request = Request.blank('', POST={'graderName': 'scored_on_percent'})
        response = self.item.grade_handler(request=request, dispatch='')
        self.assertEqual(response.status_code, 500)

    def test_grader_in_studio(self):
        self.item.runtime.get_real_user = None
        self.item.cumulative_score['scored_on_end']['isScored'] = True
        request = Request.blank('', POST={'graderName': 'scored_on_percent'})
        response = self.item.grade_handler(request=request, dispatch='')
        self.assertFalse(self.item.cumulative_score['scored_on_percent']['isScored'])
        self.assertEqual(response.status_code, 501)  # NotImplemented

    def test_handle_ajax_graded(self):
        expected_graders_before = {
            'scored_on_end': {
                'isScored': False, 'graderValue': True,
                'graderState': None, 'saveState': False,
            },
            'scored_on_percent': {
                'isScored': False, 'graderValue': 75,
                'graderState': None, 'saveState': True,
            },
        }
        self.assertEqual(self.item_descriptor.cumulative_score, expected_graders_before)
        
        graders = {
            'cumulative_score':
            '{"scored_on_percent": true}'
        }
        self.item_descriptor.handle_ajax('save_user_state', graders)
        
        expected_graders_after = {
           'scored_on_end': {
                'isScored': False, 'graderValue': True,
                'graderState': None, 'saveState': False,
            },
            'scored_on_percent': {
                'isScored': False, 'graderValue': 75,
                'graderState': True, 'saveState': True,
            },
        }
        self.assertEqual(self.item_descriptor.cumulative_score, expected_graders_after)
