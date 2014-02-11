# -*- coding: utf-8 -*-
"""Video xmodule tests in mongo."""

from mock import patch, PropertyMock
import os
import tempfile
import textwrap
import unittest
from functools import partial

from xmodule.contentstore.content import StaticContent
from xmodule.modulestore import Location
from xmodule.contentstore.django import contentstore
from . import BaseTestXmodule
from .test_video_xml import SOURCE_XML
from django.conf import settings
from xmodule.video_module import _create_youtube_string
from cache_toolbox.core import del_cached_content
from xmodule.exceptions import NotFoundError

class TestVideo(BaseTestXmodule):
    """Integration tests: web client + mongo."""

    CATEGORY = "video"
    DATA = SOURCE_XML
    METADATA = {}

    def test_handle_ajax_dispatch(self):
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

    def tearDown(self):
        _clear_assets(self.item_module.location)


class TestVideoYouTube(TestVideo):
    METADATA = {}

    def test_video_constructor(self):
        """Make sure that all parameters extracted correctly from xml"""
        context = self.item_module.render('student_view').content

        sources = {
            'main': u'example.mp4',
            u'mp4': u'example.mp4',
            u'webm': u'example.webm',
        }

        expected_context = {
            'ajax_url': self.item_descriptor.xmodule_runtime.ajax_url + '/save_user_state',
            'data_dir': getattr(self, 'data_dir', None),
            'caption_asset_path': '/static/subs/',
            'show_captions': 'true',
            'display_name': u'A Name',
            'end': 3610.0,
            'id': self.item_module.location.html_id(),
            'sources': sources,
            'speed': 'null',
            'general_speed': 1.0,
            'start': 3603.0,
            'sub': u'a_sub_file.srt.sjson',
            'track': '',
            'youtube_streams': _create_youtube_string(self.item_module),
            'autoplay': settings.FEATURES.get('AUTOPLAY_VIDEOS', False),
            'yt_test_timeout': 1500,
            'yt_test_url': 'https://gdata.youtube.com/feeds/api/videos/',
        }

        self.assertEqual(
            context,
            self.item_module.xmodule_runtime.render_template('video.html', expected_context),
        )


class TestVideoNonYouTube(TestVideo):
    """Integration tests: web client + mongo."""
    DATA = """
        <video show_captions="true"
        display_name="A Name"
        sub="a_sub_file.srt.sjson"
        download_video="true"
        start_time="01:00:03" end_time="01:00:10"
        >
            <source src="example.mp4"/>
            <source src="example.webm"/>
        </video>
    """
    MODEL_DATA = {
        'data': DATA,
    }
    METADATA = {}

    def test_video_constructor(self):
        """Make sure that if the 'youtube' attribute is omitted in XML, then
            the template generates an empty string for the YouTube streams.
        """
        sources = {
            'main': u'example.mp4',
            u'mp4': u'example.mp4',
            u'webm': u'example.webm',
        }

        context = self.item_module.render('student_view').content
        expected_context = {
            'ajax_url': self.item_descriptor.xmodule_runtime.ajax_url + '/save_user_state',
            'data_dir': getattr(self, 'data_dir', None),
            'caption_asset_path': '/static/subs/',
            'show_captions': 'true',
            'display_name': u'A Name',
            'end': 3610.0,
            'id': self.item_module.location.html_id(),
            'sources': sources,
            'speed': 'null',
            'general_speed': 1.0,
            'start': 3603.0,
            'sub': u'a_sub_file.srt.sjson',
            'track': '',
            'youtube_streams': '1.00:OEoXaMPEzfM',
            'autoplay': settings.FEATURES.get('AUTOPLAY_VIDEOS', True),
            'yt_test_timeout': 1500,
            'yt_test_url': 'https://gdata.youtube.com/feeds/api/videos/',
        }

        self.assertEqual(
            context,
            self.item_module.xmodule_runtime.render_template('video.html', expected_context),
        )


