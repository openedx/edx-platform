# -*- coding: utf-8 -*-
"""Video xmodule tests in mongo."""


import json
import os
import tempfile
import textwrap
from datetime import timedelta

import ddt
import freezegun
import six
from django.core.files.base import ContentFile
from django.utils.timezone import now
from edxval import api
from mock import MagicMock, Mock, patch
from webob import Request, Response

from common.test.utils import normalize_repr
from openedx.core.djangoapps.contentserver.caching import del_cached_content
from xmodule.contentstore.content import StaticContent
from xmodule.contentstore.django import contentstore
from xmodule.exceptions import NotFoundError
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.video_module import VideoBlock
from xmodule.video_module.transcripts_utils import (
    Transcript,
    edxval_api,
    get_transcript,
    subs_filename,
)
from xmodule.x_module import STUDENT_VIEW

from .helpers import BaseTestXmodule
from .test_video_xml import SOURCE_XML

TRANSCRIPT = {"start": [10], "end": [100], "text": ["Hi, welcome to Edx."]}
BUMPER_TRANSCRIPT = {"start": [1], "end": [10], "text": ["A bumper"]}
SRT_content = textwrap.dedent(u"""
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
    srt_file.write(content.encode('utf-8'))
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
        asset_location = asset['asset_key']
        del_cached_content(asset_location)
        store.delete(asset_location)


def _get_subs_id(filename):
    basename = os.path.splitext(os.path.basename(filename))[0]
    return basename.replace('subs_', '').replace('.srt', '')


def _create_file(content=''):
    """
    Create temporary subs_somevalue.srt.sjson file.
    """
    sjson_file = tempfile.NamedTemporaryFile(prefix="subs_", suffix=".srt.sjson")
    sjson_file.content_type = 'application/json'
    sjson_file.write(textwrap.dedent(content).encode('utf-8'))
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


@normalize_repr
def attach_sub(item, filename):
    """
    Attach `en` transcript.
    """
    item.sub = filename


@normalize_repr
def attach_bumper_transcript(item, filename, lang="en"):
    """
    Attach bumper transcript.
    """
    item.video_bumper["transcripts"][lang] = filename


class BaseTestVideoXBlock(BaseTestXmodule):
    """Base class for VideoXBlock tests."""

    CATEGORY = 'video'

    def initialize_block(self, data=None, **kwargs):
        """ Initialize an XBlock to run tests on. """
        if data:
            # VideoBlock data field is no longer used but to avoid needing to re-do
            # a lot of tests code, parse and set the values as fields.
            fields_data = VideoBlock.parse_video_xml(data)
            kwargs.update(fields_data)
        super(BaseTestVideoXBlock, self).initialize_module(**kwargs)

    def setUp(self):
        super(BaseTestVideoXBlock, self).setUp()
        self.initialize_block(data=self.DATA, metadata=self.METADATA)


class TestVideo(BaseTestVideoXBlock):
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

        status_codes = {response.status_code for response in responses.values()}
        self.assertEqual(status_codes.pop(), 404)

    def test_handle_ajax_for_speed_with_nan(self):
        self.item_descriptor.handle_ajax('save_user_state', {'speed': json.dumps(1.0)})
        self.assertEqual(self.item_descriptor.speed, 1.0)
        self.assertEqual(self.item_descriptor.global_speed, 1.0)

        # try to set NaN value for speed.
        response = self.item_descriptor.handle_ajax(
            'save_user_state', {'speed': json.dumps(float('NaN'))}
        )

        self.assertFalse(json.loads(response)['success'])
        expected_error = u"Invalid speed value nan, must be a float."
        self.assertEqual(json.loads(response)['error'], expected_error)

        # verify that the speed and global speed are still 1.0
        self.assertEqual(self.item_descriptor.speed, 1.0)
        self.assertEqual(self.item_descriptor.global_speed, 1.0)

    def test_handle_ajax(self):

        data = [
            {u'speed': 2.0},
            {u'saved_video_position': "00:00:10"},
            {u'transcript_language': 'uk'},
            {u'bumper_do_not_show_again': True},
            {u'bumper_last_view_date': True},
            {u'demoo�': 'sample'}
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

        self.assertEqual(self.item_descriptor.bumper_do_not_show_again, False)
        self.item_descriptor.handle_ajax('save_user_state', {'bumper_do_not_show_again': True})
        self.assertEqual(self.item_descriptor.bumper_do_not_show_again, True)

        with freezegun.freeze_time(now()):
            self.assertEqual(self.item_descriptor.bumper_last_view_date, None)
            self.item_descriptor.handle_ajax('save_user_state', {'bumper_last_view_date': True})
            self.assertEqual(self.item_descriptor.bumper_last_view_date, now())

        response = self.item_descriptor.handle_ajax('save_user_state', {u'demoo�': "sample"})
        self.assertEqual(json.loads(response)['success'], True)

    def get_handler_url(self, handler, suffix):
        """
        Return the URL for the specified handler on self.item_descriptor.
        """
        return self.item_descriptor.xmodule_runtime.handler_url(
            self.item_descriptor, handler, suffix
        ).rstrip('/?')

    def tearDown(self):
        _clear_assets(self.item_descriptor.location)
        super(TestVideo, self).tearDown()


@ddt.ddt
class TestTranscriptAvailableTranslationsDispatch(TestVideo):
    """
    Test video handler that provide available translations info.

    Tests for `available_translations` dispatch.
    """
    srt_file = _create_srt_file()
    DATA = u"""
        <video show_captions="true"
        display_name="A Name"
        >
            <source src="example.mp4"/>
            <source src="example.webm"/>
            <transcript language="uk" src="{}"/>
        </video>
    """.format(os.path.split(srt_file.name)[1])

    MODEL_DATA = {
        'data': DATA
    }

    def setUp(self):
        super(TestTranscriptAvailableTranslationsDispatch, self).setUp()
        self.item_descriptor.render(STUDENT_VIEW)
        self.item = self.item_descriptor
        self.subs = {"start": [10], "end": [100], "text": ["Hi, welcome to Edx."]}

    def test_available_translation_en(self):
        good_sjson = _create_file(json.dumps(self.subs))
        _upload_sjson_file(good_sjson, self.item_descriptor.location)
        self.item.sub = _get_subs_id(good_sjson.name)

        request = Request.blank('/available_translations')
        response = self.item.transcript(request=request, dispatch='available_translations')
        self.assertEqual(json.loads(response.body.decode('utf-8')), ['en'])

    def test_available_translation_non_en(self):
        _upload_file(_create_srt_file(), self.item_descriptor.location, os.path.split(self.srt_file.name)[1])

        request = Request.blank('/available_translations')
        response = self.item.transcript(request=request, dispatch='available_translations')
        self.assertEqual(json.loads(response.body.decode('utf-8')), ['uk'])

    @patch('xmodule.video_module.transcripts_utils.get_video_transcript_content')
    def test_multiple_available_translations(self, mock_get_video_transcript_content):
        mock_get_video_transcript_content.return_value = {
            'content': json.dumps({
                "start": [10],
                "end": [100],
                "text": ["Hi, welcome to Edx."],
            }),
            'file_name': 'edx.sjson'
        }

        good_sjson = _create_file(json.dumps(self.subs))

        # Upload english transcript.
        _upload_sjson_file(good_sjson, self.item_descriptor.location)

        # Upload non-english transcript.
        _upload_file(self.srt_file, self.item_descriptor.location, os.path.split(self.srt_file.name)[1])

        self.item.sub = _get_subs_id(good_sjson.name)
        self.item.edx_video_id = 'an-edx-video-id'

        request = Request.blank('/available_translations')
        response = self.item.transcript(request=request, dispatch='available_translations')
        self.assertEqual(sorted(json.loads(response.body.decode('utf-8'))), sorted(['en', 'uk']))

    @patch('xmodule.video_module.transcripts_utils.get_video_transcript_content')
    @patch('xmodule.video_module.transcripts_utils.get_available_transcript_languages')
    @ddt.data(
        (
            ['en', 'uk', 'ro'],
            '',
            {},
            ['en', 'uk', 'ro']
        ),
        (
            ['uk', 'ro'],
            True,
            {},
            ['en', 'uk', 'ro']
        ),
        (
            ['de', 'ro'],
            True,
            {
                'uk': True,
                'ro': False,
            },
            ['en', 'uk', 'de', 'ro']
        ),
        (
            ['de'],
            True,
            {
                'uk': True,
                'ro': False,
            },
            ['en', 'uk', 'de', 'ro']
        ),
    )
    @ddt.unpack
    def test_val_available_translations(
        self,
        val_transcripts,
        sub,
        transcripts,
        result,
        mock_get_transcript_languages,
        mock_get_video_transcript_content
    ):
        """
        Tests available translations with video component's and val's transcript languages
        while the feature is enabled.
        """
        for lang_code, in_content_store in six.iteritems(dict(transcripts)):
            if in_content_store:
                file_name, __ = os.path.split(self.srt_file.name)
                _upload_file(self.srt_file, self.item_descriptor.location, file_name)
                transcripts[lang_code] = file_name
            else:
                transcripts[lang_code] = 'non_existent.srt.sjson'
        if sub:
            sjson_transcript = _create_file(json.dumps(self.subs))
            _upload_sjson_file(sjson_transcript, self.item_descriptor.location)
            sub = _get_subs_id(sjson_transcript.name)

        mock_get_video_transcript_content.return_value = {
            'content': json.dumps({
                "start": [10],
                "end": [100],
                "text": ["Hi, welcome to Edx."],
            }),
            'file_name': 'edx.sjson'
        }
        mock_get_transcript_languages.return_value = val_transcripts
        self.item.transcripts = transcripts
        self.item.sub = sub
        self.item.edx_video_id = 'an-edx-video-id'
        # Make request to available translations dispatch.
        request = Request.blank('/available_translations')
        response = self.item.transcript(request=request, dispatch='available_translations')
        six.assertCountEqual(self, json.loads(response.body.decode('utf-8')), result)

    @patch('xmodule.video_module.transcripts_utils.edxval_api.get_available_transcript_languages')
    def test_val_available_translations_feature_disabled(self, mock_get_available_transcript_languages):
        """
        Tests available translations with val transcript languages when feature is disabled.
        """
        mock_get_available_transcript_languages.return_value = ['en', 'de', 'ro']
        request = Request.blank('/available_translations')
        response = self.item.transcript(request=request, dispatch='available_translations')
        self.assertEqual(response.status_code, 404)


@ddt.ddt
class TestTranscriptAvailableTranslationsBumperDispatch(TestVideo):
    """
    Test video handler that provide available translations info.

    Tests for `available_translations_bumper` dispatch.
    """
    srt_file = _create_srt_file()
    DATA = u"""
        <video show_captions="true"
        display_name="A Name"
        >
            <source src="example.mp4"/>
            <source src="example.webm"/>
            <transcript language="uk" src="{}"/>
        </video>
    """.format(os.path.split(srt_file.name)[1])

    MODEL_DATA = {
        'data': DATA
    }

    def setUp(self):
        super(TestTranscriptAvailableTranslationsBumperDispatch, self).setUp()
        self.item_descriptor.render(STUDENT_VIEW)
        self.item = self.item_descriptor
        self.dispatch = "available_translations/?is_bumper=1"
        self.item.video_bumper = {"transcripts": {"en": ""}}

    @ddt.data("en", "uk")
    def test_available_translation_en_and_non_en(self, lang):
        filename = os.path.split(self.srt_file.name)[1]
        _upload_file(self.srt_file, self.item_descriptor.location, filename)
        self.item.video_bumper["transcripts"][lang] = filename

        request = Request.blank('/' + self.dispatch)
        response = self.item.transcript(request=request, dispatch=self.dispatch)
        self.assertEqual(json.loads(response.body.decode('utf-8')), [lang])

    @patch('xmodule.video_module.transcripts_utils.get_available_transcript_languages')
    def test_multiple_available_translations(self, mock_get_transcript_languages):
        """
        Verify that available translations dispatch works as expected for multiple
        translations and returns both content store and edxval translations.
        """
        # Assuming that edx-val has German translation available for this video component.
        mock_get_transcript_languages.return_value = ['de']
        en_translation = _create_srt_file()
        en_translation_filename = os.path.split(en_translation.name)[1]
        uk_translation_filename = os.path.split(self.srt_file.name)[1]
        # Upload english transcript.
        _upload_file(en_translation, self.item_descriptor.location, en_translation_filename)

        # Upload non-english transcript.
        _upload_file(self.srt_file, self.item_descriptor.location, uk_translation_filename)

        self.item.video_bumper["transcripts"]["en"] = en_translation_filename
        self.item.video_bumper["transcripts"]["uk"] = uk_translation_filename

        request = Request.blank('/' + self.dispatch)
        response = self.item.transcript(request=request, dispatch=self.dispatch)
        # Assert that bumper only get its own translations.
        self.assertEqual(sorted(json.loads(response.body.decode('utf-8'))), sorted(['en', 'uk']))


@ddt.ddt
class TestTranscriptDownloadDispatch(TestVideo):
    """
    Test video handler that provide translation transcripts.

    Tests for `download` dispatch.
    """

    DATA = """
        <video show_captions="true"
        display_name="A Name"
        sub="OEoXaMPEzfM"
        edx_video_id="123"
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
        self.item_descriptor.render(STUDENT_VIEW)
        self.item = self.item_descriptor

    def test_download_transcript_not_exist(self):
        request = Request.blank('/download')
        response = self.item.transcript(request=request, dispatch='download')
        self.assertEqual(response.status, '404 Not Found')

    @patch(
        'xmodule.video_module.video_handlers.get_transcript',
        return_value=('Subs!', 'test_filename.srt', 'application/x-subrip; charset=utf-8')
    )
    def test_download_srt_exist(self, __):
        request = Request.blank('/download')
        response = self.item.transcript(request=request, dispatch='download')
        self.assertEqual(response.body.decode('utf-8'), 'Subs!')
        self.assertEqual(response.headers['Content-Type'], 'application/x-subrip; charset=utf-8')
        self.assertEqual(response.headers['Content-Language'], 'en')

    @patch(
        'xmodule.video_module.video_handlers.get_transcript',
        return_value=('Subs!', 'txt', 'text/plain; charset=utf-8')
    )
    def test_download_txt_exist(self, __):
        self.item.transcript_format = 'txt'
        request = Request.blank('/download')
        response = self.item.transcript(request=request, dispatch='download')
        self.assertEqual(response.body.decode('utf-8'), 'Subs!')
        self.assertEqual(response.headers['Content-Type'], 'text/plain; charset=utf-8')
        self.assertEqual(response.headers['Content-Language'], 'en')

    def test_download_en_no_sub(self):
        request = Request.blank('/download')
        response = self.item.transcript(request=request, dispatch='download')
        self.assertEqual(response.status, '404 Not Found')
        with self.assertRaises(NotFoundError):
            get_transcript(self.item)

    @patch(
        'xmodule.video_module.transcripts_utils.get_transcript_for_video',
        return_value=(Transcript.SRT, u"塞", 'Subs!')
    )
    def test_download_non_en_non_ascii_filename(self, __):
        request = Request.blank('/download')
        response = self.item.transcript(request=request, dispatch='download')
        self.assertEqual(response.body.decode('utf-8'), 'Subs!')
        self.assertEqual(response.headers['Content-Type'], 'application/x-subrip; charset=utf-8')
        self.assertEqual(response.headers['Content-Disposition'], 'attachment; filename="en_塞.srt"')

    @patch('xmodule.video_module.transcripts_utils.edxval_api.get_video_transcript_data')
    @patch('xmodule.video_module.get_transcript', Mock(side_effect=NotFoundError))
    def test_download_fallback_transcript(self, mock_get_video_transcript_data):
        """
        Verify val transcript is returned as a fallback if it is not found in the content store.
        """
        mock_get_video_transcript_data.return_value = {
            'content': json.dumps({
                "start": [10],
                "end": [100],
                "text": ["Hi, welcome to Edx."],
            }),
            'file_name': 'edx.sjson'
        }

        # Make request to XModule transcript handler
        request = Request.blank('/download')
        response = self.item.transcript(request=request, dispatch='download')

        # Expected response
        expected_content = u'0\n00:00:00,010 --> 00:00:00,100\nHi, welcome to Edx.\n\n'
        expected_headers = {
            'Content-Disposition': 'attachment; filename="edx.srt"',
            'Content-Language': u'en',
            'Content-Type': 'application/x-subrip; charset=utf-8'
        }

        # Assert the actual response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, expected_content)
        for attribute, value in six.iteritems(expected_headers):
            self.assertEqual(response.headers[attribute], value)


@ddt.ddt
class TestTranscriptTranslationGetDispatch(TestVideo):
    """
    Test video handler that provide translation transcripts.

    Tests for `translation` and `translation_bumper` dispatches.
    """

    srt_file = _create_srt_file()
    DATA = u"""
        <video
            show_captions="true"
            display_name="A Name"
            edx_video_id="123"
        >
            <source src="example.mp4"/>
            <source src="example.webm"/>
            <transcript language="uk" src="{}"/>
        </video>
    """.format(os.path.split(srt_file.name)[1])

    MODEL_DATA = {
        'data': DATA
    }

    def setUp(self):
        super(TestTranscriptTranslationGetDispatch, self).setUp()
        self.item_descriptor.render(STUDENT_VIEW)
        self.item = self.item_descriptor
        self.item.video_bumper = {"transcripts": {"en": ""}}

    @ddt.data(
        # No language
        ('/translation', 'translation', '400 Bad Request'),
        # No videoId - HTML5 video with language that is not in available languages
        ('/translation/ru', 'translation/ru', '404 Not Found'),
        # Language is not in available languages
        ('/translation/ru?videoId=12345', 'translation/ru', '404 Not Found'),
        # Youtube_id is invalid or does not exist
        ('/translation/uk?videoId=9855256955511225', 'translation/uk', '404 Not Found'),
        ('/translation?is_bumper=1', 'translation', '400 Bad Request'),
        ('/translation/ru?is_bumper=1', 'translation/ru', '404 Not Found'),
        ('/translation/ru?videoId=12345&is_bumper=1', 'translation/ru', '404 Not Found'),
        ('/translation/uk?videoId=9855256955511225&is_bumper=1', 'translation/uk', '404 Not Found'),
    )
    @ddt.unpack
    def test_translation_fails(self, url, dispatch, status_code):
        request = Request.blank(url)
        response = self.item.transcript(request=request, dispatch=dispatch)
        self.assertEqual(response.status, status_code)

    @ddt.data(
        ('translation/en?videoId={}', 'translation/en', attach_sub),
        ('translation/en?videoId={}&is_bumper=1', 'translation/en', attach_bumper_transcript))
    @ddt.unpack
    def test_translaton_en_youtube_success(self, url, dispatch, attach):
        subs = {"start": [10], "end": [100], "text": ["Hi, welcome to Edx."]}
        good_sjson = _create_file(json.dumps(subs))
        _upload_sjson_file(good_sjson, self.item_descriptor.location)
        subs_id = _get_subs_id(good_sjson.name)

        attach(self.item, subs_id)
        request = Request.blank(url.format(subs_id))
        response = self.item.transcript(request=request, dispatch=dispatch)
        self.assertDictEqual(json.loads(response.body.decode('utf-8')), subs)

    def test_translation_non_en_youtube_success(self):
        subs = {
            u'end': [100],
            u'start': [12],
            u'text': [
                u'\u041f\u0440\u0438\u0432\u0456\u0442, edX \u0432\u0456\u0442\u0430\u0454 \u0432\u0430\u0441.'
            ]
        }
        self.srt_file.seek(0)
        _upload_file(self.srt_file, self.item_descriptor.location, os.path.split(self.srt_file.name)[1])
        subs_id = _get_subs_id(self.srt_file.name)

        # youtube 1_0 request, will generate for all speeds for existing ids
        self.item.youtube_id_1_0 = subs_id
        self.item.youtube_id_0_75 = '0_75'
        self.store.update_item(self.item, self.user.id)
        request = Request.blank('/translation/uk?videoId={}'.format(subs_id))
        response = self.item.transcript(request=request, dispatch='translation/uk')
        self.assertDictEqual(json.loads(response.body.decode('utf-8')), subs)

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

        self.assertDictEqual(json.loads(response.body.decode('utf-8')), calculated_0_75)
        # 1_5 will be generated from 1_0
        self.item.youtube_id_1_5 = '1_5'
        self.store.update_item(self.item, self.user.id)
        request = Request.blank('/translation/uk?videoId={}'.format('1_5'))
        response = self.item.transcript(request=request, dispatch='translation/uk')
        calculated_1_5 = {
            u'end': [150],
            u'start': [18],
            u'text': [
                u'\u041f\u0440\u0438\u0432\u0456\u0442, edX \u0432\u0456\u0442\u0430\u0454 \u0432\u0430\u0441.'
            ]
        }
        self.assertDictEqual(json.loads(response.body.decode('utf-8')), calculated_1_5)

    @ddt.data(
        ('translation/en', 'translation/en', attach_sub),
        ('translation/en?is_bumper=1', 'translation/en', attach_bumper_transcript))
    @ddt.unpack
    def test_translaton_en_html5_success(self, url, dispatch, attach):
        good_sjson = _create_file(json.dumps(TRANSCRIPT))
        _upload_sjson_file(good_sjson, self.item_descriptor.location)
        subs_id = _get_subs_id(good_sjson.name)

        attach(self.item, subs_id)
        self.store.update_item(self.item, self.user.id)
        request = Request.blank(url)
        response = self.item.transcript(request=request, dispatch=dispatch)
        self.assertDictEqual(json.loads(response.body.decode('utf-8')), TRANSCRIPT)

    def test_translaton_non_en_html5_success(self):
        subs = {
            u'end': [100],
            u'start': [12],
            u'text': [
                u'\u041f\u0440\u0438\u0432\u0456\u0442, edX \u0432\u0456\u0442\u0430\u0454 \u0432\u0430\u0441.'
            ]
        }
        self.srt_file.seek(0)
        _upload_file(self.srt_file, self.item_descriptor.location, os.path.split(self.srt_file.name)[1])

        # manually clean youtube_id_1_0, as it has default value
        self.item.youtube_id_1_0 = ""
        request = Request.blank('/translation/uk')
        response = self.item.transcript(request=request, dispatch='translation/uk')
        self.assertDictEqual(json.loads(response.body.decode('utf-8')), subs)

    def test_translation_static_transcript_xml_with_data_dirc(self):
        """
        Test id data_dir is set in XML course.

        Set course data_dir and ensure we get redirected to that path
        if it isn't found in the contentstore.
        """
        # Simulate data_dir set in course.
        test_modulestore = MagicMock()
        attrs = {'get_course.return_value': Mock(data_dir='dummy/static', static_asset_path='')}
        test_modulestore.configure_mock(**attrs)
        self.item_descriptor.runtime.modulestore = test_modulestore

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

    @ddt.data(
        # Test youtube style en
        ('/translation/en?videoId=12345', 'translation/en', '307 Temporary Redirect', '12345'),
        # Test html5 style en
        ('/translation/en', 'translation/en', '307 Temporary Redirect', 'OEoXaMPEzfM', attach_sub),
        # Test different language to ensure we are just ignoring it since we can't
        # translate with static fallback
        ('/translation/uk', 'translation/uk', '404 Not Found'),
        (
            '/translation/en?is_bumper=1', 'translation/en', '307 Temporary Redirect', 'OEoXaMPEzfM',
            attach_bumper_transcript
        ),
        ('/translation/uk?is_bumper=1', 'translation/uk', '404 Not Found'),
    )
    @ddt.unpack
    def test_translation_static_transcript(self, url, dispatch, status_code, sub=None, attach=None):
        """
        Set course static_asset_path and ensure we get redirected to that path
        if it isn't found in the contentstore
        """
        self._set_static_asset_path()

        if attach:
            attach(self.item, sub)
        request = Request.blank(url)
        response = self.item.transcript(request=request, dispatch=dispatch)
        self.assertEqual(response.status, status_code)
        if sub:
            self.assertIn(
                ('Location', '/static/dummy/static/subs_{}.srt.sjson'.format(sub)),
                response.headerlist
            )

    @patch('xmodule.video_module.VideoBlock.course_id', return_value='not_a_course_locator')
    def test_translation_static_non_course(self, __):
        """
        Test that get_static_transcript short-circuits in the case of a non-CourseLocator.
        This fixes a bug for videos inside of content libraries.
        """
        self._set_static_asset_path()

        # When course_id is not mocked out, these values would result in 307, as tested above.
        request = Request.blank('/translation/en?videoId=12345')
        response = self.item.transcript(request=request, dispatch='translation/en')
        self.assertEqual(response.status, '404 Not Found')

    def _set_static_asset_path(self):
        """ Helper method for setting up the static_asset_path information """
        self.course.static_asset_path = 'dummy/static'
        self.course.save()
        store = modulestore()
        with store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, self.course.id):
            store.update_item(self.course, self.user.id)

    @patch('xmodule.video_module.transcripts_utils.edxval_api.get_video_transcript_data')
    @patch('xmodule.video_module.VideoBlock.translation', Mock(side_effect=NotFoundError))
    @patch('xmodule.video_module.VideoBlock.get_static_transcript', Mock(return_value=Response(status=404)))
    def test_translation_fallback_transcript(self, mock_get_video_transcript_data):
        """
        Verify that the val transcript is returned as a fallback,
        if it is not found in the content store.
        """
        transcript = {
            'content': json.dumps({
                "start": [10],
                "end": [100],
                "text": ["Hi, welcome to Edx."],
            }),
            'file_name': 'edx.sjson'
        }
        mock_get_video_transcript_data.return_value = transcript

        # Make request to XModule transcript handler
        response = self.item.transcript(request=Request.blank('/translation/en'), dispatch='translation/en')

        # Expected headers
        expected_headers = {
            'Content-Language': 'en',
            'Content-Type': 'application/json'
        }

        # Assert the actual response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, transcript['content'])
        for attribute, value in six.iteritems(expected_headers):
            self.assertEqual(response.headers[attribute], value)

    @patch('xmodule.video_module.VideoBlock.translation', Mock(side_effect=NotFoundError))
    @patch('xmodule.video_module.VideoBlock.get_static_transcript', Mock(return_value=Response(status=404)))
    def test_translation_fallback_transcript_feature_disabled(self):
        """
        Verify that val transcript is not returned when its feature is disabled.
        """
        # Make request to XModule transcript handler
        response = self.item.transcript(request=Request.blank('/translation/en'), dispatch='translation/en')
        # Assert the actual response
        self.assertEqual(response.status_code, 404)


