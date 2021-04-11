# -*- coding: utf-8 -*-

"""
Acceptance tests for Video.
"""


import os
from unittest import skipIf
from mock import patch

from common.test.acceptance.fixtures.course import CourseFixture, XBlockFixtureDesc
from common.test.acceptance.pages.common.auto_auth import AutoAuthPage
from common.test.acceptance.pages.lms.courseware import CoursewarePage
from common.test.acceptance.pages.lms.tab_nav import TabNavPage
from common.test.acceptance.pages.lms.video.video import VideoPage
from common.test.acceptance.tests.helpers import (
    UniqueCourseTest,
    YouTubeStubConfig,
    is_youtube_available,
)
from openedx.core.lib.tests import attr

VIDEO_SOURCE_PORT = 8777
VIDEO_HOSTNAME = os.environ.get('BOK_CHOY_HOSTNAME', 'localhost')

HTML5_SOURCES = [
    'http://{}:{}/gizmo.mp4'.format(VIDEO_HOSTNAME, VIDEO_SOURCE_PORT),
    'http://{}:{}/gizmo.webm'.format(VIDEO_HOSTNAME, VIDEO_SOURCE_PORT),
    'http://{}:{}/gizmo.ogv'.format(VIDEO_HOSTNAME, VIDEO_SOURCE_PORT),
]

HTML5_SOURCES_INCORRECT = [
    'http://{}:{}/gizmo.mp99'.format(VIDEO_HOSTNAME, VIDEO_SOURCE_PORT),
]

HLS_SOURCES = [
    'http://{}:{}/hls/history.m3u8'.format(VIDEO_HOSTNAME, VIDEO_SOURCE_PORT),
]


