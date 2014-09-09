# -*- coding: utf-8 -*-

"""
Acceptance tests for CMS Video Module.
"""
from nose.plugins.attrib import attr
from unittest import skipIf
from ...pages.studio.auto_auth import AutoAuthPage
from ...pages.studio.overview import CourseOutlinePage
from ...pages.studio.video.video import VideoComponentPage
from ...fixtures.course import CourseFixture, XBlockFixtureDesc
from ..helpers import UniqueCourseTest, is_youtube_available, YouTubeStubConfig


@skipIf(is_youtube_available() is False, 'YouTube is not available!')
class CMSVideoBaseTest(UniqueCourseTest):
    """
    CMS Video Module Base Test Class
    """

    def setUp(self):
        """
        Initialization of pages and course fixture for tests
        """
        super(CMSVideoBaseTest, self).setUp()

        self.video = VideoComponentPage(self.browser)

        # This will be initialized later
        self.unit_page = None

        self.outline = CourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        self.course_fixture = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )

        self.assets = []

    def _install_course_fixture(self):
        """
        Prepare for tests by creating a course with a section, subsection, and unit.
        Performs the following:
            Create a course with a section, subsection, and unit
            Create a user and make that user a course author
            Log the user into studio
        """
        if self.assets:
            self.course_fixture.add_asset(self.assets)

        # Create course with Video component
        self.course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit').add_children(
                        XBlockFixtureDesc('video', 'Video')
                    )
                )
            )
        ).install()

        # Auto login and register the course
        AutoAuthPage(
            self.browser,
            staff=False,
            username=self.course_fixture.user.get('username'),
            email=self.course_fixture.user.get('email'),
            password=self.course_fixture.user.get('password')
        ).visit()

    def _navigate_to_course_unit_page(self):
        """
        Open the course from the dashboard and expand the section and subsection and click on the Unit link
        The end result is the page where the user is editing the newly created unit
        """
        # Visit Course Outline page
        self.outline.visit()

        # Visit Unit page
        self.unit_page = self.outline.section('Test Section').subsection('Test Subsection').toggle_expand().unit(
            'Test Unit').go_to()

        self.video.wait_for_video_component_render()

    def navigate_to_course_unit(self):
        """
        Install the course with required components and navigate to course unit page
        """
        self._install_course_fixture()
        self._navigate_to_course_unit_page()

    def edit_component(self, xblock_index=1):
        """
        Open component Edit Dialog for first component on page.

        Arguments:
            xblock_index: number starting from 1 (0th entry is the unit page itself)
        """
        self.unit_page.xblocks[xblock_index].edit()

    def open_advanced_tab(self):
        """
        Open components advanced tab.
        """
        # The 0th entry is the unit page itself.
        self.unit_page.xblocks[1].open_advanced_tab()

    def open_basic_tab(self):
        """
        Open components basic tab.
        """
        # The 0th entry is the unit page itself.
        self.unit_page.xblocks[1].open_basic_tab()

    def save_unit_settings(self):
        """
        Save component settings.
        """
        # The 0th entry is the unit page itself.
        self.unit_page.xblocks[1].save_settings()


