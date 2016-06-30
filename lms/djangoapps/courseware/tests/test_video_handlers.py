# -*- coding: utf-8 -*-
"""Video xmodule tests in mongo."""

import os
import freezegun
import tempfile
import textwrap
import json
import ddt

from nose.plugins.attrib import attr
from datetime import timedelta, datetime
from webob import Request
from mock import MagicMock, Mock, patch

from xmodule.contentstore.content import StaticContent
from xmodule.contentstore.django import contentstore
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import ModuleStoreEnum
from xmodule.x_module import STUDENT_VIEW
from . import BaseTestXmodule
from .test_video_xml import SOURCE_XML
from contentserver.caching import del_cached_content
from xmodule.exceptions import NotFoundError

from xmodule.video_module.transcripts_utils import (
    TranscriptException,
    TranscriptsGenerationException,
)


TRANSCRIPT = {"start": [10], "end": [100], "text": ["Hi, welcome to Edx."]}
BUMPER_TRANSCRIPT = {"start": [1], "end": [10], "text": ["A bumper"]}
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


def attach_sub(item, filename):
    """
    Attach `en` transcript.
    """
    item.sub = filename


def attach_bumper_transcript(item, filename, lang="en"):
    """
    Attach bumper transcript.
    """
    item.video_bumper["transcripts"][lang] = filename


@attr('shard_1')
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

        status_codes = {response.status_code for response in responses.values()}
        self.assertEqual(status_codes.pop(), 404)

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

        with freezegun.freeze_time(datetime.now()):
            self.assertEqual(self.item_descriptor.bumper_last_view_date, None)
            self.item_descriptor.handle_ajax('save_user_state', {'bumper_last_view_date': True})
            self.assertEqual(self.item_descriptor.bumper_last_view_date, datetime.utcnow())

        response = self.item_descriptor.handle_ajax('save_user_state', {u'demoo�': "sample"})
        self.assertEqual(json.loads(response)['success'], True)

    def tearDown(self):
        _clear_assets(self.item_descriptor.location)
        super(TestVideo, self).tearDown()


@attr('shard_1')
class TestTranscriptAvailableTranslationsDispatch(TestVideo):
    """
    Test video handler that provide available translations info.

    Tests for `available_translations` dispatch.
    """
    srt_file = _create_srt_file()
    DATA = """
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
        _upload_file(self.srt_file, self.item_descriptor.location, os.path.split(self.srt_file.name)[1])

        request = Request.blank('/available_translations')
        response = self.item.transcript(request=request, dispatch='available_translations')
        self.assertEqual(json.loads(response.body), ['uk'])

    def test_multiple_available_translations(self):
        good_sjson = _create_file(json.dumps(self.subs))

        # Upload english transcript.
        _upload_sjson_file(good_sjson, self.item_descriptor.location)

        # Upload non-english transcript.
        _upload_file(self.srt_file, self.item_descriptor.location, os.path.split(self.srt_file.name)[1])

        self.item.sub = _get_subs_id(good_sjson.name)

        request = Request.blank('/available_translations')
        response = self.item.transcript(request=request, dispatch='available_translations')
        self.assertEqual(json.loads(response.body), ['en', 'uk'])


@attr('shard_1')
@ddt.ddt
class TestTranscriptAvailableTranslationsBumperDispatch(TestVideo):
    """
    Test video handler that provide available translations info.

    Tests for `available_translations_bumper` dispatch.
    """
    srt_file = _create_srt_file()
    DATA = """
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
        self.item = self.item_descriptor.xmodule_runtime.xmodule_instance
        self.dispatch = "available_translations/?is_bumper=1"
        self.item.video_bumper = {"transcripts": {"en": ""}}

    @ddt.data("en", "uk")
    def test_available_translation_en_and_non_en(self, lang):
        filename = os.path.split(self.srt_file.name)[1]
        _upload_file(self.srt_file, self.item_descriptor.location, filename)
        self.item.video_bumper["transcripts"][lang] = filename

        request = Request.blank('/' + self.dispatch)
        response = self.item.transcript(request=request, dispatch=self.dispatch)
        self.assertEqual(json.loads(response.body), [lang])

    def test_multiple_available_translations(self):
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
        self.item_descriptor.render(STUDENT_VIEW)
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
        transcripts = self.item.get_transcripts_info()
        with self.assertRaises(NotFoundError):
            self.item.get_transcript(transcripts)

    @patch('xmodule.video_module.VideoModule.get_transcript', return_value=('Subs!', u"塞.srt", 'application/x-subrip; charset=utf-8'))
    def test_download_non_en_non_ascii_filename(self, __):
        request = Request.blank('/download')
        response = self.item.transcript(request=request, dispatch='download')
        self.assertEqual(response.body, 'Subs!')
        self.assertEqual(response.headers['Content-Type'], 'application/x-subrip; charset=utf-8')
        self.assertEqual(response.headers['Content-Disposition'], 'attachment; filename="塞.srt"')


