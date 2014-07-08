# -*- coding: utf-8 -*-

"""
Acceptance tests for CMS Video Module.
"""

from unittest import skipIf
from ...pages.studio.auto_auth import AutoAuthPage
from ...pages.studio.overview import CourseOutlinePage
from ...pages.studio.video.video import VidoComponentPage
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

        self.video = VidoComponentPage(self.browser)

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

    def _install_course_fixture(self):
        """
        Prepare for tests by creating a course with a section, subsection, and unit.
        Performs the following:
            Create a course with a section, subsection, and unit
            Create a user and make that user a course author
            Log the user into studio
        """

        # Create course with Video component
        self.course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc("vertical", "Test Unit").add_children(
                        XBlockFixtureDesc('video', 'Video'),
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

    def edit_component(self):
        """
        Make component editable and open components Edit Dialog.

        Arguments:
            handout_filename (str): handout file name to be uploaded
            save_settings (bool): save settings or not

        """
        self.unit_page.set_unit_visibility('private')
        self.unit_page.components[0].edit()

    def open_advanced_tab(self):
        """
        Open components advanced tab.
        """
        self.unit_page.components[0].open_advanced_tab()

    def save_unit_settings(self):
        """
        Save component settings.
        """
        self.unit_page.components[0].save_settings()


class CMSVideoTest(CMSVideoBaseTest):
    """
    CMS Video Test Class
    """

    def setUp(self):
        super(CMSVideoTest, self).setUp()

    def tearDown(self):
        YouTubeStubConfig.reset()

    def _create_course_unit(self, youtube_stub_config=None):
        """
        Create CMS Video Course Unit and Navigates to it.

        Arguments:
            youtube_stub_config (dict)

        """
        if youtube_stub_config:
            YouTubeStubConfig.configure(youtube_stub_config)

        self.navigate_to_course_unit()

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
        And I wait for "3" seconds
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

        self.assertFalse(self.video.is_autoplay_enabled())
