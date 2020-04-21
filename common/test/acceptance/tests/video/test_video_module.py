# -*- coding: utf-8 -*-

"""
Acceptance tests for Video.
"""


import os
from unittest import skipIf

from ddt import data, ddt, unpack
from mock import patch
from six.moves import range

from common.test.acceptance.fixtures.course import CourseFixture, XBlockFixtureDesc
from common.test.acceptance.pages.common.auto_auth import AutoAuthPage
from common.test.acceptance.pages.lms.course_info import CourseInfoPage
from common.test.acceptance.pages.lms.courseware import CoursewarePage
from common.test.acceptance.pages.lms.tab_nav import TabNavPage
from common.test.acceptance.pages.lms.video.video import VideoPage
from common.test.acceptance.tests.helpers import (
    UniqueCourseTest,
    YouTubeStubConfig,
    is_youtube_available,
    skip_if_browser
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
        self.course_info_page = CourseInfoPage(self.browser, self.course_id)
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


@attr(shard=13)
@ddt
class YouTubeVideoTest(VideoBaseTest):
    """ Test YouTube Video Player """

    def test_youtube_video_rendering_wo_html5_sources(self):
        """
        Scenario: Video component is rendered in the LMS in Youtube mode without HTML5 sources
        Given the course has a Video component in "Youtube" mode
        Then the video has rendered in "Youtube" mode
        """
        self.navigate_to_video()

        # Verify that video has rendered in "Youtube" mode
        self.assertTrue(self.video.is_video_rendered('youtube'))

    def test_transcript_button_wo_english_transcript(self):
        """
        Scenario: Transcript button works correctly w/o english transcript in Youtube mode
        Given the course has a Video component in "Youtube" mode
        And I have defined a non-english transcript for the video
        And I have uploaded a non-english transcript file to assets
        Then I see the correct text in the captions
        """
        data = {'transcripts': {'zh': 'chinese_transcripts.srt'}}
        self.metadata = self.metadata_for_mode('youtube', data)
        self.assets.append('chinese_transcripts.srt')
        self.navigate_to_video()
        self.video.show_captions()

        # Verify that we see "好 各位同学" text in the transcript
        unicode_text = u"好 各位同学"
        self.assertIn(unicode_text, self.video.captions_text)

    def test_cc_button(self):
        """
        Scenario: CC button works correctly with transcript in YouTube mode
        Given the course has a video component in "Youtube" mode
        And I have defined a transcript for the video
        Then I see the closed captioning element over the video
        """
        data = {'transcripts': {'zh': 'chinese_transcripts.srt'}}
        self.metadata = self.metadata_for_mode('youtube', data)
        self.assets.append('chinese_transcripts.srt')
        self.navigate_to_video()

        # Show captions and make sure they're visible and cookie is set
        self.video.show_closed_captions()
        self.video.wait_for_closed_captions()
        self.assertTrue(self.video.is_closed_captions_visible)
        self.video.reload_page()
        self.assertTrue(self.video.is_closed_captions_visible)

        # Hide captions and make sure they're hidden and cookie is unset
        self.video.hide_closed_captions()
        self.video.wait_for_closed_captions_to_be_hidden()
        self.video.reload_page()
        self.video.wait_for_closed_captions_to_be_hidden()

    def test_transcript_button_transcripts_and_sub_fields_empty(self):
        """
        Scenario: Transcript button works correctly if transcripts and sub fields are empty,
            but transcript file exists in assets (Youtube mode of Video component)
        Given the course has a Video component in "Youtube" mode
        And I have uploaded a .srt.sjson file to assets
        Then I see the correct english text in the captions
        """
        self._install_course_fixture()
        self.course_fixture.add_asset(['subs_3_yD_cEKoCk.srt.sjson'])
        self.course_fixture._upload_assets()
        self._navigate_to_courseware_video_and_render()
        self.video.show_captions()

        # Verify that we see "Welcome to edX." text in the captions
        self.assertIn('Welcome to edX.', self.video.captions_text)

    def test_transcript_button_hidden_no_translations(self):
        """
        Scenario: Transcript button is hidden if no translations
        Given the course has a Video component in "Youtube" mode
        Then the "Transcript" button is hidden
        """
        self.navigate_to_video()
        self.assertFalse(self.video.is_button_shown('transcript_button'))

    def test_download_button_wo_english_transcript(self):
        """
        Scenario: Download button works correctly w/o english transcript in YouTube mode
        Given the course has a Video component in "Youtube" mode
        And I have defined a downloadable non-english transcript for the video
        And I have uploaded a non-english transcript file to assets
        Then I can download the transcript in "srt" format
        """
        data = {'download_track': True, 'transcripts': {'zh': 'chinese_transcripts.srt'}}
        self.metadata = self.metadata_for_mode('youtube', additional_data=data)
        self.assets.append('chinese_transcripts.srt')

        # go to video
        self.navigate_to_video()

        # check if we can download transcript in "srt" format that has text "好 各位同学"
        unicode_text = u"好 各位同学"
        self.assertTrue(self.video.downloaded_transcript_contains_text('srt', unicode_text))

    def test_download_button_two_transcript_languages(self):
        """
        Scenario: Download button works correctly for multiple transcript languages
        Given the course has a Video component in "Youtube" mode
        And I have defined a downloadable non-english transcript for the video
        And I have defined english subtitles for the video
        Then I see the correct english text in the captions
        And the english transcript downloads correctly
        And I see the correct non-english text in the captions
        And the non-english transcript downloads correctly
        """
        self.assets.extend(['chinese_transcripts.srt', 'subs_3_yD_cEKoCk.srt.sjson'])
        data = {'download_track': True, 'transcripts': {'zh': 'chinese_transcripts.srt'}, 'sub': '3_yD_cEKoCk'}
        self.metadata = self.metadata_for_mode('youtube', additional_data=data)

        # go to video
        self.navigate_to_video()

        # check if "Welcome to edX." text in the captions
        self.assertIn('Welcome to edX.', self.video.captions_text)

        # check if we can download transcript in "srt" format that has text "Welcome to edX."
        self.assertTrue(self.video.downloaded_transcript_contains_text('srt', 'Welcome to edX.'))

        # select language with code "zh"
        self.assertTrue(self.video.select_language('zh'))

        # check if we see "好 各位同学" text in the captions
        unicode_text = u"好 各位同学"
        self.assertIn(unicode_text, self.video.captions_text)

        # check if we can download transcript in "srt" format that has text "好 各位同学"
        unicode_text = u"好 各位同学"
        self.assertTrue(self.video.downloaded_transcript_contains_text('srt', unicode_text))

    def test_video_rendering_with_default_response_time(self):
        """
        Scenario: Video is rendered in Youtube mode when the YouTube Server responds quickly
        Given the YouTube server response time less than 1.5 seconds
        And the course has a Video component in "Youtube_HTML5" mode
        Then the video has rendered in "Youtube" mode
        """
        # configure youtube server
        self.youtube_configuration['time_to_response'] = 0.4
        self.metadata = self.metadata_for_mode('youtube_html5')

        self.navigate_to_video()

        self.assertTrue(self.video.is_video_rendered('youtube'))

    def test_video_rendering_wo_default_response_time(self):
        """
        Scenario: Video is rendered in HTML5 when the YouTube Server responds slowly
        Given the YouTube server response time is greater than 1.5 seconds
        And the course has a Video component in "Youtube_HTML5" mode
        Then the video has rendered in "HTML5" mode
        """
        # configure youtube server
        self.youtube_configuration['time_to_response'] = 7.0
        self.metadata = self.metadata_for_mode('youtube_html5')

        self.navigate_to_video()

        self.assertTrue(self.video.is_video_rendered('html5'))

    def test_video_with_youtube_blocked_with_default_response_time(self):
        """
        Scenario: Video is rendered in HTML5 mode when the YouTube API is blocked
        Given the YouTube API is blocked
        And the course has a Video component in "Youtube_HTML5" mode
        Then the video has rendered in "HTML5" mode
        And only one video has rendered
        """
        # configure youtube server
        self.youtube_configuration.update({
            'youtube_api_blocked': True,
        })

        self.metadata = self.metadata_for_mode('youtube_html5')

        self.navigate_to_video()

        self.assertTrue(self.video.is_video_rendered('html5'))

        # The video should only be loaded once
        self.assertEqual(len(self.video.q(css='video')), 1)

    def test_video_with_youtube_blocked_delayed_response_time(self):
        """
        Scenario: Video is rendered in HTML5 mode when the YouTube API is blocked
        Given the YouTube server response time is greater than 1.5 seconds
        And the YouTube API is blocked
        And the course has a Video component in "Youtube_HTML5" mode
        Then the video has rendered in "HTML5" mode
        And only one video has rendered
        """
        # configure youtube server
        self.youtube_configuration.update({
            'time_to_response': 2.0,
            'youtube_api_blocked': True,
        })

        self.metadata = self.metadata_for_mode('youtube_html5')

        self.navigate_to_video()

        self.assertTrue(self.video.is_video_rendered('html5'))

        # The video should only be loaded once
        self.assertEqual(len(self.video.q(css='video')), 1)

    def test_html5_video_rendered_with_youtube_captions(self):
        """
        Scenario: User should see Youtube captions for If there are no transcripts
        available for HTML5 mode
        Given that I have uploaded a .srt.sjson file to assets for Youtube mode
        And the YouTube API is blocked
        And the course has a Video component in "Youtube_HTML5" mode
        And Video component rendered in HTML5 mode
        And Html5 mode video has no transcripts
        When I see the captions for HTML5 mode video
        Then I should see the Youtube captions
        """
        self.assets.append('subs_3_yD_cEKoCk.srt.sjson')
        # configure youtube server
        self.youtube_configuration.update({
            'time_to_response': 2.0,
            'youtube_api_blocked': True,
        })

        data = {'sub': '3_yD_cEKoCk'}
        self.metadata = self.metadata_for_mode('youtube_html5', additional_data=data)

        self.navigate_to_video()

        self.assertTrue(self.video.is_video_rendered('html5'))
        # check if caption button is visible
        self.assertTrue(self.video.is_button_shown('transcript_button'))
        self._verify_caption_text('Welcome to edX.')

    @data(('srt', '00:00:00,260'), ('txt', 'Welcome to edX.'))
    @unpack
    def test_download_transcript_links_work_correctly(self, file_type, search_text):
        """
        Scenario: Download 'srt' transcript link works correctly.
        Download 'txt' transcript link works correctly.
        Given the course has Video components A and B in "Youtube" mode
        And Video component C in "HTML5" mode
        And I have defined downloadable transcripts for the videos
        Then I can download a transcript for Video A in "srt" format
        And the Download Transcript menu does not exist for Video C
        """

        data_a = {'sub': '3_yD_cEKoCk', 'download_track': True}
        youtube_a_metadata = self.metadata_for_mode('youtube', additional_data=data_a)
        self.assets.append('subs_3_yD_cEKoCk.srt.sjson')

        data_b = {'youtube_id_1_0': 'b7xgknqkQk8', 'sub': 'b7xgknqkQk8', 'download_track': True}
        youtube_b_metadata = self.metadata_for_mode('youtube', additional_data=data_b)
        self.assets.append('subs_b7xgknqkQk8.srt.sjson')

        data_c = {'track': 'http://example.org/', 'download_track': True}
        html5_c_metadata = self.metadata_for_mode('html5', additional_data=data_c)

        self.contents_of_verticals = [
            [{'display_name': 'A', 'metadata': youtube_a_metadata}],
            [{'display_name': 'B', 'metadata': youtube_b_metadata}],
            [{'display_name': 'C', 'metadata': html5_c_metadata}]
        ]

        # open the section with videos (open vertical containing video "A")
        self.navigate_to_video()

        # check if we can download transcript in "srt" format that has text "00:00:00,260"
        self.assertTrue(self.video.downloaded_transcript_contains_text(file_type, search_text))

        # open vertical containing video "C"
        self.courseware_page.nav.go_to_vertical('Test Vertical-2')

        # menu "download_transcript" doesn't exist
        self.assertFalse(self.video.is_menu_present('download_transcript'))

    def _verify_caption_text(self, text):
        self.video._wait_for(
            lambda: (text in self.video.captions_text),
            u'Captions contain "{}" text'.format(text),
            timeout=5
        )

    def _verify_closed_caption_text(self, text):
        """
        Scenario: returns True if the captions are visible, False is else
        """
        self.video.wait_for(
            lambda: (text in self.video.closed_captions_text),
            u'Closed captions contain "{}" text'.format(text),
            timeout=5
        )

    def test_video_language_menu_working_closed_captions(self):
        """
        Scenario: Language menu works correctly in Video component, checks closed captions
        Given the course has a Video component in "Youtube" mode
        And I have defined multiple language transcripts for the videos
        And I make sure captions are closed
        And I see video menu "language" with correct items
        And I select language with code "en"
        Then I see "Welcome to edX." text in the closed captions
        And I select language with code "zh"
        Then I see "我们今天要讲的题目是" text in the closed captions
        """
        self.assets.extend(['chinese_transcripts.srt', 'subs_3_yD_cEKoCk.srt.sjson'])
        data = {'transcripts': {"zh": "chinese_transcripts.srt"}, 'sub': '3_yD_cEKoCk'}
        self.metadata = self.metadata_for_mode('youtube', additional_data=data)

        # go to video
        self.navigate_to_video()
        self.video.show_closed_captions()

        correct_languages = {'en': 'English', 'zh': 'Chinese'}
        self.assertEqual(self.video.caption_languages, correct_languages)

        # we start the video, then pause it to activate the transcript
        self.video.click_player_button('play')
        self.video.wait_for_position('0:03')
        self.video.click_player_button('pause')

        self.video.select_language('en')
        self.video.click_transcript_line(line_no=1)
        self._verify_closed_caption_text('Welcome to edX.')

        self.video.select_language('zh')
        unicode_text = u"我们今天要讲的题目是"
        self.video.click_transcript_line(line_no=1)
        self._verify_closed_caption_text(unicode_text)

    def test_video_component_stores_speed_correctly_for_multiple_videos(self):
        """
        Scenario: Video component stores speed correctly when each video is in separate sequential
        Given I have a video "A" in "Youtube" mode in position "1" of sequential
        And a video "B" in "Youtube" mode in position "2" of sequential
        And a video "C" in "HTML5" mode in position "3" of sequential
        """
        # vertical titles are created in VideoBaseTest._create_single_vertical
        # and are of the form Test Vertical-{_} where _ is the index in self.contents_of_verticals
        self.contents_of_verticals = [
            [{'display_name': 'A'}], [{'display_name': 'B'}],
            [{'display_name': 'C', 'metadata': self.metadata_for_mode('html5')}]
        ]

        self.navigate_to_video()

        # select the "2.0" speed on video "A"
        self.courseware_page.nav.go_to_vertical('Test Vertical-0')
        self.video.wait_for_video_player_render()
        self.video.speed = '2.0'

        # select the "0.50" speed on video "B"
        self.courseware_page.nav.go_to_vertical('Test Vertical-1')
        self.video.wait_for_video_player_render()
        self.video.speed = '0.50'

        # open video "C"
        self.courseware_page.nav.go_to_vertical('Test Vertical-2')
        self.video.wait_for_video_player_render()

        # Since the playback speed was set to .5 in "B", this video will also be impacted
        # because a playback speed has never explicitly been set for it. However, this video
        # does not have a .5 playback option, so the closest possible (.75) should be selected.
        self.video.verify_speed_changed('0.75x')

        # go to the vertical containing video "A"
        self.courseware_page.nav.go_to_vertical('Test Vertical-0')

        # Video "A" should still play at speed 2.0 because it was explicitly set to that.
        self.assertEqual(self.video.speed, '2.0x')

        # reload the page
        self.video.reload_page()

        # go to the vertical containing video "A"
        self.courseware_page.nav.go_to_vertical('Test Vertical-0')

        # check if video "A" should start playing at speed "2.0"
        self.assertEqual(self.video.speed, '2.0x')

        # select the "1.0" speed on video "A"
        self.video.speed = '1.0'

        # go to the vertical containing "B"
        self.courseware_page.nav.go_to_vertical('Test Vertical-1')

        # Video "B" should still play at speed .5 because it was explicitly set to that.
        self.assertEqual(self.video.speed, '0.50x')

        # go to the vertical containing video "C"
        self.courseware_page.nav.go_to_vertical('Test Vertical-2')

        # The change of speed for Video "A" should  impact Video "C" because it still has
        # not been explicitly set to a speed.
        self.video.verify_speed_changed('1.0x')

    def test_video_has_correct_transcript(self):
        """
        Scenario: Youtube video has correct transcript if fields for other speeds are filled
        Given it has a video in "Youtube" mode
        And I have uploaded multiple transcripts
        And I make sure captions are opened
        Then I see "Welcome to edX." text in the captions
        And I select the "1.50" speed
        And I reload the page with video
        Then I see "Welcome to edX." text in the captions
        And I see duration "1:56"

        """
        self.assets.extend(['subs_3_yD_cEKoCk.srt.sjson', 'subs_b7xgknqkQk8.srt.sjson'])
        data = {'sub': '3_yD_cEKoCk', 'youtube_id_1_5': 'b7xgknqkQk8'}
        self.metadata = self.metadata_for_mode('youtube', additional_data=data)

        # go to video
        self.navigate_to_video()

        self.video.show_captions()

        self.assertIn('Welcome to edX.', self.video.captions_text)

        self.video.speed = '1.50'

        self.video.reload_page()

        self.assertIn('Welcome to edX.', self.video.captions_text)

        self.assertTrue(self.video.duration, '1.56')

    def test_video_position_stored_correctly_wo_seek(self):
        """
        Scenario: Video component stores position correctly when page is reloaded
        Given the course has a Video component in "Youtube" mode
        Then the video has rendered in "Youtube" mode
        And I click video button "play""
        Then I wait until video reaches at position "0.03"
        And I click video button "pause"
        And I reload the page with video
        And I click video button "play""
        And I click video button "pause"
        Then video slider should be Equal or Greater than "0:03"

        """
        self.navigate_to_video()

        self.video.click_player_button('play')

        self.video.wait_for_position('0:03')

        self.video.click_player_button('pause')

        self.video.reload_page()

        self.video.click_player_button('play')
        self.video.click_player_button('pause')

        self.assertGreaterEqual(self.video.seconds, 3)

    def test_simplified_and_traditional_chinese_transcripts(self):
        """
        Scenario: Simplified and Traditional Chinese transcripts work as expected in Youtube mode

        Given the course has a Video component in "Youtube" mode
        And I have defined a Simplified Chinese transcript for the video
        And I have defined a Traditional Chinese transcript for the video
        Then I see the correct subtitle language options in cc menu
        Then I see the correct text in the captions for Simplified and Traditional Chinese transcripts
        And I can download the transcripts for Simplified and Traditional Chinese
        And video subtitle menu has 'zh_HANS', 'zh_HANT' translations for 'Simplified Chinese'
        and 'Traditional Chinese' respectively
        """
        data = {
            'download_track': True,
            'transcripts': {'zh_HANS': 'simplified_chinese.srt', 'zh_HANT': 'traditional_chinese.srt'}
        }
        self.metadata = self.metadata_for_mode('youtube', data)
        self.assets.extend(['simplified_chinese.srt', 'traditional_chinese.srt'])
        self.navigate_to_video()

        langs = {'zh_HANS': u'在线学习是革', 'zh_HANT': u'在線學習是革'}
        for lang_code, unicode_text in langs.items():
            self.video.scroll_to_button("transcript_button")
            self.assertTrue(self.video.select_language(lang_code))
            self.assertIn(unicode_text, self.video.captions_text)
            self.assertTrue(self.video.downloaded_transcript_contains_text('srt', unicode_text))

        self.assertEqual(self.video.caption_languages, {'zh_HANS': 'Simplified Chinese', 'zh_HANT': 'Traditional Chinese'})


@attr(shard=13)
class YouTubeHtml5VideoTest(VideoBaseTest):
    """ Test YouTube HTML5 Video Player """

    def test_youtube_video_rendering_with_unsupported_sources(self):
        """
        Scenario: Video component is rendered in the LMS in Youtube mode
            with HTML5 sources that doesn't supported by browser
        Given the course has a Video component in "Youtube_HTML5_Unsupported_Video" mode
        Then the video has rendered in "Youtube" mode
        """
        self.metadata = self.metadata_for_mode('youtube_html5_unsupported_video')
        self.navigate_to_video()

        # Verify that the video has rendered in "Youtube" mode
        self.assertTrue(self.video.is_video_rendered('youtube'))


@attr(shard=19)
class Html5VideoTest(VideoBaseTest):
    """ Test HTML5 Video Player """

    def test_autoplay_disabled_for_video_component(self):
        """
        Scenario: Autoplay is disabled by default for a Video component
        Given the course has a Video component in "HTML5" mode
        When I view the Video component
        Then it does not have autoplay enabled
        """
        self.metadata = self.metadata_for_mode('html5')
        self.navigate_to_video()

        # Verify that the video has autoplay mode disabled
        self.assertFalse(self.video.is_autoplay_enabled)

    def test_html5_video_rendering_with_unsupported_sources(self):
        """
        Scenario: LMS displays an error message for HTML5 sources that are not supported by browser
        Given the course has a Video component in "HTML5_Unsupported_Video" mode
        When I view the Video component
        Then and error message is shown
        And the error message has the correct text
        """
        self.metadata = self.metadata_for_mode('html5_unsupported_video')
        self.navigate_to_video_no_render()

        # Verify that error message is shown
        self.assertTrue(self.video.is_error_message_shown)

        # Verify that error message has correct text
        correct_error_message_text = 'No playable video sources found.'
        self.assertIn(correct_error_message_text, self.video.error_message_text)

        # Verify that spinner is not shown
        self.assertFalse(self.video.is_spinner_shown)

    def test_download_button_wo_english_transcript(self):
        """
        Scenario: Download button works correctly w/o english transcript in HTML5 mode
        Given the course has a Video component in "HTML5" mode
        And I have defined a downloadable non-english transcript for the video
        And I have uploaded a non-english transcript file to assets
        Then I see the correct non-english text in the captions
        And the non-english transcript downloads correctly
        """
        data = {'download_track': True, 'transcripts': {'zh': 'chinese_transcripts.srt'}}
        self.metadata = self.metadata_for_mode('html5', additional_data=data)
        self.assets.append('chinese_transcripts.srt')

        # go to video
        self.navigate_to_video()

        # check if we see "好 各位同学" text in the captions
        unicode_text = u"好 各位同学"
        self.assertIn(unicode_text, self.video.captions_text)

        # check if we can download transcript in "srt" format that has text "好 各位同学"
        unicode_text = u"好 各位同学"
        self.assertTrue(self.video.downloaded_transcript_contains_text('srt', unicode_text))

    def test_download_button_two_transcript_languages(self):
        """
        Scenario: Download button works correctly for multiple transcript languages in HTML5 mode
        Given the course has a Video component in "HTML5" mode
        And I have defined a downloadable non-english transcript for the video
        And I have defined english subtitles for the video
        Then I see the correct english text in the captions
        And the english transcript downloads correctly
        And I see the correct non-english text in the captions
        And the non-english transcript downloads correctly
        """
        self.assets.extend(['chinese_transcripts.srt', 'subs_3_yD_cEKoCk.srt.sjson'])
        data = {'download_track': True, 'transcripts': {'zh': 'chinese_transcripts.srt'}, 'sub': '3_yD_cEKoCk'}
        self.metadata = self.metadata_for_mode('html5', additional_data=data)

        # go to video
        self.navigate_to_video()

        # check if "Welcome to edX." text in the captions
        self.assertIn('Welcome to edX.', self.video.captions_text)

        self.video.wait_for_element_visibility('.transcript-end', 'Transcript has loaded')

        # check if we can download transcript in "srt" format that has text "Welcome to edX."
        self.assertTrue(self.video.downloaded_transcript_contains_text('srt', 'Welcome to edX.'))

        # select language with code "zh"
        self.assertTrue(self.video.select_language('zh'))

        # check if we see "好 各位同学" text in the captions
        unicode_text = u"好 各位同学"

        self.assertIn(unicode_text, self.video.captions_text)

        # Then I can download transcript in "srt" format that has text "好 各位同学"
        unicode_text = u"好 各位同学"
        self.assertTrue(self.video.downloaded_transcript_contains_text('srt', unicode_text))

    def test_cc_button_with_english_transcript(self):
        """
        Scenario: CC button works correctly with only english transcript in HTML5 mode
        Given the course has a Video component in "HTML5" mode
        And I have defined english subtitles for the video
        And I have uploaded an english transcript file to assets
        Then I see the correct text in the captions
        """
        self.assets.append('subs_3_yD_cEKoCk.srt.sjson')
        data = {'sub': '3_yD_cEKoCk'}
        self.metadata = self.metadata_for_mode('html5', additional_data=data)

        # go to video
        self.navigate_to_video()

        # make sure captions are opened
        self.video.show_captions()

        # check if we see "Welcome to edX." text in the captions
        self.assertIn("Welcome to edX.", self.video.captions_text)

    def test_cc_button_wo_english_transcript(self):
        """
        Scenario: CC button works correctly w/o english transcript in HTML5 mode
        Given the course has a Video component in "HTML5" mode
        And I have defined a non-english transcript for the video
        And I have uploaded a non-english transcript file to assets
        Then I see the correct text in the captions
        """
        self.assets.append('chinese_transcripts.srt')
        data = {'transcripts': {'zh': 'chinese_transcripts.srt'}}
        self.metadata = self.metadata_for_mode('html5', additional_data=data)

        # go to video
        self.navigate_to_video()

        # make sure captions are opened
        self.video.show_captions()

        # check if we see "好 各位同学" text in the captions
        unicode_text = u"好 各位同学"
        self.assertIn(unicode_text, self.video.captions_text)

    def test_video_rendering(self):
        """
        Scenario: Video component is fully rendered in the LMS in HTML5 mode
        Given the course has a Video component in "HTML5" mode
        Then the video has rendered in "HTML5" mode
        And video sources are correct
        """
        self.metadata = self.metadata_for_mode('html5')

        self.navigate_to_video()

        self.assertTrue(self.video.is_video_rendered('html5'))

        self.assertTrue(all([source in HTML5_SOURCES for source in self.video.sources]))


@attr(shard=13)
class YouTubeQualityTest(VideoBaseTest):
    """ Test YouTube Video Quality Button """

    @skip_if_browser('firefox')
    def test_quality_button_visibility(self):
        """
        Scenario: Quality button appears on play.

        Given the course has a Video component in "Youtube" mode
        Then I see video button "quality" is hidden
        And I click video button "play"
        Then I see video button "quality" is visible
        """
        self.navigate_to_video()

        self.assertFalse(self.video.is_quality_button_visible)

        self.video.click_player_button('play')

        self.video.wait_for(lambda: self.video.is_quality_button_visible, 'waiting for quality button to appear')

    @skip_if_browser('firefox')
    def test_quality_button_works_correctly(self):
        """
        Scenario: Quality button works correctly.

        Given the course has a Video component in "Youtube" mode
        And I click video button "play"
        And I see video button "quality" is inactive
        And I click video button "quality"
        Then I see video button "quality" is active
        """
        self.navigate_to_video()

        self.video.click_player_button('play')

        self.video.wait_for(lambda: self.video.is_quality_button_visible, 'waiting for quality button to appear')

        self.assertFalse(self.video.is_quality_button_active)

        self.video.click_player_button('quality')

        self.video.wait_for(lambda: self.video.is_quality_button_active, 'waiting for quality button activation')


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


@attr(shard=11)
class VideoPlayOrderTest(VideoBaseTest):
    """
    Test video play order with multiple videos

    Priority of video formats is:
        * Youtube
        * HLS
        * HTML5
    """

    def setUp(self):
        super(VideoPlayOrderTest, self).setUp()

    def test_play_youtube_video(self):
        """
        Scenario: Correct video is played when we have different video formats.

        Given the course has a Video component with Youtube, HTML5 and HLS sources available.
        When I view the Video component
        Then it should play the Youtube video
        """
        additional_data = {'youtube_id_1_0': 'b7xgknqkQk8'}
        self.metadata = self.metadata_for_mode('html5_and_hls', additional_data=additional_data)
        self.navigate_to_video()

        # Verify that the video is youtube
        self.assertTrue(self.video.is_video_rendered('youtube'))

    def test_play_html5_hls_video(self):
        """
        Scenario: HLS video is played when we have HTML5 and HLS video formats only.

        Given the course has a Video component with HTML5 and HLS sources available.
        When I view the Video component
        Then it should play the HLS video
        """
        self.metadata = self.metadata_for_mode('html5_and_hls')
        self.navigate_to_video()

        # Verify that the video is hls
        self.assertTrue(self.video.is_video_rendered('hls'))


@attr(shard=11)
class HLSVideoTest(VideoBaseTest):
    """
    Tests related to HLS video
    """

    def test_video_play_pause(self):
        """
        Scenario: Video play and pause is working as expected for hls video

        Given the course has a Video component with only HLS source available.
        When I view the Video component
        Then I can see play and pause are working as expected
        """
        self.metadata = self.metadata_for_mode('hls')
        self.navigate_to_video()

        self.video.click_player_button('play')
        self.assertIn(self.video.state, ['buffering', 'playing'])
        self.video.click_player_button('pause')
        self.assertEqual(self.video.state, 'pause')

    def test_video_seek(self):
        """
        Scenario: Video seek is working as expected for hls video

        Given the course has a Video component with only HLS source available.
        When I view the Video component
        Then I can seek the video as expected
        """
        self.metadata = self.metadata_for_mode('hls')
        self.navigate_to_video()

        self.video.click_player_button('play')
        self.video.wait_for_position('0:02')
        self.video.click_player_button('pause')
        self.video.seek('0:05')
        self.assertEqual(self.video.position, '0:05')

    def test_video_download_link(self):
        """
        Scenario: Correct video url is selected for download

        Given the course has a Video component with Youtube, HTML5 and HLS sources available.
        When I view the Video component
        Then HTML5 video download url is available
        """
        self.metadata = self.metadata_for_mode('html5_and_hls', additional_data={'download_video': True})
        self.navigate_to_video()

        # Verify that the video download url is correct
        self.assertEqual(self.video.video_download_url, HTML5_SOURCES[0])

    def test_no_video_download_link_for_hls(self):
        """
        Scenario: Video download url is not shown for hls videos

        Given the course has a Video component with only HLS sources available.
        When I view the Video component
        Then there is no video download url shown
        """
        additional_data = {'download_video': True}
        self.metadata = self.metadata_for_mode('hls', additional_data=additional_data)
        self.navigate_to_video()

        # Verify that the video download url is not shown
        self.assertEqual(self.video.video_download_url, None)

    def test_hls_video_with_youtube_delayed_response_time(self):
        """
        Scenario: HLS video is rendered when the YouTube API response time is slow
        Given the YouTube server response time is greater than 1.5 seconds
        And the course has a Video component with Youtube, HTML5 and HLS sources available
        Then the HLS video is rendered
        """
        # configure youtube server
        self.youtube_configuration.update({
            'time_to_response': 7.0,
        })

        self.metadata = self.metadata_for_mode('html5_and_hls', additional_data={'youtube_id_1_0': 'b7xgknqkQk8'})
        self.navigate_to_video()
        self.assertTrue(self.video.is_video_rendered('hls'))

    def test_hls_video_with_transcript(self):
        """
        Scenario: Transcript work as expected for an HLS video

        Given the course has a Video component with "HLS" video only
        And I have defined a transcript for the video
        Then I see the correct text in the captions for transcript
        Then I play, pause and seek to 0:00
        Then I click on a caption line
        And video position should be updated accordingly
        Then I change video position
        And video caption should be updated accordingly
        """
        data = {'transcripts': {'zh': 'transcript.srt'}}
        self.metadata = self.metadata_for_mode('hls', additional_data=data)
        self.assets.append('transcript.srt')
        self.navigate_to_video()

        self.assertIn("Hi, edX welcomes you0.", self.video.captions_text)

        # This is required to load the video
        self.video.click_player_button('play')
        # Below 2 steps are required to test the caption line click scenario
        self.video.click_player_button('pause')
        self.video.seek('0:00')

        for line_no in range(5):
            self.video.click_transcript_line(line_no=line_no)
            self.video.wait_for_position(u'0:0{}'.format(line_no))

        for line_no in range(5):
            self.video.seek(u'0:0{}'.format(line_no))
            self.assertEqual(self.video.active_caption_text, u'Hi, edX welcomes you{}.'.format(line_no))
