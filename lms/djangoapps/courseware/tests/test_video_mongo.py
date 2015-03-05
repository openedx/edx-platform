# -*- coding: utf-8 -*-
"""Video xmodule tests in mongo."""
import json
from collections import OrderedDict
from mock import patch, MagicMock

from django.conf import settings

from xmodule.video_module import create_youtube_string
from xmodule.x_module import STUDENT_VIEW
from xmodule.tests.test_video import VideoDescriptorTestBase

from edxval.api import create_profile, create_video

from . import BaseTestXmodule
from .test_video_xml import SOURCE_XML
from .test_video_handlers import TestVideo


class TestVideoYouTube(TestVideo):
    METADATA = {}

    def test_video_constructor(self):
        """Make sure that all parameters extracted correctly from xml"""
        context = self.item_descriptor.render(STUDENT_VIEW).content
        sources = json.dumps([u'example.mp4', u'example.webm'])

        expected_context = {
            'ajax_url': self.item_descriptor.xmodule_runtime.ajax_url + '/save_user_state',
            'autoplay': settings.FEATURES.get('AUTOPLAY_VIDEOS', False),
            'branding_info': None,
            'license': None,
            'cdn_eval': False,
            'cdn_exp_group': None,
            'data_dir': getattr(self, 'data_dir', None),
            'display_name': u'A Name',
            'end': 3610.0,
            'id': self.item_descriptor.location.html_id(),
            'show_captions': 'true',
            'handout': None,
            'download_video_link': u'example.mp4',
            'sources': sources,
            'speed': 'null',
            'general_speed': 1.0,
            'start': 3603.0,
            'saved_video_position': 0.0,
            'sub': u'a_sub_file.srt.sjson',
            'track': None,
            'youtube_streams': create_youtube_string(self.item_descriptor),
            'yt_test_timeout': 1500,
            'yt_api_url': 'www.youtube.com/iframe_api',
            'yt_test_url': 'gdata.youtube.com/feeds/api/videos/',
            'transcript_download_format': 'srt',
            'transcript_download_formats_list': [{'display_name': 'SubRip (.srt) file', 'value': 'srt'}, {'display_name': 'Text (.txt) file', 'value': 'txt'}],
            'transcript_language': u'en',
            'transcript_languages': json.dumps(OrderedDict({"en": "English", "uk": u"Українська"})),
            'transcript_translation_url': self.item_descriptor.xmodule_runtime.handler_url(
                self.item_descriptor, 'transcript', 'translation'
            ).rstrip('/?'),
            'transcript_available_translations_url': self.item_descriptor.xmodule_runtime.handler_url(
                self.item_descriptor, 'transcript', 'available_translations'
            ).rstrip('/?'),
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
        context = self.item_descriptor.render(STUDENT_VIEW).content
        sources = json.dumps([u'example.mp4', u'example.webm'])

        expected_context = {
            'ajax_url': self.item_descriptor.xmodule_runtime.ajax_url + '/save_user_state',
            'branding_info': None,
            'license': None,
            'cdn_eval': False,
            'cdn_exp_group': None,
            'data_dir': getattr(self, 'data_dir', None),
            'show_captions': 'true',
            'handout': None,
            'display_name': u'A Name',
            'download_video_link': u'example.mp4',
            'end': 3610.0,
            'id': self.item_descriptor.location.html_id(),
            'sources': sources,
            'speed': 'null',
            'general_speed': 1.0,
            'start': 3603.0,
            'saved_video_position': 0.0,
            'sub': u'a_sub_file.srt.sjson',
            'track': None,
            'youtube_streams': '1.00:3_yD_cEKoCk',
            'autoplay': settings.FEATURES.get('AUTOPLAY_VIDEOS', True),
            'yt_test_timeout': 1500,
            'yt_api_url': 'www.youtube.com/iframe_api',
            'yt_test_url': 'gdata.youtube.com/feeds/api/videos/',
            'transcript_download_format': 'srt',
            'transcript_download_formats_list': [{'display_name': 'SubRip (.srt) file', 'value': 'srt'}, {'display_name': 'Text (.txt) file', 'value': 'txt'}],
            'transcript_language': u'en',
            'transcript_languages': '{"en": "English"}',
            'transcript_translation_url': self.item_descriptor.xmodule_runtime.handler_url(
                self.item_descriptor, 'transcript', 'translation'
            ).rstrip('/?'),
            'transcript_available_translations_url': self.item_descriptor.xmodule_runtime.handler_url(
                self.item_descriptor, 'transcript', 'available_translations'
            ).rstrip('/?')
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
        super(TestGetHtmlMethod, self).setUp()
        self.setup_course()

    def test_get_html_track(self):
        SOURCE_XML = """
            <video show_captions="true"
            display_name="A Name"
                sub="{sub}" download_track="{download_track}"
            start_time="01:00:03" end_time="01:00:10" download_video="true"
            >
                <source src="example.mp4"/>
                <source src="example.webm"/>
                {track}
                {transcripts}
            </video>
        """

        cases = [
            {
                'download_track': u'true',
                'track': u'<track src="http://www.example.com/track"/>',
                'sub': u'a_sub_file.srt.sjson',
                'expected_track_url': u'http://www.example.com/track',
                'transcripts': '',
            },
            {
                'download_track': u'true',
                'track': u'',
                'sub': u'a_sub_file.srt.sjson',
                'expected_track_url': u'a_sub_file.srt.sjson',
                'transcripts': '',
            },
            {
                'download_track': u'true',
                'track': u'',
                'sub': u'',
                'expected_track_url': None,
                'transcripts': '',
            },
            {
                'download_track': u'false',
                'track': u'<track src="http://www.example.com/track"/>',
                'sub': u'a_sub_file.srt.sjson',
                'expected_track_url': None,
                'transcripts': '',
            },
            {
                'download_track': u'true',
                'track': u'',
                'sub': u'',
                'expected_track_url': u'a_sub_file.srt.sjson',
                'transcripts': '<transcript language="uk" src="ukrainian.srt" />',
            },
        ]
        sources = json.dumps([u'example.mp4', u'example.webm'])

        expected_context = {
            'branding_info': None,
            'license': None,
            'cdn_eval': False,
            'cdn_exp_group': None,
            'data_dir': getattr(self, 'data_dir', None),
            'show_captions': 'true',
            'handout': None,
            'display_name': u'A Name',
            'download_video_link': u'example.mp4',
            'end': 3610.0,
            'id': None,
            'sources': sources,
            'start': 3603.0,
            'saved_video_position': 0.0,
            'sub': u'a_sub_file.srt.sjson',
            'speed': 'null',
            'general_speed': 1.0,
            'track': u'http://www.example.com/track',
            'youtube_streams': '1.00:3_yD_cEKoCk',
            'autoplay': settings.FEATURES.get('AUTOPLAY_VIDEOS', True),
            'yt_test_timeout': 1500,
            'yt_api_url': 'www.youtube.com/iframe_api',
            'yt_test_url': 'gdata.youtube.com/feeds/api/videos/',
            'transcript_download_formats_list': [{'display_name': 'SubRip (.srt) file', 'value': 'srt'}, {'display_name': 'Text (.txt) file', 'value': 'txt'}],
        }

        for data in cases:
            DATA = SOURCE_XML.format(
                download_track=data['download_track'],
                track=data['track'],
                sub=data['sub'],
                transcripts=data['transcripts'],
            )

            self.initialize_module(data=DATA)
            track_url = self.item_descriptor.xmodule_runtime.handler_url(
                self.item_descriptor, 'transcript', 'download'
            ).rstrip('/?')

            context = self.item_descriptor.render(STUDENT_VIEW).content

            expected_context.update({
                'transcript_download_format': None if self.item_descriptor.track and self.item_descriptor.download_track else 'srt',
                'transcript_languages': '{"en": "English"}' if not data['transcripts'] else json.dumps({"uk": u'Українська'}),
                'transcript_language': u'en' if not data['transcripts'] or data.get('sub') else u'uk',
                'transcript_translation_url': self.item_descriptor.xmodule_runtime.handler_url(
                    self.item_descriptor, 'transcript', 'translation'
                ).rstrip('/?'),
                'transcript_available_translations_url': self.item_descriptor.xmodule_runtime.handler_url(
                    self.item_descriptor, 'transcript', 'available_translations'
                ).rstrip('/?'),
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
                    'download_video_link': u'example_source.mp4',
                    'sources': json.dumps([u'example.mp4', u'example.webm']),
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
                    'download_video_link': u'example.mp4',
                    'sources': json.dumps([u'example.mp4', u'example.webm']),
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
                    'sources': json.dumps([u'example.mp4', u'example.webm']),
                },
            },
        ]

        initial_context = {
            'branding_info': None,
            'license': None,
            'cdn_eval': False,
            'cdn_exp_group': None,
            'data_dir': getattr(self, 'data_dir', None),
            'show_captions': 'true',
            'handout': None,
            'display_name': u'A Name',
            'download_video_link': None,
            'end': 3610.0,
            'id': None,
            'sources': '[]',
            'speed': 'null',
            'general_speed': 1.0,
            'start': 3603.0,
            'saved_video_position': 0.0,
            'sub': u'a_sub_file.srt.sjson',
            'track': None,
            'youtube_streams': '1.00:3_yD_cEKoCk',
            'autoplay': settings.FEATURES.get('AUTOPLAY_VIDEOS', True),
            'yt_test_timeout': 1500,
            'yt_api_url': 'www.youtube.com/iframe_api',
            'yt_test_url': 'gdata.youtube.com/feeds/api/videos/',
            'transcript_download_format': 'srt',
            'transcript_download_formats_list': [{'display_name': 'SubRip (.srt) file', 'value': 'srt'}, {'display_name': 'Text (.txt) file', 'value': 'txt'}],
            'transcript_language': u'en',
            'transcript_languages': '{"en": "English"}',
        }

        for data in cases:
            DATA = SOURCE_XML.format(
                download_video=data['download_video'],
                source=data['source'],
                sources=data['sources']
            )
            self.initialize_module(data=DATA)
            context = self.item_descriptor.render(STUDENT_VIEW).content

            expected_context = dict(initial_context)
            expected_context.update({
                'transcript_translation_url': self.item_descriptor.xmodule_runtime.handler_url(
                    self.item_descriptor, 'transcript', 'translation'
                ).rstrip('/?'),
                'transcript_available_translations_url': self.item_descriptor.xmodule_runtime.handler_url(
                    self.item_descriptor, 'transcript', 'available_translations'
                ).rstrip('/?'),
                'ajax_url': self.item_descriptor.xmodule_runtime.ajax_url + '/save_user_state',
                'id': self.item_descriptor.location.html_id(),
            })
            expected_context.update(data['result'])

            self.assertEqual(
                context,
                self.item_descriptor.xmodule_runtime.render_template('video.html', expected_context)
            )

    def test_get_html_with_non_existent_edx_video_id(self):
        """
        Tests the VideoModule get_html where a edx_video_id is given but a video is not found
        """
        SOURCE_XML = """
            <video show_captions="true"
            display_name="A Name"
            sub="a_sub_file.srt.sjson" source="{source}"
            download_video="{download_video}"
            start_time="01:00:03" end_time="01:00:10"
            edx_video_id="{edx_video_id}"
            >
                {sources}
            </video>
        """
        no_video_data = {
            'download_video': 'true',
            'source': 'example_source.mp4',
            'sources': """
            <source src="example.mp4"/>
            <source src="example.webm"/>
            """,
            'edx_video_id': "meow",
            'result': {
                'download_video_link': u'example_source.mp4',
                'sources': json.dumps([u'example.mp4', u'example.webm']),
            }
        }
        DATA = SOURCE_XML.format(
            download_video=no_video_data['download_video'],
            source=no_video_data['source'],
            sources=no_video_data['sources'],
            edx_video_id=no_video_data['edx_video_id']
        )
        self.initialize_module(data=DATA)

        # Referencing a non-existent VAL ID in courseware won't cause an error --
        # it'll just fall back to the values in the VideoDescriptor.
        self.assertIn("example_source.mp4", self.item_descriptor.render(STUDENT_VIEW).content)

    @patch('edxval.api.get_video_info')
    def test_get_html_with_mocked_edx_video_id(self, mock_get_video_info):
        mock_get_video_info.return_value = {
            'url': '/edxval/video/example',
            'edx_video_id': u'example',
            'duration': 111.0,
            'client_video_id': u'The example video',
            'encoded_videos': [
                {
                    'url': u'http://www.meowmix.com',
                    'file_size': 25556,
                    'bitrate': 9600,
                    'profile': u'desktop_mp4'
                }
            ]
        }

        SOURCE_XML = """
            <video show_captions="true"
            display_name="A Name"
            sub="a_sub_file.srt.sjson" source="{source}"
            download_video="{download_video}"
            start_time="01:00:03" end_time="01:00:10"
            edx_video_id="{edx_video_id}"
            >
                {sources}
            </video>
        """

        data = {
            # test with download_video set to false and make sure download_video_link is not set (is None)
            'download_video': 'false',
            'source': 'example_source.mp4',
            'sources': """
                <source src="example.mp4"/>
                <source src="example.webm"/>
            """,
            'edx_video_id': "mock item",
            'result': {
                'download_video_link': None,
                # make sure the desktop_mp4 url is included as part of the alternative sources.
                'sources': json.dumps([u'example.mp4', u'example.webm', u'http://www.meowmix.com']),
            }
        }

        # Video found for edx_video_id
        initial_context = {
            'branding_info': None,
            'license': None,
            'cdn_eval': False,
            'cdn_exp_group': None,
            'data_dir': getattr(self, 'data_dir', None),
            'show_captions': 'true',
            'handout': None,
            'display_name': u'A Name',
            'download_video_link': None,
            'end': 3610.0,
            'id': None,
            'sources': '[]',
            'speed': 'null',
            'general_speed': 1.0,
            'start': 3603.0,
            'saved_video_position': 0.0,
            'sub': u'a_sub_file.srt.sjson',
            'track': None,
            'youtube_streams': '1.00:3_yD_cEKoCk',
            'autoplay': settings.FEATURES.get('AUTOPLAY_VIDEOS', True),
            'yt_test_timeout': 1500,
            'yt_api_url': 'www.youtube.com/iframe_api',
            'yt_test_url': 'gdata.youtube.com/feeds/api/videos/',
            'transcript_download_format': 'srt',
            'transcript_download_formats_list': [{'display_name': 'SubRip (.srt) file', 'value': 'srt'}, {'display_name': 'Text (.txt) file', 'value': 'txt'}],
            'transcript_language': u'en',
            'transcript_languages': '{"en": "English"}',
        }

        DATA = SOURCE_XML.format(
            download_video=data['download_video'],
            source=data['source'],
            sources=data['sources'],
            edx_video_id=data['edx_video_id']
        )
        self.initialize_module(data=DATA)
        context = self.item_descriptor.render(STUDENT_VIEW).content

        expected_context = dict(initial_context)
        expected_context.update({
            'transcript_translation_url': self.item_descriptor.xmodule_runtime.handler_url(
                self.item_descriptor, 'transcript', 'translation'
            ).rstrip('/?'),
            'transcript_available_translations_url': self.item_descriptor.xmodule_runtime.handler_url(
                self.item_descriptor, 'transcript', 'available_translations'
            ).rstrip('/?'),
            'ajax_url': self.item_descriptor.xmodule_runtime.ajax_url + '/save_user_state',
            'id': self.item_descriptor.location.html_id(),
        })
        expected_context.update(data['result'])

        self.assertEqual(
            context,
            self.item_descriptor.xmodule_runtime.render_template('video.html', expected_context)
        )

    def test_get_html_with_existing_edx_video_id(self):
        # create test profiles and their encodings
        encoded_videos = []
        for profile, extension in [("desktop_webm", "webm"), ("desktop_mp4", "mp4")]:
            result = create_profile(
                dict(
                    profile_name=profile,
                    extension=extension,
                    width=200,
                    height=2001
                )
            )
            self.assertEqual(result, profile)
            encoded_videos.append(
                dict(
                    url=u"http://fake-video.edx.org/thundercats.{}".format(extension),
                    file_size=9000,
                    bitrate=42,
                    profile=profile,
                )
            )

        result = create_video(
            dict(
                client_video_id="Thunder Cats",
                duration=111,
                edx_video_id="thundercats",
                status='test',
                encoded_videos=encoded_videos
            )
        )
        self.assertEqual(result, "thundercats")

        SOURCE_XML = """
            <video show_captions="true"
            display_name="A Name"
            sub="a_sub_file.srt.sjson" source="{source}"
            download_video="{download_video}"
            start_time="01:00:03" end_time="01:00:10"
            edx_video_id="{edx_video_id}"
            >
                {sources}
            </video>
        """

        data = {
            'download_video': 'true',
            'source': 'example_source.mp4',
            'sources': """
                <source src="example.mp4"/>
                <source src="example.webm"/>
            """,
            'edx_video_id': "thundercats",
            'result': {
                'download_video_link': u'http://fake-video.edx.org/thundercats.mp4',
                # make sure the urls for the various encodings are included as part of the alternative sources.
                'sources': json.dumps(
                    [u'example.mp4', u'example.webm'] +
                    [video['url'] for video in encoded_videos]
                ),
            }
        }

        # Video found for edx_video_id
        initial_context = {
            'branding_info': None,
            'license': None,
            'cdn_eval': False,
            'cdn_exp_group': None,
            'data_dir': getattr(self, 'data_dir', None),
            'show_captions': 'true',
            'handout': None,
            'display_name': u'A Name',
            'download_video_link': None,
            'end': 3610.0,
            'id': None,
            'sources': '[]',
            'speed': 'null',
            'general_speed': 1.0,
            'start': 3603.0,
            'saved_video_position': 0.0,
            'sub': u'a_sub_file.srt.sjson',
            'track': None,
            'youtube_streams': '1.00:3_yD_cEKoCk',
            'autoplay': settings.FEATURES.get('AUTOPLAY_VIDEOS', True),
            'yt_test_timeout': 1500,
            'yt_api_url': 'www.youtube.com/iframe_api',
            'yt_test_url': 'gdata.youtube.com/feeds/api/videos/',
            'transcript_download_format': 'srt',
            'transcript_download_formats_list': [{'display_name': 'SubRip (.srt) file', 'value': 'srt'}, {'display_name': 'Text (.txt) file', 'value': 'txt'}],
            'transcript_language': u'en',
            'transcript_languages': '{"en": "English"}',
        }

        DATA = SOURCE_XML.format(
            download_video=data['download_video'],
            source=data['source'],
            sources=data['sources'],
            edx_video_id=data['edx_video_id']
        )
        self.initialize_module(data=DATA)
        context = self.item_descriptor.render(STUDENT_VIEW).content

        expected_context = dict(initial_context)
        expected_context.update({
            'transcript_translation_url': self.item_descriptor.xmodule_runtime.handler_url(
                self.item_descriptor, 'transcript', 'translation'
            ).rstrip('/?'),
            'transcript_available_translations_url': self.item_descriptor.xmodule_runtime.handler_url(
                self.item_descriptor, 'transcript', 'available_translations'
            ).rstrip('/?'),
            'ajax_url': self.item_descriptor.xmodule_runtime.ajax_url + '/save_user_state',
            'id': self.item_descriptor.location.html_id(),
        })
        expected_context.update(data['result'])

        self.assertEqual(
            context,
            self.item_descriptor.xmodule_runtime.render_template('video.html', expected_context)
        )

    # pylint: disable=invalid-name
    @patch('xmodule.video_module.video_module.BrandingInfoConfig')
    @patch('xmodule.video_module.video_module.get_video_from_cdn')
    def test_get_html_cdn_source(self, mocked_get_video, mock_BrandingInfoConfig):
        """
        Test if sources got from CDN.
        """

        mock_BrandingInfoConfig.get_config.return_value = {
            "CN": {
                'url': 'http://www.xuetangx.com',
                'logo_src': 'http://www.xuetangx.com/static/images/logo.png',
                'logo_tag': 'Video hosted by XuetangX.com'
            }
        }

        def side_effect(*args, **kwargs):
            cdn = {
                'http://example.com/example.mp4': 'http://cdn_example.com/example.mp4',
                'http://example.com/example.webm': 'http://cdn_example.com/example.webm',
            }
            return cdn.get(args[1])

        mocked_get_video.side_effect = side_effect

        SOURCE_XML = """
            <video show_captions="true"
            display_name="A Name"
            sub="a_sub_file.srt.sjson" source="{source}"
            download_video="{download_video}"
            edx_video_id="{edx_video_id}"
            start_time="01:00:03" end_time="01:00:10"
            >
                {sources}
            </video>
        """

        case_data = {
            'download_video': 'true',
            'source': 'example_source.mp4',
            'sources': """
                <source src="http://example.com/example.mp4"/>
                <source src="http://example.com/example.webm"/>
            """,
            'result': {
                'download_video_link': u'example_source.mp4',
                'sources': json.dumps(
                    [
                        u'http://cdn_example.com/example.mp4',
                        u'http://cdn_example.com/example.webm'
                    ]
                ),
            },
        }

        # test with and without edx_video_id specified.
        cases = [
            dict(case_data, edx_video_id=""),
            dict(case_data, edx_video_id="vid-v1:12345"),
        ]

        initial_context = {
            'branding_info': {
                'logo_src': 'http://www.xuetangx.com/static/images/logo.png',
                'logo_tag': 'Video hosted by XuetangX.com',
                'url': 'http://www.xuetangx.com'
            },
            'license': None,
            'cdn_eval': False,
            'cdn_exp_group': None,
            'data_dir': getattr(self, 'data_dir', None),
            'show_captions': 'true',
            'handout': None,
            'display_name': u'A Name',
            'download_video_link': None,
            'end': 3610.0,
            'id': None,
            'sources': '[]',
            'speed': 'null',
            'general_speed': 1.0,
            'start': 3603.0,
            'saved_video_position': 0.0,
            'sub': u'a_sub_file.srt.sjson',
            'track': None,
            'youtube_streams': '1.00:3_yD_cEKoCk',
            'autoplay': settings.FEATURES.get('AUTOPLAY_VIDEOS', True),
            'yt_test_timeout': 1500,
            'yt_api_url': 'www.youtube.com/iframe_api',
            'yt_test_url': 'gdata.youtube.com/feeds/api/videos/',
            'transcript_download_format': 'srt',
            'transcript_download_formats_list': [{'display_name': 'SubRip (.srt) file', 'value': 'srt'}, {'display_name': 'Text (.txt) file', 'value': 'txt'}],
            'transcript_language': u'en',
            'transcript_languages': '{"en": "English"}',
        }

        for data in cases:
            DATA = SOURCE_XML.format(
                download_video=data['download_video'],
                source=data['source'],
                sources=data['sources'],
                edx_video_id=data['edx_video_id'],
            )
            self.initialize_module(data=DATA)
            self.item_descriptor.xmodule_runtime.user_location = 'CN'

            context = self.item_descriptor.render('student_view').content

            expected_context = dict(initial_context)
            expected_context.update({
                'transcript_translation_url': self.item_descriptor.xmodule_runtime.handler_url(
                    self.item_descriptor, 'transcript', 'translation'
                ).rstrip('/?'),
                'transcript_available_translations_url': self.item_descriptor.xmodule_runtime.handler_url(
                    self.item_descriptor, 'transcript', 'available_translations'
                ).rstrip('/?'),
                'ajax_url': self.item_descriptor.xmodule_runtime.ajax_url + '/save_user_state',
                'id': self.item_descriptor.location.html_id(),
            })
            expected_context.update(data['result'])

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
        super(TestVideoDescriptorInitialization, self).setUp()
        self.setup_course()

    def test_source_not_in_html5sources(self):
        metadata = {
            'source': 'http://example.org/video.mp4',
            'html5_sources': ['http://youtu.be/3_yD_cEKoCk.mp4'],
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

    def test_download_video_is_explicitly_set(self):
        metadata = {
            'track': u'http://some_track.srt',
            'source': 'http://example.org/video.mp4',
            'html5_sources': ['http://youtu.be/3_yD_cEKoCk.mp4'],
            'download_video': False,
        }

        self.initialize_module(metadata=metadata)

        fields = self.item_descriptor.editable_metadata_fields
        self.assertIn('source', fields)
        self.assertIn('download_video', fields)

        self.assertFalse(self.item_descriptor.download_video)
        self.assertTrue(self.item_descriptor.source_visible)
        self.assertTrue(self.item_descriptor.download_track)

    def test_source_is_empty(self):
        metadata = {
            'source': '',
            'html5_sources': ['http://youtu.be/3_yD_cEKoCk.mp4'],
        }

        self.initialize_module(metadata=metadata)
        fields = self.item_descriptor.editable_metadata_fields

        self.assertNotIn('source', fields)
        self.assertFalse(self.item_descriptor.download_video)


class VideoDescriptorTest(VideoDescriptorTestBase):
    """
    Tests for video descriptor that requires access to django settings.
    """
    def setUp(self):
        super(VideoDescriptorTest, self).setUp()
        self.descriptor.runtime.handler_url = MagicMock()

    def test_get_context(self):
        """"
        Test get_context.

        This test is located here and not in xmodule.tests because get_context calls editable_metadata_fields.
        Which, in turn, uses settings.LANGUAGES from django setttings.
        """
        correct_tabs = [
            {
                'name': "Basic",
                'template': "video/transcripts.html",
                'current': True
            },
            {
                'name': 'Advanced',
                'template': 'tabs/metadata-edit-tab.html'
            }
        ]
        rendered_context = self.descriptor.get_context()
        self.assertListEqual(rendered_context['tabs'], correct_tabs)