class TestGetHtmlMethod(BaseTestXmodule):
    '''
    Make sure that `get_html` works correctly.
    '''
    CATEGORY = "video"
    DATA = SOURCE_XML
    maxDiff = None
    METADATA = {}

    def setUp(self):
        self.setup_course();

    def test_get_html_track(self):
        SOURCE_XML = """
            <video show_captions="true"
            display_name="A Name"
                sub="{sub}" download_track="{download_track}"
            start_time="01:00:03" end_time="01:00:10"
            >
                <source src="example.mp4"/>
                <source src="example.webm"/>
                {track}
            </video>
        """

        cases = [
            {
                'download_track': u'true',
                'track': u'<track src="http://www.example.com/track"/>',
                'sub': u'a_sub_file.srt.sjson',
                'expected_track_url': u'http://www.example.com/track',
            },
            {
                'download_track': u'true',
                'track': u'',
                'sub': u'a_sub_file.srt.sjson',
                'expected_track_url': u'a_sub_file.srt.sjson',
            },
            {
                'download_track': u'true',
                'track': u'',
                'sub': u'',
                'expected_track_url': None
            },
            {
                'download_track': u'false',
                'track': u'<track src="http://www.example.com/track"/>',
                'sub': u'a_sub_file.srt.sjson',
                'expected_track_url': None,
            },
        ]

        expected_context = {
            'data_dir': getattr(self, 'data_dir', None),
            'caption_asset_path': '/static/subs/',
            'show_captions': 'true',
            'display_name': u'A Name',
            'end': 3610.0,
            'id': None,
            'sources': {
                u'mp4': u'example.mp4',
                u'webm': u'example.webm'
            },
            'start': 3603.0,
            'sub': u'a_sub_file.srt.sjson',
            'speed': 'null',
            'general_speed': 1.0,
            'track': u'http://www.example.com/track',
            'youtube_streams': '1.00:OEoXaMPEzfM',
            'autoplay': settings.FEATURES.get('AUTOPLAY_VIDEOS', True),
            'yt_test_timeout': 1500,
            'yt_test_url': 'https://gdata.youtube.com/feeds/api/videos/',
        }

        for data in cases:
            DATA = SOURCE_XML.format(
                download_track=data['download_track'],
                track=data['track'],
                sub=data['sub']
            )

            self.initialize_module(data=DATA)
            # track_url = self.item_descriptor.xmodule_runtime.handler_url(self.item_module, 'download_transcript')

            context = self.item_module.render('student_view').content

            expected_context.update({
                'ajax_url': self.item_descriptor.xmodule_runtime.ajax_url + '/save_user_state',
                # 'track': track_url if data['expected_track_url'] == u'a_sub_file.srt.sjson' else data['expected_track_url'],
                'track': u'http://www.example.com/track' if data['track'] else '',
                'sub': data['sub'],
                'id': self.item_module.location.html_id(),
            })

            self.assertEqual(
                context,
                self.item_module.xmodule_runtime.render_template('video.html', expected_context),
            )

    def test_get_html_source(self):
        SOURCE_XML = """
            <video show_captions="true"
            display_name="A Name"
            sub="a_sub_file.srt.sjson" source="{source}"
            download_video="{download_video}"
            start_time="01:00:03" end_time="01:00:10"
            >
                {sources}
            </video>
        """
        cases = [
            # self.download_video == True
            {
                'download_video': 'true',
                'source': 'example_source.mp4',
                'sources': """
                    <source src="example.mp4"/>
                    <source src="example.webm"/>
                """,
                'result': {
                    'main': u'example_source.mp4',
                    u'mp4': u'example.mp4',
                    u'webm': u'example.webm',
                },
            },
            {
                'download_video': 'true',
                'source': '',
                'sources': """
                    <source src="example.mp4"/>
                    <source src="example.webm"/>
                """,
                'result': {
                    'main': u'example.mp4',
                    u'mp4': u'example.mp4',
                    u'webm': u'example.webm',
                },
            },
            {
                'download_video': 'true',
                'source': '',
                'sources': [],
                'result': {},
            },

            # self.download_video == False
            {
                'download_video': 'false',
                'source': 'example_source.mp4',
                'sources': """
                    <source src="example.mp4"/>
                    <source src="example.webm"/>
                """,
                'result': {
                    u'mp4': u'example.mp4',
                    u'webm': u'example.webm',
                },
            },
        ]

        expected_context = {
            'data_dir': getattr(self, 'data_dir', None),
            'caption_asset_path': '/static/subs/',
            'show_captions': 'true',
            'display_name': u'A Name',
            'end': 3610.0,
            'id': None,
            'sources': None,
            'speed': 'null',
            'general_speed': 1.0,
            'start': 3603.0,
            'sub': u'a_sub_file.srt.sjson',
            'track': '',
            'youtube_streams': '1.00:OEoXaMPEzfM',
            'autoplay': settings.FEATURES.get('AUTOPLAY_VIDEOS', True),
            'yt_test_timeout': 1500,
            'yt_test_url': 'https://gdata.youtube.com/feeds/api/videos/',
        }

        for data in cases:
            DATA = SOURCE_XML.format(
                download_video=data['download_video'],
                source=data['source'],
                sources=data['sources']
            )
            self.initialize_module(data=DATA)
            context = self.item_module.render('student_view').content

            expected_context.update({
                'ajax_url': self.item_descriptor.xmodule_runtime.ajax_url + '/save_user_state',
                'sources': data['result'],
                'id': self.item_module.location.html_id(),
            })

            self.assertEqual(
                context,
                self.item_module.xmodule_runtime.render_template('video.html', expected_context)
            )