@skipIf(is_youtube_available() is False, 'YouTube is not available!')
class VideoBaseTest(UniqueCourseTest):
    """
    Base class for tests of the Video Player
    Sets up the course and provides helper functions for the Video tests.
    """

    def setUp(self):
        """
        Initialization of pages and course fixture for video tests
        """
        super(VideoBaseTest, self).setUp()
        self.longMessage = True

        self.video = VideoPage(self.browser)
        self.tab_nav = TabNavPage(self.browser)
        self.courseware_page = CoursewarePage(self.browser, self.course_id)
        self.auth_page = AutoAuthPage(self.browser, course_id=self.course_id)

        self.course_fixture = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )

        self.metadata = None
        self.assets = []
        self.contents_of_verticals = None
        self.youtube_configuration = {}
        self.user_info = {}

        # reset youtube stub server
        self.addCleanup(YouTubeStubConfig.reset)

    def navigate_to_video(self):
        """ Prepare the course and get to the video and render it """
        self._install_course_fixture()
        self._navigate_to_courseware_video_and_render()

    def navigate_to_video_no_render(self):
        """
        Prepare the course and get to the video unit
        however do not wait for it to render, because
        the has been an error.
        """
        self._install_course_fixture()
        self._navigate_to_courseware_video_no_render()

    def _install_course_fixture(self):
        """ Install the course fixture that has been defined """
        if self.assets:
            self.course_fixture.add_asset(self.assets)

        chapter_sequential = XBlockFixtureDesc('sequential', 'Test Section')
        chapter_sequential.add_children(*self._add_course_verticals())
        chapter = XBlockFixtureDesc('chapter', 'Test Chapter').add_children(chapter_sequential)
        self.course_fixture.add_children(chapter)
        self.course_fixture.install()

        if len(self.youtube_configuration) > 0:
            YouTubeStubConfig.configure(self.youtube_configuration)

    def _add_course_verticals(self):
        """
        Create XBlockFixtureDesc verticals
        :return: a list of XBlockFixtureDesc
        """
        xblock_verticals = []
        _contents_of_verticals = self.contents_of_verticals

        # Video tests require at least one vertical with a single video.
        if not _contents_of_verticals:
            _contents_of_verticals = [[{'display_name': 'Video', 'metadata': self.metadata}]]

        for vertical_index, vertical in enumerate(_contents_of_verticals):
            xblock_verticals.append(self._create_single_vertical(vertical, vertical_index))

        return xblock_verticals

    def _create_single_vertical(self, vertical_contents, vertical_index):
        """
        Create a single course vertical of type XBlockFixtureDesc with category `vertical`.
        A single course vertical can contain single or multiple video modules.
        :param vertical_contents: a list of items for the vertical to contain
        :param vertical_index: index for the vertical display name
        :return: XBlockFixtureDesc
        """
        xblock_course_vertical = XBlockFixtureDesc('vertical', u'Test Vertical-{0}'.format(vertical_index))

        for video in vertical_contents:
            xblock_course_vertical.add_children(
                XBlockFixtureDesc('video', video['display_name'], metadata=video.get('metadata')))

        return xblock_course_vertical

    def _navigate_to_courseware_video(self):
        """ Register for the course and navigate to the video unit """
        self.auth_page.visit()
        self.user_info = self.auth_page.user_info
        self.courseware_page.visit()

    def _navigate_to_courseware_video_and_render(self):
        """ Wait for the video player to render """
        self._navigate_to_courseware_video()
        self.video.wait_for_video_player_render()

    def _navigate_to_courseware_video_no_render(self):
        """ Wait for the video Xmodule but not for rendering """
        self._navigate_to_courseware_video()
        self.video.wait_for_video_class()

    def metadata_for_mode(self, player_mode, additional_data=None):
        """
        Create a dictionary for video player configuration according to `player_mode`
        :param player_mode (str): Video player mode
        :param additional_data (dict): Optional additional metadata.
        :return: dict
        """
        metadata = {}
        youtube_ids = {
            'youtube_id_1_0': '',
            'youtube_id_0_75': '',
            'youtube_id_1_25': '',
            'youtube_id_1_5': '',
        }

        if player_mode == 'html5':
            metadata.update(youtube_ids)
            metadata.update({
                'html5_sources': HTML5_SOURCES
            })

        if player_mode == 'youtube_html5':
            metadata.update({
                'html5_sources': HTML5_SOURCES,
            })

        if player_mode == 'youtube_html5_unsupported_video':
            metadata.update({
                'html5_sources': HTML5_SOURCES_INCORRECT
            })

        if player_mode == 'html5_unsupported_video':
            metadata.update(youtube_ids)
            metadata.update({
                'html5_sources': HTML5_SOURCES_INCORRECT
            })

        if player_mode == 'hls':
            metadata.update(youtube_ids)
            metadata.update({
                'html5_sources': HLS_SOURCES,
            })

        if player_mode == 'html5_and_hls':
            metadata.update(youtube_ids)
            metadata.update({
                'html5_sources': HTML5_SOURCES + HLS_SOURCES,
            })

        if additional_data:
            metadata.update(additional_data)

        return metadata

    def go_to_sequential_position(self, position):
        """
        Navigate to sequential specified by `video_display_name`
        """
        self.courseware_page.go_to_sequential_position(position)
        self.video.wait_for_video_player_render()


@attr('a11y')
class LMSVideoBlockA11yTest(VideoBaseTest):
    """
    LMS Video Accessibility Test Class
    """

    def setUp(self):
        browser = os.environ.get('SELENIUM_BROWSER', 'firefox')

        # the a11y tests run in CI under phantomjs which doesn't
        # support html5 video or flash player, so the video tests
        # don't work in it. We still want to be able to run these
        # tests in CI, so override the browser setting if it is
        # phantomjs.
        if browser == 'phantomjs':
            browser = 'firefox'

        with patch.dict(os.environ, {'SELENIUM_BROWSER': browser}):
            super(LMSVideoBlockA11yTest, self).setUp()

    def test_video_player_a11y(self):
        # load transcripts so we can test skipping to
        self.assets.extend(['english_single_transcript.srt', 'subs_3_yD_cEKoCk.srt.sjson'])
        data = {'transcripts': {"en": "english_single_transcript.srt"}, 'sub': '3_yD_cEKoCk'}
        self.metadata = self.metadata_for_mode('youtube', additional_data=data)

        # go to video
        self.navigate_to_video()
        self.video.show_captions()

        # limit the scope of the audit to the video player only.
        self.video.a11y_audit.config.set_scope(
            include=["div.video"]
        )
        self.video.a11y_audit.check_for_accessibility_errors()