class TestStudioTranscriptTranslationGetDispatch(TestVideo):
    """
    Test Studio video handler that provide translation transcripts.

    Tests for `translation` dispatch GET HTTP method.
    """
    srt_file = _create_srt_file()
    DATA = u"""
        <video show_captions="true"
        display_name="A Name"
        >
            <source src="example.mp4"/>
            <source src="example.webm"/>
            <transcript language="uk" src="{}"/>
            <transcript language="zh" src="{}"/>
        </video>
    """.format(os.path.split(srt_file.name)[1], u"塞.srt")

    MODEL_DATA = {'data': DATA}

    def test_translation_fails(self):
        # No language
        request = Request.blank("")
        response = self.item_descriptor.studio_transcript(request=request, dispatch="translation")
        self.assertEqual(response.status, "400 Bad Request")

        # No language_code param in request.GET
        request = Request.blank("")
        response = self.item_descriptor.studio_transcript(request=request, dispatch="translation")
        self.assertEqual(response.status, "400 Bad Request")
        self.assertEqual(response.json["error"], "Language is required.")

        # Correct case:
        filename = os.path.split(self.srt_file.name)[1]
        _upload_file(self.srt_file, self.item_descriptor.location, filename)
        request = Request.blank(u"translation?language_code=uk")
        response = self.item_descriptor.studio_transcript(request=request, dispatch="translation?language_code=uk")
        self.srt_file.seek(0)
        self.assertEqual(response.body, self.srt_file.read())
        self.assertEqual(response.headers["Content-Type"], "application/x-subrip; charset=utf-8")
        self.assertEqual(
            response.headers["Content-Disposition"],
            u'attachment; filename="uk_{}"'.format(filename)
        )
        self.assertEqual(response.headers["Content-Language"], "uk")

        # Non ascii file name download:
        self.srt_file.seek(0)
        _upload_file(self.srt_file, self.item_descriptor.location, u"塞.srt")
        request = Request.blank("translation?language_code=zh")
        response = self.item_descriptor.studio_transcript(request=request, dispatch="translation?language_code=zh")
        self.srt_file.seek(0)
        self.assertEqual(response.body, self.srt_file.read())
        self.assertEqual(response.headers["Content-Type"], "application/x-subrip; charset=utf-8")
        self.assertEqual(response.headers["Content-Disposition"], 'attachment; filename="zh_塞.srt"')
        self.assertEqual(response.headers["Content-Language"], "zh")