class TestVideoDescriptorInitialization(BaseTestXmodule):
    """
    Make sure that module initialization works correctly.
    """
    CATEGORY = "video"
    DATA = SOURCE_XML
    METADATA = {}

    def setUp(self):
        self.setup_course();

    def test_source_not_in_html5sources(self):
        metadata = {
            'source': 'http://example.org/video.mp4',
            'html5_sources': ['http://youtu.be/OEoXaMPEzfM.mp4'],
        }

        self.initialize_module(metadata=metadata)
        fields = self.item_descriptor.editable_metadata_fields

        self.assertIn('source', fields)
        self.assertEqual(self.item_module.source, 'http://example.org/video.mp4')
        self.assertTrue(self.item_module.download_video)
        self.assertTrue(self.item_module.source_visible)

    def test_source_in_html5sources(self):
        metadata = {
            'source': 'http://example.org/video.mp4',
            'html5_sources': ['http://example.org/video.mp4'],
        }

        self.initialize_module(metadata=metadata)
        fields = self.item_descriptor.editable_metadata_fields

        self.assertNotIn('source', fields)
        self.assertTrue(self.item_module.download_video)
        self.assertFalse(self.item_module.source_visible)

    @patch('xmodule.x_module.XModuleDescriptor.editable_metadata_fields', new_callable=PropertyMock)
    def test_download_video_is_explicitly_set(self, mock_editable_fields):
        mock_editable_fields.return_value = {
            'download_video': {
                'default_value': False,
                'explicitly_set': True,
                'display_name': 'Video Download Allowed',
                'help': 'Show a link beneath the video to allow students to download the video.',
                'type': 'Boolean',
                'value': False,
                'field_name': 'download_video',
                'options': [
                    {'display_name': "True", "value": True},
                    {'display_name': "False", "value": False}
                ],
            },
            'html5_sources': {
                'default_value': [],
                'explicitly_set': False,
                'display_name': 'Video Sources',
                'help': 'A list of filenames to be used with HTML5 video.',
                'type': 'List',
                'value': [u'http://youtu.be/OEoXaMPEzfM.mp4'],
                'field_name': 'html5_sources',
                'options': [],
            },
            'source': {
                'default_value': '',
                'explicitly_set': False,
                'display_name': 'Download Video',
                'help': 'The external URL to download the video.',
                'type': 'Generic',
                'value': u'http://example.org/video.mp4',
                'field_name': 'source',
                'options': [],
            },
            'track': {
                'default_value': '',
                'explicitly_set': False,
                'display_name': 'Download Transcript',
                'help': 'The external URL to download the timed transcript track.',
                'type': 'Generic',
                'value': u'',
                'field_name': 'track',
                'options': [],
            },
        }
        metadata = {
            'track': '',
            'source': 'http://example.org/video.mp4',
            'html5_sources': ['http://youtu.be/OEoXaMPEzfM.mp4'],
        }

        self.initialize_module(metadata=metadata)
        fields = self.item_descriptor.editable_metadata_fields

        self.assertIn('source', fields)
        self.assertFalse(self.item_module.download_video)
        self.assertTrue(self.item_module.source_visible)

    def test_source_is_empty(self):
        metadata = {
            'source': '',
            'html5_sources': ['http://youtu.be/OEoXaMPEzfM.mp4'],
        }

        self.initialize_module(metadata=metadata)
        fields = self.item_descriptor.editable_metadata_fields

        self.assertNotIn('source', fields)
        self.assertFalse(self.item_module.download_video)

    @unittest.skip('Skipped due to the reason described in BLD-811')
    def test_track_is_not_empty(self):
        metatdata = {
            'track': 'http://example.org/track',
        }

        self.initialize_module(metadata=metatdata)
        fields = self.item_descriptor.editable_metadata_fields

        self.assertIn('track', fields)
        self.assertEqual(self.item_module.track, 'http://example.org/track')
        self.assertTrue(self.item_module.download_track)
        self.assertTrue(self.item_module.track_visible)

    @unittest.skip('Skipped due to the reason described in BLD-811')
    @patch('xmodule.x_module.XModuleDescriptor.editable_metadata_fields', new_callable=PropertyMock)
    def test_download_track_is_explicitly_set(self, mock_editable_fields):
        mock_editable_fields.return_value = {
            'download_track': {
                'default_value': False,
                'explicitly_set': True,
                'display_name': 'Transcript Download Allowed',
                'help': 'Show a link beneath the video to allow students to download the transcript.',
                'type': 'Boolean',
                'value': False,
                'field_name': 'download_track',
                'options': [
                    {'display_name': "True", "value": True},
                    {'display_name': "False", "value": False}
                ],
            },
            'track': {
                'default_value': '',
                'explicitly_set': False,
                'display_name': 'Download Transcript',
                'help': 'The external URL to download the timed transcript track.',
                'type': 'Generic',
                'value': u'http://example.org/track',
                'field_name': 'track',
                'options': [],
            },
            'source': {
                'default_value': '',
                'explicitly_set': False,
                'display_name': 'Download Video',
                'help': 'The external URL to download the video.',
                'type': 'Generic',
                'value': u'',
                'field_name': 'source',
                'options': [],
            },
        }
        metadata = {
            'source': '',
            'track': 'http://example.org/track',
        }

        self.initialize_module(metadata=metadata)
        fields = self.item_descriptor.editable_metadata_fields

        self.assertIn('track', fields)
        self.assertEqual(self.item_module.track, 'http://example.org/track')
        self.assertFalse(self.item_module.download_track)
        self.assertTrue(self.item_module.track_visible)

    @unittest.skip('Skipped due to the reason described in BLD-811')
    def test_track_is_empty(self):
        metatdata = {
            'track': '',
        }

        self.initialize_module(metadata=metatdata)
        fields = self.item_descriptor.editable_metadata_fields

        self.assertNotIn('track', fields)
        self.assertEqual(self.item_module.track, '')
        self.assertFalse(self.item_module.download_track)
        self.assertFalse(self.item_module.track_visible)


