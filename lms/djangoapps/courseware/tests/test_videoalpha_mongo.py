# -*- coding: utf-8 -*-
"""Video xmodule tests in mongo."""

from . import BaseTestXmodule
from .test_videoalpha_xml import SOURCE_XML
from django.conf import settings


class TestVideo(BaseTestXmodule):
    """Integration tests: web client + mongo."""

    CATEGORY = "videoalpha"
    DATA = SOURCE_XML
    MODEL_DATA = {
        'data': DATA
    }

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

    def test_videoalpha_constructor(self):
        """Make sure that all parameters extracted correclty from xml"""

        fragment = self.runtime.render(self.item_module, None, 'student_view')
        expected_context = {
            'data_dir': getattr(self, 'data_dir', None),
            'caption_asset_path': '/c4x/MITx/999/asset/subs_',
            'show_captions': self.item_module.show_captions,
            'display_name': self.item_module.display_name_with_default,
            'end': self.item_module.end_time,
            'id': self.item_module.location.html_id(),
            'sources': self.item_module.sources,
            'start': self.item_module.start_time,
            'sub': self.item_module.sub,
            'track': self.item_module.track,
            'youtube_streams': self.item_module.youtube_streams,
            'autoplay': settings.MITX_FEATURES.get('AUTOPLAY_VIDEOS', True)
        }
        self.assertEqual(fragment.content, self.runtime.render_template('videoalpha.html', expected_context))


class TestVideoNonYouTube(TestVideo):
    """Integration tests: web client + mongo."""

    DATA = """
        <videoalpha show_captions="true"
        data_dir=""
        caption_asset_path=""
        autoplay="true"
        start_time="01:00:03" end_time="01:00:10"
        >
            <source src=".../mit-3091x/M-3091X-FA12-L21-3_100.mp4"/>
            <source src=".../mit-3091x/M-3091X-FA12-L21-3_100.webm"/>
            <source src=".../mit-3091x/M-3091X-FA12-L21-3_100.ogv"/>
        </videoalpha>
    """
    MODEL_DATA = {
        'data': DATA
    }

    def test_videoalpha_constructor(self):
        """Make sure that if the 'youtube' attribute is omitted in XML, then
            the template generates an empty string for the YouTube streams.
        """

        fragment = self.runtime.render(self.item_module, None, 'student_view')
        expected_context = {
            'data_dir': getattr(self, 'data_dir', None),
            'caption_asset_path': '/c4x/MITx/999/asset/subs_',
            'show_captions': self.item_module.show_captions,
            'display_name': self.item_module.display_name_with_default,
            'end': self.item_module.end_time,
            'id': self.item_module.location.html_id(),
            'sources': self.item_module.sources,
            'start': self.item_module.start_time,
            'sub': self.item_module.sub,
            'track': self.item_module.track,
            'youtube_streams': '',
            'autoplay': settings.MITX_FEATURES.get('AUTOPLAY_VIDEOS', True)
        }
        self.assertEqual(fragment.content, self.runtime.render_template('videoalpha.html', expected_context))
