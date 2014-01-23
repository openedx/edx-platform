# -*- coding: utf-8 -*-
"""Video xmodule tests in mongo."""
from mock import patch, PropertyMock
import json

from . import BaseTestXmodule
from .test_video_xml import SOURCE_XML
from .test_video_handlers import TestVideo
from django.conf import settings
from xmodule.video_module import create_youtube_string


class TestVideoYouTube(TestVideo):
    METADATA = {}

    def test_video_constructor(self):
        """Make sure that all parameters extracted correctly from xml"""
        context = self.item_descriptor.render('student_view').content

        sources = {
            'main': u'example.mp4',
            u'mp4': u'example.mp4',
            u'webm': u'example.webm',
        }

        expected_context = {
            'ajax_url': self.item_descriptor.xmodule_runtime.ajax_url + '/save_user_state',
            'autoplay': settings.FEATURES.get('AUTOPLAY_VIDEOS', False),
            'data_dir': getattr(self, 'data_dir', None),
            'display_name': u'A Name',
            'end': 3610.0,
            'id': self.item_descriptor.location.html_id(),
            'show_captions': 'true',
            'sources': sources,
            'speed': 'null',
            'general_speed': 1.0,
            'start': 3603.0,
            'saved_video_position': 0.0,
            'sub': u'a_sub_file.srt.sjson',
            'track': None,
            'youtube_streams': create_youtube_string(self.item_descriptor),
            'yt_test_timeout': 1500,
            'yt_test_url': 'https://gdata.youtube.com/feeds/api/videos/',
            'transcript_language': 'en',
            'transcript_languages': '{"en": "English", "uk": "Ukrainian"}',
            'transcript_translation_url': self.item_descriptor.xmodule_runtime.handler_url(
                self.item_descriptor, 'transcript'
            ).rstrip('/?') + '/translation',
            'transcript_available_translations_url': self.item_descriptor.xmodule_runtime.handler_url(
                self.item_descriptor, 'transcript'
            ).rstrip('/?') + '/available_translations',
        }
        self.assertEqual(
            context,
            self.item_descriptor.xmodule_runtime.render_template('video.html', expected_context),
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

        context = self.item_descriptor.render('student_view').content
        expected_context = {
            'ajax_url': self.item_descriptor.xmodule_runtime.ajax_url + '/save_user_state',
            'data_dir': getattr(self, 'data_dir', None),
            'show_captions': 'true',
            'display_name': u'A Name',
            'end': 3610.0,
            'id': self.item_descriptor.location.html_id(),
            'sources': sources,
            'speed': 'null',
            'general_speed': 1.0,
            'start': 3603.0,
            'saved_video_position': 0.0,
            'sub': u'a_sub_file.srt.sjson',
            'track': None,
            'youtube_streams': '1.00:OEoXaMPEzfM',
            'autoplay': settings.FEATURES.get('AUTOPLAY_VIDEOS', True),
            'yt_test_timeout': 1500,
            'yt_test_url': 'https://gdata.youtube.com/feeds/api/videos/',
            'transcript_language': 'en',
            'transcript_languages': '{"en": "English"}',
            'transcript_translation_url': self.item_descriptor.xmodule_runtime.handler_url(
                self.item_descriptor, 'transcript'
            ).rstrip('/?') + '/translation',
            'transcript_available_translations_url': self.item_descriptor.xmodule_runtime.handler_url(
                self.item_descriptor, 'transcript'
            ).rstrip('/?') + '/available_translations',
        }

        self.assertEqual(
            context,
            self.item_descriptor.xmodule_runtime.render_template('video.html', expected_context),
        )


class TestGetHtmlMethod(BaseTestXmodule):
    '''
    Make sure that `get_html` works correctly.
    '''
    CATEGORY = "video"
    DATA = SOURCE_XML
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
            'show_captions': 'true',
            'display_name': u'A Name',
            'end': 3610.0,
            'id': None,
            'sources': {
                'main': u'example.mp4',
                u'mp4': u'example.mp4',
                u'webm': u'example.webm'
            },
            'start': 3603.0,
            'saved_video_position': 0.0,
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
            track_url = self.item_descriptor.xmodule_runtime.handler_url(
                self.item_descriptor, 'transcript'
            ).rstrip('/?') + '/download'

            context = self.item_descriptor.render('student_view').content

            expected_context.update({
                'transcript_languages': '{"en": "English"}' if self.item_descriptor.sub else '{}',
                'transcript_language': 'en' if self.item_descriptor.sub else json.dumps(None),
                'transcript_translation_url': self.item_descriptor.xmodule_runtime.handler_url(
                    self.item_descriptor, 'transcript'
                ).rstrip('/?') + '/translation',
                'transcript_available_translations_url': self.item_descriptor.xmodule_runtime.handler_url(
                    self.item_descriptor, 'transcript'
                ).rstrip('/?') + '/available_translations',
                'ajax_url': self.item_descriptor.xmodule_runtime.ajax_url + '/save_user_state',
                'track': track_url if data['expected_track_url'] == u'a_sub_file.srt.sjson' else data['expected_track_url'],
                'sub': data['sub'],
                'id': self.item_descriptor.location.html_id(),
            })

            self.assertEqual(
                context,
                self.item_descriptor.xmodule_runtime.render_template('video.html', expected_context),
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
            'show_captions': 'true',
            'display_name': u'A Name',
            'end': 3610.0,
            'id': None,
            'sources': None,
            'speed': 'null',
            'general_speed': 1.0,
            'start': 3603.0,
            'saved_video_position': 0.0,
            'sub': u'a_sub_file.srt.sjson',
            'track': None,
            'youtube_streams': '1.00:OEoXaMPEzfM',
            'autoplay': settings.FEATURES.get('AUTOPLAY_VIDEOS', True),
            'yt_test_timeout': 1500,
            'yt_test_url': 'https://gdata.youtube.com/feeds/api/videos/',
            'transcript_language': 'en',
            'transcript_languages': '{"en": "English"}',
        }

        for data in cases:
            DATA = SOURCE_XML.format(
                download_video=data['download_video'],
                source=data['source'],
                sources=data['sources']
            )
            self.initialize_module(data=DATA)
            context = self.item_descriptor.render('student_view').content

            expected_context.update({
                'transcript_translation_url': self.item_descriptor.xmodule_runtime.handler_url(
                    self.item_descriptor, 'transcript'
                ).rstrip('/?') + '/translation',
                'transcript_available_translations_url': self.item_descriptor.xmodule_runtime.handler_url(
                    self.item_descriptor, 'transcript'
                ).rstrip('/?') + '/available_translations',
                'ajax_url': self.item_descriptor.xmodule_runtime.ajax_url + '/save_user_state',
                'sources': data['result'],
                'id': self.item_descriptor.location.html_id(),
            })

            self.assertEqual(
                context,
                self.item_descriptor.xmodule_runtime.render_template('video.html', expected_context)
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
        self.assertEqual(self.item_descriptor.source, 'http://example.org/video.mp4')
        self.assertTrue(self.item_descriptor.download_video)
        self.assertTrue(self.item_descriptor.source_visible)

    def test_source_in_html5sources(self):
        metadata = {
            'source': 'http://example.org/video.mp4',
            'html5_sources': ['http://example.org/video.mp4'],
        }

        self.initialize_module(metadata=metadata)
        fields = self.item_descriptor.editable_metadata_fields

        self.assertNotIn('source', fields)
        self.assertTrue(self.item_descriptor.download_video)
        self.assertFalse(self.item_descriptor.source_visible)

    @patch('xmodule.video_module.VideoDescriptor.editable_metadata_fields', new_callable=PropertyMock)
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
                'value': u'http://some_track.srt',
                'field_name': 'track',
                'options': [],
            },
            'download_track': {
                'default_value': False,
                'explicitly_set': False,
                'display_name': 'Transcript Download Allowed',
                'help': 'Show a link beneath the video to allow students to download the transcript. Note: You must add a link to the HTML5 Transcript field above.',
                'type': 'Generic',
                'value': False,
                'field_name': 'download_track',
                'options': [],
            }
        }
        metadata = {
            'track': u'http://some_track.srt',
            'source': 'http://example.org/video.mp4',
            'html5_sources': ['http://youtu.be/OEoXaMPEzfM.mp4'],
        }

        self.initialize_module(metadata=metadata)
        fields = self.item_descriptor.editable_metadata_fields

        self.assertIn('source', fields)
        self.assertFalse(self.item_descriptor.download_video)
        self.assertTrue(self.item_descriptor.source_visible)
        self.assertTrue(self.item_descriptor.download_track)

    def test_source_is_empty(self):
        metadata = {
            'source': '',
            'html5_sources': ['http://youtu.be/OEoXaMPEzfM.mp4'],
        }

        self.initialize_module(metadata=metadata)
        fields = self.item_descriptor.editable_metadata_fields

        self.assertNotIn('source', fields)
        self.assertFalse(self.item_descriptor.download_video)