class TestVideoGetTranscriptsMethod(TestVideo):
    """
    Make sure that `get_transcript` method works correctly
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

    def test_good_transcript(self):
        self.item_module.render('student_view')
        item = self.item_descriptor.xmodule_runtime.xmodule_instance

        good_sjson = _create_file(content="""
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
            """)

        _upload_file(good_sjson, self.item_module.location)
        subs_id = _get_subs_id(good_sjson.name)

        text = item.get_transcript(subs_id)
        expected_text = "Hi, welcome to Edx.\nLet's start with what is on your screen right now."

        self.assertEqual(text, expected_text)

    def test_not_found_error(self):
        self.item_module.render('student_view')
        item = self.item_descriptor.xmodule_runtime.xmodule_instance

        with self.assertRaises(NotFoundError):
            item.get_transcript('wrong')

    def test_value_error(self):
        self.item_module.render('student_view')
        item = self.item_descriptor.xmodule_runtime.xmodule_instance

        good_sjson = _create_file(content='bad content')

        _upload_file(good_sjson, self.item_module.location)
        subs_id = _get_subs_id(good_sjson.name)

        with self.assertRaises(ValueError):
            item.get_transcript(subs_id)

    def test_key_error(self):
        self.item_module.render('student_view')
        item = self.item_descriptor.xmodule_runtime.xmodule_instance

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

        _upload_file(good_sjson, self.item_module.location)
        subs_id = _get_subs_id(good_sjson.name)

        with self.assertRaises(KeyError):
            item.get_transcript(subs_id)


def _clear_assets(location):
    store = contentstore()

    content_location = StaticContent.compute_location(
        location.org, location.course, location.name
    )

    assets, __ = store.get_all_content_for_course(content_location)
    for asset in assets:
        asset_location = Location(asset["_id"])
        id = StaticContent.get_id_from_location(asset_location)
        store.delete(id)

def _get_subs_id(filename):
        basename = os.path.splitext(os.path.basename(filename))[0]
        return basename.replace('subs_', '').replace('.srt', '')

def _create_file(content=''):
    sjson_file = tempfile.NamedTemporaryFile(prefix="subs_", suffix=".srt.sjson")
    sjson_file.content_type = 'application/json'
    sjson_file.write(textwrap.dedent(content))
    sjson_file.seek(0)

    return sjson_file

def _upload_file(file, location):
    filename = 'subs_{}.srt.sjson'.format(_get_subs_id(file.name))
    mime_type = file.content_type

    content_location = StaticContent.compute_location(
        location.org, location.course, filename
    )

    sc_partial = partial(StaticContent, content_location, filename, mime_type)
    content = sc_partial(file.read())

    (thumbnail_content, thumbnail_location) = contentstore().generate_thumbnail(
        content,
        tempfile_path=None
    )
    del_cached_content(thumbnail_location)

    if thumbnail_content is not None:
        content.thumbnail_location = thumbnail_location

    contentstore().save(content)
    del_cached_content(content.location)