@ddt.ddt
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

    @ddt.data(
        {
            "post_data": {},
            "error_message": "The following parameters are required: edx_video_id, language_code, new_language_code."
        },
        {
            "post_data": {"edx_video_id": "111", "language_code": "ar", "new_language_code": "ur"},
            "error_message": 'A transcript with the "ur" language code already exists.'
        },
        {
            "post_data": {"edx_video_id": "111", "language_code": "ur", "new_language_code": "ur"},
            "error_message": "A transcript file is required."
        },
    )
    @ddt.unpack
    def test_studio_transcript_post_validations(self, post_data, error_message):
        """
        Verify that POST request validations works as expected.
        """
        # mock available_translations method
        self.item_descriptor.available_translations = lambda transcripts, verify_assets: ['ur']
        request = Request.blank('/translation', POST=post_data)
        response = self.item_descriptor.studio_transcript(request=request, dispatch='translation')
        self.assertEqual(response.json["error"], error_message)

    @ddt.data(
        {
            "edx_video_id": "",
        },
        {
            "edx_video_id": "1234-5678-90",
        },
    )
    @ddt.unpack
    def test_studio_transcript_post_w_no_edx_video_id(self, edx_video_id):
        """
        Verify that POST request works as expected
        """
        post_data = {
            "edx_video_id": edx_video_id,
            "language_code": "ar",
            "new_language_code": "uk",
            "file": ("filename.srt", SRT_content)
        }

        if edx_video_id:
            edxval_api.create_video({
                "edx_video_id": edx_video_id,
                "status": "uploaded",
                "client_video_id": "a video",
                "duration": 0,
                "encoded_videos": [],
                "courses": []
            })

        request = Request.blank('/translation', POST=post_data)
        response = self.item_descriptor.studio_transcript(request=request, dispatch='translation')
        self.assertEqual(response.status, '201 Created')
        response = json.loads(response.text)
        self.assertTrue(response["language_code"], "uk")
        self.assertDictEqual(self.item_descriptor.transcripts, {})
        self.assertTrue(edxval_api.get_video_transcript_data(video_id=response["edx_video_id"], language_code="uk"))

    def test_studio_transcript_post_bad_content(self):
        """
        Verify that transcript content encode/decode errors handled as expected
        """
        post_data = {
            "edx_video_id": "",
            "language_code": "ar",
            "new_language_code": "uk",
            "file": ("filename.srt", SRT_content.encode("cp1251"))
        }

        request = Request.blank("/translation", POST=post_data)
        response = self.item_descriptor.studio_transcript(request=request, dispatch="translation")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json["error"],
            "There is a problem with this transcript file. Try to upload a different file."
        )