@attr('shard_1')
@ddt.ddt
class TestTranscriptTranslationGetDispatch(TestVideo):
    """
    Test video handler that provide translation transcripts.

    Tests for `translation` and `translation_bumper` dispatches.
    """

    srt_file = _create_srt_file()
    DATA = """
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
        super(TestTranscriptTranslationGetDispatch, self).setUp()
        self.item_descriptor.render(STUDENT_VIEW)
        self.item = self.item_descriptor.xmodule_runtime.xmodule_instance
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
        self.assertDictEqual(json.loads(response.body), subs)

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

    @ddt.data(
        ('translation/en', 'translation/en', attach_sub),
        ('translation/en?is_bumper=1', 'translation/en', attach_bumper_transcript))
    @ddt.unpack
    def test_translaton_en_html5_success(self, url, dispatch, attach):
        good_sjson = _create_file(json.dumps(TRANSCRIPT))
        _upload_sjson_file(good_sjson, self.item_descriptor.location)
        subs_id = _get_subs_id(good_sjson.name)

        attach(self.item, subs_id)
        request = Request.blank(url)
        response = self.item.transcript(request=request, dispatch=dispatch)
        self.assertDictEqual(json.loads(response.body), TRANSCRIPT)

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
        self.assertDictEqual(json.loads(response.body), subs)

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

    @patch('xmodule.video_module.VideoModule.course_id', return_value='not_a_course_locator')
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


@attr('shard_1')
class TestStudioTranscriptTranslationGetDispatch(TestVideo):
    """
    Test Studio video handler that provide translation transcripts.

    Tests for `translation` dispatch GET HTTP method.
    """
    srt_file = _create_srt_file()
    DATA = """
        <video show_captions="true"
        display_name="A Name"
        >
            <source src="example.mp4"/>
            <source src="example.webm"/>
            <transcript language="uk" src="{}"/>
            <transcript language="zh" src="{}"/>
        </video>
    """.format(os.path.split(srt_file.name)[1], u"塞.srt".encode('utf8'))

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
        filename = os.path.split(self.srt_file.name)[1]
        _upload_file(self.srt_file, self.item_descriptor.location, filename)
        self.srt_file.seek(0)
        request = Request.blank(u'translation/uk?filename={}'.format(filename))
        response = self.item_descriptor.studio_transcript(request=request, dispatch='translation/uk')
        self.assertEqual(response.body, self.srt_file.read())
        self.assertEqual(response.headers['Content-Type'], 'application/x-subrip; charset=utf-8')
        self.assertEqual(
            response.headers['Content-Disposition'],
            'attachment; filename="{}"'.format(filename)
        )
        self.assertEqual(response.headers['Content-Language'], 'uk')

        # Non ascii file name download:
        self.srt_file.seek(0)
        _upload_file(self.srt_file, self.item_descriptor.location, u'塞.srt')
        self.srt_file.seek(0)
        request = Request.blank('translation/zh?filename={}'.format(u'塞.srt'.encode('utf8')))
        response = self.item_descriptor.studio_transcript(request=request, dispatch='translation/zh')
        self.assertEqual(response.body, self.srt_file.read())
        self.assertEqual(response.headers['Content-Type'], 'application/x-subrip; charset=utf-8')
        self.assertEqual(response.headers['Content-Disposition'], 'attachment; filename="塞.srt"')
        self.assertEqual(response.headers['Content-Language'], 'zh')


@attr('shard_1')
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
        # Non-UTF8 file content encoding.
        response = self.item_descriptor.studio_transcript(request=request, dispatch='translation/uk')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.body, "Invalid encoding type, transcripts should be UTF-8 encoded.")

        # No language is passed.
        request = Request.blank('/translation', POST={'file': ('filename', SRT_content)})
        response = self.item_descriptor.studio_transcript(request=request, dispatch='translation')
        self.assertEqual(response.status, '400 Bad Request')

        # Language, good filename and good content.
        request = Request.blank('/translation/uk', POST={'file': ('filename.srt', SRT_content)})
        response = self.item_descriptor.studio_transcript(request=request, dispatch='translation/uk')
        self.assertEqual(response.status, '201 Created')
        self.assertDictEqual(json.loads(response.body), {'filename': u'filename.srt', 'status': 'Success'})
        self.assertDictEqual(self.item_descriptor.transcripts, {})
        self.assertTrue(_check_asset(self.item_descriptor.location, u'filename.srt'))


@attr('shard_1')
class TestGetTranscript(TestVideo):
    """
    Make sure that `get_transcript` method works correctly
    """
    srt_file = _create_srt_file()
    DATA = """
        <video show_captions="true"
        display_name="A Name"
        >
            <source src="example.mp4"/>
            <source src="example.webm"/>
            <transcript language="uk" src="{}"/>
            <transcript language="zh" src="{}"/>
        </video>
    """.format(os.path.split(srt_file.name)[1], u"塞.srt".encode('utf8'))

    MODEL_DATA = {
        'data': DATA
    }
    METADATA = {}

    def setUp(self):
        super(TestGetTranscript, self).setUp()
        self.item_descriptor.render(STUDENT_VIEW)
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

        transcripts = self.item.get_transcripts_info()
        text, filename, mime_type = self.item.get_transcript(transcripts)

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
        transcripts = self.item.get_transcripts_info()
        text, filename, mime_type = self.item.get_transcript(transcripts, transcript_format="txt")
        expected_text = textwrap.dedent("""\
            Hi, welcome to Edx.
            Let's start with what is on your screen right now.""")

        self.assertEqual(text, expected_text)
        self.assertEqual(filename, self.item.sub + '.txt')
        self.assertEqual(mime_type, 'text/plain; charset=utf-8')

    def test_en_with_empty_sub(self):

        transcripts = {"transcripts": {}, "sub": ""}
        # no self.sub, self.youttube_1_0 exist, but no file in assets
        with self.assertRaises(NotFoundError):
            self.item.get_transcript(transcripts)

        # no self.sub and no self.youtube_1_0, no non-en transcritps
        self.item.youtube_id_1_0 = None
        with self.assertRaises(ValueError):
            self.item.get_transcript(transcripts)

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

        text, filename, mime_type = self.item.get_transcript(transcripts)
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
        self.srt_file.seek(0)
        _upload_file(self.srt_file, self.item_descriptor.location, u"塞.srt")

        transcripts = self.item.get_transcripts_info()
        text, filename, mime_type = self.item.get_transcript(transcripts)
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

        transcripts = self.item.get_transcripts_info()
        with self.assertRaises(ValueError):
            self.item.get_transcript(transcripts)

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
            self.item.get_transcript(transcripts)
