# -*- coding: utf-8 -*-
"""Video xmodule tests in mongo."""

import os
import tempfile
import textwrap
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

    def init_module(self, data=None, model_data=None):
        DATA = str(self.DATA)
        if data:
            self.DATA = data

        MODEL_DATA = dict(self.MODEL_DATA)
        if model_data:
            self.MODEL_DATA.update(model_data)

        super(TestVideo, self).setUp()

        self.DATA = DATA
        self.MODEL_DATA = MODEL_DATA


    def get_subs_id(self, filename):
        basename = os.path.splitext(os.path.basename(filename))[0]
        return basename.replace('subs_', '').replace('.srt', '')

    def create_file(self, content=''):
        sjson_file = tempfile.NamedTemporaryFile(prefix="subs_", suffix=".srt.sjson")
        sjson_file.content_type = 'application/json'
        sjson_file.write(textwrap.dedent(content))
        sjson_file.seek(0)

        return sjson_file

    def upload_file(self, file, location):
        filename = 'subs_{}.srt.sjson'.format(self.get_subs_id(file.name))
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

    def clear_assets(self, location):
        store = contentstore()

        content_location = StaticContent.compute_location(
            location.org, location.course, location.name
        )

        assets = store.get_all_content_for_course(content_location)

        for asset in assets:
            asset_location = Location(asset["_id"])
            id = StaticContent.get_id_from_location(asset_location)
            store.delete(id)

    def tearDown(self):
        self.clear_assets(self.item_module.location)

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


class TestVideoYouTube(TestVideo):
    def test_video_constructor(self):
        """Make sure that all parameters extracted correclty from xml"""
        self.maxDiff = None
        context = self.item_module.render('student_view').content

        sources = {
            'main': u'example.mp4',
            u'mp4': u'example.mp4',
            u'webm': u'example.webm',
        }

        expected_context = {
            'data_dir': getattr(self, 'data_dir', None),
            'caption_asset_path': '/static/subs/',
            'show_captions': 'true',
            'display_name': u'A Name',
            'end': 3610.0,
            'id': self.item_module.location.html_id(),
            'sources': sources,
            'start': 3603.0,
            'sub': u'a_sub_file.srt.sjson',
            'track': None,
            'youtube_streams': _create_youtube_string(self.item_module),
            'autoplay': settings.FEATURES.get('AUTOPLAY_VIDEOS', False),
            'yt_test_timeout': 1500,
            'yt_test_url': 'https://gdata.youtube.com/feeds/api/videos/'
        }

        self.assertEqual(
            context,
            self.item_module.xmodule_runtime.render_template('video.html', expected_context)
        )

class TestVideoNonYouTube(TestVideo):
    """Integration tests: web client + mongo."""

    DATA = """
        <video show_captions="true"
        display_name="A Name"
        sub="a_sub_file.srt.sjson"
        start_time="01:00:03" end_time="01:00:10"
        >
            <source src="example.mp4"/>
            <source src="example.webm"/>
        </video>
    """
    MODEL_DATA = {
        'data': DATA
    }

    def test_video_constructor(self):
        """Make sure that if the 'youtube' attribute is omitted in XML, then
            the template generates an empty string for the YouTube streams.
        """
        self.maxDiff = None
        sources = {
            'main': u'example.mp4',
            u'mp4': u'example.mp4',
            u'webm': u'example.webm',
        }

        context = self.item_module.render('student_view').content

        expected_context = {
            'data_dir': getattr(self, 'data_dir', None),
            'caption_asset_path': '/static/subs/',
            'show_captions': 'true',
            'display_name': u'A Name',
            'end': 3610.0,
            'id': self.item_module.location.html_id(),
            'sources': sources,
            'start': 3603.0,
            'sub': u'a_sub_file.srt.sjson',
            'track': None,
            'youtube_streams': '1.00:OEoXaMPEzfM',
            'autoplay': settings.FEATURES.get('AUTOPLAY_VIDEOS', True),
            'yt_test_timeout': 1500,
            'yt_test_url': 'https://gdata.youtube.com/feeds/api/videos/'
        }

        self.assertEqual(
            context,
            self.item_module.xmodule_runtime.render_template('video.html', expected_context)
        )