@ddt.ddt
class TestStudioTranscriptTranslationDeleteDispatch(TestVideo):
    """
    Test studio video handler that provide translation transcripts.

    Tests for `translation` dispatch DELETE HTTP method.
    """
    EDX_VIDEO_ID, LANGUAGE_CODE_UK, LANGUAGE_CODE_EN = u'an_edx_video_id', u'uk', u'en'
    REQUEST_META = {'wsgi.url_scheme': 'http', 'REQUEST_METHOD': 'DELETE'}
    SRT_FILE = _create_srt_file()

    @ddt.data(
        {
            'params': {'lang': 'uk'}
        },
        {
            'params': {'edx_video_id': '12345'}
        },
        {
            'params': {}
        },
    )
    @ddt.unpack
    def test_translation_missing_required_params(self, params):
        """
        Verify that DELETE dispatch works as expected when required args are missing from request
        """
        request = Request(self.REQUEST_META, body=json.dumps(params).encode('utf-8'))
        response = self.item_descriptor.studio_transcript(request=request, dispatch='translation')
        self.assertEqual(response.status_code, 400)

    def test_translation_delete_w_edx_video_id(self):
        """
        Verify that DELETE dispatch works as expected when video has edx_video_id
        """
        request_body = json.dumps({'lang': self.LANGUAGE_CODE_UK, 'edx_video_id': self.EDX_VIDEO_ID})
        api.create_video({
            'edx_video_id': self.EDX_VIDEO_ID,
            'status': 'upload',
            'client_video_id': 'awesome.mp4',
            'duration': 0,
            'encoded_videos': [],
            'courses': [six.text_type(self.course.id)]
        })
        api.create_video_transcript(
            video_id=self.EDX_VIDEO_ID,
            language_code=self.LANGUAGE_CODE_UK,
            file_format='srt',
            content=ContentFile(SRT_content)
        )

        # verify that a video transcript exists for expected data
        self.assertTrue(api.get_video_transcript_data(video_id=self.EDX_VIDEO_ID, language_code=self.LANGUAGE_CODE_UK))

        request = Request(self.REQUEST_META, body=request_body.encode('utf-8'))
        self.item_descriptor.edx_video_id = self.EDX_VIDEO_ID
        response = self.item_descriptor.studio_transcript(request=request, dispatch='translation')
        self.assertEqual(response.status_code, 200)

        # verify that a video transcript dose not exist for expected data
        self.assertFalse(api.get_video_transcript_data(video_id=self.EDX_VIDEO_ID, language_code=self.LANGUAGE_CODE_UK))

    def test_translation_delete_wo_edx_video_id(self):
        """
        Verify that DELETE dispatch works as expected when video has no edx_video_id
        """
        request_body = json.dumps({'lang': self.LANGUAGE_CODE_UK, 'edx_video_id': ''})
        srt_file_name_uk = subs_filename('ukrainian_translation.srt', lang=self.LANGUAGE_CODE_UK)
        request = Request(self.REQUEST_META, body=request_body.encode('utf-8'))

        # upload and verify that srt file exists in assets
        _upload_file(self.SRT_FILE, self.item_descriptor.location, srt_file_name_uk)
        self.assertTrue(_check_asset(self.item_descriptor.location, srt_file_name_uk))

        # verify transcripts field
        self.assertNotEqual(self.item_descriptor.transcripts, {})
        self.assertTrue(self.LANGUAGE_CODE_UK in self.item_descriptor.transcripts)

        # make request and verify response
        response = self.item_descriptor.studio_transcript(request=request, dispatch='translation')
        self.assertEqual(response.status_code, 200)

        # verify that srt file is deleted
        self.assertEqual(self.item_descriptor.transcripts, {})
        self.assertFalse(_check_asset(self.item_descriptor.location, srt_file_name_uk))

    def test_translation_delete_w_english_lang(self):
        """
        Verify that DELETE dispatch works as expected for english language translation
        """
        request_body = json.dumps({'lang': self.LANGUAGE_CODE_EN, 'edx_video_id': ''})
        srt_file_name_en = subs_filename('english_translation.srt', lang=self.LANGUAGE_CODE_EN)
        self.item_descriptor.transcripts['en'] = 'english_translation.srt'
        request = Request(self.REQUEST_META, body=request_body.encode('utf-8'))

        # upload and verify that srt file exists in assets
        _upload_file(self.SRT_FILE, self.item_descriptor.location, srt_file_name_en)
        self.assertTrue(_check_asset(self.item_descriptor.location, srt_file_name_en))

        # make request and verify response
        response = self.item_descriptor.studio_transcript(request=request, dispatch='translation')
        self.assertEqual(response.status_code, 200)

        # verify that srt file is deleted
        self.assertTrue(self.LANGUAGE_CODE_EN not in self.item_descriptor.transcripts)
        self.assertFalse(_check_asset(self.item_descriptor.location, srt_file_name_en))

    def test_translation_delete_w_sub(self):
        """
        Verify that DELETE dispatch works as expected when translation is present against `sub` field
        """
        request_body = json.dumps({'lang': self.LANGUAGE_CODE_EN, 'edx_video_id': ''})
        sub_file_name = subs_filename(self.item_descriptor.sub, lang=self.LANGUAGE_CODE_EN)
        request = Request(self.REQUEST_META, body=request_body.encode('utf-8'))

        # sub should not be empy
        self.assertFalse(self.item_descriptor.sub == u'')

        # upload and verify that srt file exists in assets
        _upload_file(self.SRT_FILE, self.item_descriptor.location, sub_file_name)
        self.assertTrue(_check_asset(self.item_descriptor.location, sub_file_name))

        # make request and verify response
        response = self.item_descriptor.studio_transcript(request=request, dispatch='translation')
        self.assertEqual(response.status_code, 200)

        # verify that sub is empty and transcript is deleted also
        self.assertTrue(self.item_descriptor.sub == u'')
        self.assertFalse(_check_asset(self.item_descriptor.location, sub_file_name))