@attr('shard_2')
class CMSVideoTest(CMSVideoBaseTest):
    """
    CMS Video Test Class
    """

    def setUp(self):
        super(CMSVideoTest, self).setUp()

        self.addCleanup(YouTubeStubConfig.reset)

    def _create_course_unit(self, youtube_stub_config=None, subtitles=False):
        """
        Create a Studio Video Course Unit and Navigate to it.

        Arguments:
            youtube_stub_config (dict)
            subtitles (bool)

        """
        if youtube_stub_config:
            YouTubeStubConfig.configure(youtube_stub_config)

        if subtitles:
            self.assets.append('subs_OEoXaMPEzfM.srt.sjson')

        self.navigate_to_course_unit()

    def _create_video(self):
        """
        Create Xblock Video Component.
        """
        self.video.create_video()

        video_xblocks = self.video.xblocks()

        # Total video xblock components count should be equals to 2
        # Why 2? One video component is created by default for each test. Please see
        # test_studio_video_module.py:CMSVideoTest._create_course_unit
        # And we are creating second video component here.
        self.assertTrue(video_xblocks == 2)

    def test_youtube_stub_proxy(self):
        """
        Scenario: YouTube stub server proxies YouTube API correctly
        Given youtube stub server proxies YouTube API
        And I have created a Video component
        Then I can see video button "play"
        And I click video button "play"
        Then I can see video button "pause"
        """
        self._create_course_unit(youtube_stub_config={'youtube_api_blocked': False})

        self.assertTrue(self.video.is_button_shown('play'))
        self.video.click_player_button('play')
        self.assertTrue(self.video.is_button_shown('pause'))

    def test_youtube_stub_blocks_youtube_api(self):
        """
        Scenario: YouTube stub server can block YouTube API
        Given youtube stub server blocks YouTube API
        And I have created a Video component
        Then I do not see video button "play"
        """
        self._create_course_unit(youtube_stub_config={'youtube_api_blocked': True})

        self.assertFalse(self.video.is_button_shown('play'))

    def test_autoplay_is_disabled(self):
        """
        Scenario: Autoplay is disabled in Studio
        Given I have created a Video component
        Then when I view the video it does not have autoplay enabled
        """
        self._create_course_unit()

        self.assertFalse(self.video.is_autoplay_enabled)

    def test_video_creation_takes_single_click(self):
        """
        Scenario: Creating a video takes a single click
        And creating a video takes a single click
        """
        self._create_course_unit()

        # This will create a video by doing a single click and then ensure that video is created
        self._create_video()

    def test_captions_hidden_correctly(self):
        """
        Scenario: Captions are hidden correctly
        Given I have created a Video component with subtitles
        And I have hidden captions
        Then when I view the video it does not show the captions
        """
        self._create_course_unit(subtitles=True)

        self.video.hide_captions()

        self.assertFalse(self.video.is_captions_visible())

    def test_video_controls_shown_correctly(self):
        """
        Scenario: Video controls for all videos show correctly
        Given I have created two Video components
        And first is private video
        When I reload the page
        Then video controls for all videos are visible
        """
        self._create_course_unit(youtube_stub_config={'youtube_api_private_video': True})
        self.video.create_video()

        # change id of first default video
        self.edit_component(1)
        self.open_advanced_tab()
        self.video.set_field_value('YouTube ID', 'sampleid123')
        self.save_unit_settings()

        # again open unit page and check that video controls show for both videos
        self._navigate_to_course_unit_page()
        self.assertTrue(self.video.is_controls_visible())

    def test_captions_shown_correctly(self):
        """
        Scenario: Captions are shown correctly
        Given I have created a Video component with subtitles
        Then when I view the video it does show the captions
        """
        self._create_course_unit(subtitles=True)

        self.assertTrue(self.video.is_captions_visible())

    def test_captions_toggling(self):
        """
        Scenario: Captions are toggled correctly
        Given I have created a Video component with subtitles
        And I have toggled captions
        Then when I view the video it does show the captions
        """
        self._create_course_unit(subtitles=True)

        self.video.click_player_button('CC')

        self.assertFalse(self.video.is_captions_visible())

        self.video.click_player_button('CC')

        self.assertTrue(self.video.is_captions_visible())

    def test_caption_line_focus(self):
        """
        Scenario: When enter key is pressed on a caption, an outline shows around it
        Given I have created a Video component with subtitles
        And Make sure captions are opened
        Then I focus on first caption line
        And I see first caption line has focused
        """
        self._create_course_unit(subtitles=True)

        self.video.show_captions()

        self.video.focus_caption_line(1)

        self.assertTrue(self.video.is_caption_line_focused(1))

    def test_slider_range_works(self):
        """
        Scenario: When start and end times are specified, a range on slider is shown
        Given I have created a Video component with subtitles
        And Make sure captions are closed
        And I edit the component
        And I open tab "Advanced"
        And I set value "00:00:12" to the field "Video Start Time"
        And I set value "00:00:24" to the field "Video Stop Time"
        And I save changes
        And I click video button "play"
        Then I see a range on slider
        """
        self._create_course_unit(subtitles=True)

        self.video.hide_captions()

        self.edit_component()

        self.open_advanced_tab()

        self.video.set_field_value('Video Start Time', '00:00:12')

        self.video.set_field_value('Video Stop Time', '00:00:24')

        self.save_unit_settings()

        self.video.click_player_button('play')

        self.assertTrue(self.video.is_slider_range_visible)