class TestVideoGetTranscripts(TestVideo):
    """Integration tests: web client + mongo."""

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

    def test_good_transcript(self):
        self.item_module.render('student_view')
        item = self.item_descriptor.xmodule_runtime.xmodule_instance

        good_sjson = self.create_file(content="""
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
                    "LILA FISHER: Hi, welcome to Edx.",
                    "I&#39;m Lila Fisher, an Edx fellow helping to put"
                  ]
                }
            """)

        self.upload_file(good_sjson, self.item_module.location)
        subs_id = self.get_subs_id(good_sjson.name)

        text = item.get_transcript(subs_id)
        expected_text = "LILA FISHER: Hi, welcome to Edx.\nI'm Lila Fisher, an Edx fellow helping to put"

        self.assertEqual(
            text, expected_text
        )

    def test_not_found_error(self):
        self.item_module.render('student_view')
        item = self.item_descriptor.xmodule_runtime.xmodule_instance

        with self.assertRaises(NotFoundError):
            item.get_transcript('wrong')

    def test_value_error(self):
        self.item_module.render('student_view')
        item = self.item_descriptor.xmodule_runtime.xmodule_instance

        good_sjson = self.create_file(content="""
                bad content
            """)

        self.upload_file(good_sjson, self.item_module.location)
        subs_id = self.get_subs_id(good_sjson.name)

        with self.assertRaises(ValueError):
            item.get_transcript(subs_id)

    def test_key_error(self):
        self.item_module.render('student_view')
        item = self.item_descriptor.xmodule_runtime.xmodule_instance

        good_sjson = self.create_file(content="""
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

        self.upload_file(good_sjson, self.item_module.location)
        subs_id = self.get_subs_id(good_sjson.name)

        with self.assertRaises(KeyError):
            item.get_transcript(subs_id)


class TestVideoTrack(TestVideo):
    """Integration tests: web client + mongo."""

    def test_get_html_source(self):
        self.maxDiff = None
        SOURCE_XML = """
            <video show_captions="true"
            display_name="A Name"
                sub="{sub}" track="{track}"
            start_time="01:00:03" end_time="01:00:10"
            >
                <source src="example.mp4"/>
                <source src="example.webm"/>
            </video>
        """

        cases = [
            {
                'track': u'[&quot;true&quot;]',
                'sub': u'a_sub_file.srt.sjson',
            },
            {
                'track': u'[]',
                'sub': u'a_sub_file.srt.sjson',
            },
            {
                'track': u'[&quot;true&quot;]',
                'sub': u'',
            },
            {
                'track': u'[]',
                'sub': u'',
            }
        ]

        expected_context = {
            'data_dir': getattr(self, 'data_dir', None),
            'caption_asset_path': '/static/subs/',
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
            'sub': u'a_sub_file.srt.sjson',
            'track': '',
            'youtube_streams': '1.00:OEoXaMPEzfM',
            'autoplay': settings.FEATURES.get('AUTOPLAY_VIDEOS', True),
            'yt_test_timeout': 1500,
            'yt_test_url': 'https://gdata.youtube.com/feeds/api/videos/'
        }

        for data in cases:
            DATA = SOURCE_XML.format(
                track=data['track'],
                sub=data['sub'],
            )
            self.init_module(data=DATA)

            track_url = self.item_descriptor.xmodule_runtime.handler_url(self.item_module, 'download_transcript').rstrip('/?')

            expected_context.update({
                'track': track_url if self.item_module.track and data['sub'] else None,
                'sub': data['sub'],
                'id': self.item_module.location.html_id(),
            })

            context = self.item_module.render('student_view').content
            self.assertEqual(
                context,
                self.item_module.xmodule_runtime.render_template('video.html', expected_context)
            )