class TestGetTranscript(TestVideo):
    """
    Make sure that `get_transcript` method works correctly
    """
    srt_file = _create_srt_file()
    DATA = u"""
        <video show_captions="true"
        display_name="A Name"
        >
            <source src="example.mp4"/>
            <source src="example.webm"/>
            <transcript language="uk" src="{}"/>
            <transcript language="zh" src="{}"/>
        </video>
    """.format(os.path.split(srt_file.name)[1], u"塞.srt")

    MODEL_DATA = {
        'data': DATA
    }
    METADATA = {}

    def setUp(self):
        super(TestGetTranscript, self).setUp()
        self.item_descriptor.render(STUDENT_VIEW)
        self.item = self.item_descriptor

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

        text, filename, mime_type = get_transcript(self.item)

        expected_text = textwrap.dedent("""\
            0
            00:00:00,270 --> 00:00:02,720
            Hi, welcome to Edx.

            1
            00:00:02,720 --> 00:00:05,430
            Let&#39;s start with what is on your screen right now.

            """)

        self.assertEqual(text, expected_text)
        self.assertEqual(filename[:-4], 'en_' + self.item.sub)
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
        text, filename, mime_type = get_transcript(self.item, output_format=Transcript.TXT)
        expected_text = textwrap.dedent("""\
            Hi, welcome to Edx.
            Let's start with what is on your screen right now.""")

        self.assertEqual(text, expected_text)
        self.assertEqual(filename, 'en_' + self.item.sub + '.txt')
        self.assertEqual(mime_type, 'text/plain; charset=utf-8')

    def test_en_with_empty_sub(self):

        self.item.sub = ""
        self.item.transcripts = None
        # no self.sub, self.youttube_1_0 exist, but no file in assets
        with self.assertRaises(NotFoundError):
            get_transcript(self.item)

        # no self.sub and no self.youtube_1_0, no non-en transcritps
        self.item.youtube_id_1_0 = None
        with self.assertRaises(NotFoundError):
            get_transcript(self.item)

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

        text, filename, mime_type = get_transcript(self.item)
        expected_text = textwrap.dedent("""\
            0
            00:00:00,270 --> 00:00:02,720
            Hi, welcome to Edx.

            1
            00:00:02,720 --> 00:00:05,430
            Let&#39;s start with what is on your screen right now.

            """)

        self.assertEqual(text, expected_text)
        self.assertEqual(filename, 'en_' + self.item.youtube_id_1_0 + '.srt')
        self.assertEqual(mime_type, 'application/x-subrip; charset=utf-8')

    def test_non_en_with_non_ascii_filename(self):
        self.item.transcript_language = 'zh'
        self.srt_file.seek(0)
        _upload_file(self.srt_file, self.item_descriptor.location, u"塞.srt")

        transcripts = self.item.get_transcripts_info()
        text, filename, mime_type = get_transcript(self.item)
        expected_text = textwrap.dedent(u"""
        0
        00:00:00,12 --> 00:00:00,100
        Привіт, edX вітає вас.
        """)
        self.assertEqual(text, expected_text)
        self.assertEqual(filename, u"zh_塞.srt")
        self.assertEqual(mime_type, 'application/x-subrip; charset=utf-8')

    def test_value_error(self):
        good_sjson = _create_file(content='bad content')

        _upload_sjson_file(good_sjson, self.item.location)
        self.item.sub = _get_subs_id(good_sjson.name)

        transcripts = self.item.get_transcripts_info()
        with self.assertRaises(ValueError):
            get_transcript(self.item)

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

        transcripts = self.item.get_transcripts_info()
        with self.assertRaises(KeyError):
            get_transcript(self.item)
