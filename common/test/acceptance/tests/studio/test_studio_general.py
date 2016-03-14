"""
Acceptance tests for Studio.
"""

from unittest import skip
from bok_choy.web_app_test import WebAppTest

from ...pages.studio.asset_index import AssetIndexPage
from ...pages.studio.auto_auth import AutoAuthPage
from ...pages.studio.course_info import CourseUpdatesPage
from ...pages.studio.edit_tabs import PagesPage
from ...pages.studio.import_export import ExportCoursePage, ImportCoursePage
from ...pages.studio.howitworks import HowitworksPage
from ...pages.studio.index import DashboardPage
from ...pages.studio.login import LoginPage
from ...pages.studio.users import CourseTeamPage
from ...pages.studio.overview import CourseOutlinePage
from ...pages.studio.settings import SettingsPage
from ...pages.studio.settings_advanced import AdvancedSettingsPage
from ...pages.studio.settings_graders import GradingPage
from ...pages.studio.signup import SignupPage
from ...pages.studio.textbooks import TextbooksPage
from ...fixtures.course import XBlockFixtureDesc

from base_studio_test import StudioCourseTest


class LoggedOutTest(WebAppTest):
    """
    Smoke test for pages in Studio that are visible when logged out.
    """

    def setUp(self):
        super(LoggedOutTest, self).setUp()
        self.pages = [LoginPage(self.browser), HowitworksPage(self.browser), SignupPage(self.browser)]

    def test_page_existence(self):
        """
        Make sure that all the pages are accessible.
        Rather than fire up the browser just to check each url,
        do them all sequentially in this testcase.
        """
        for page in self.pages:
            page.visit()


class LoggedInPagesTest(WebAppTest):
    """
    Tests that verify the pages in Studio that you can get to when logged
    in and do not have a course yet.
    """

    def setUp(self):
        super(LoggedInPagesTest, self).setUp()
        self.auth_page = AutoAuthPage(self.browser, staff=True)
        self.dashboard_page = DashboardPage(self.browser)

    def test_dashboard_no_courses(self):
        """
        Make sure that you can get to the dashboard page without a course.
        """
        self.auth_page.visit()
        self.dashboard_page.visit()


class CoursePagesTest(StudioCourseTest):
    """
    Tests that verify the pages in Studio that you can get to when logged
    in and have a course.
    """

    COURSE_ID_SEPARATOR = "."

    def setUp(self):
        """
        Install a course with no content using a fixture.
        """
        super(CoursePagesTest, self).setUp()

        self.pages = [
            clz(self.browser, self.course_info['org'], self.course_info['number'], self.course_info['run'])
            for clz in [
                AssetIndexPage, CourseUpdatesPage,
                PagesPage, ExportCoursePage, ImportCoursePage, CourseTeamPage, CourseOutlinePage, SettingsPage,
                AdvancedSettingsPage, GradingPage, TextbooksPage
            ]
        ]

    def test_page_redirect(self):
        """
        /course/ is the base URL for all courses, but by itself, it should
        redirect to /home/.
        """
        self.dashboard_page = DashboardPage(self.browser)  # pylint: disable=attribute-defined-outside-init
        self.dashboard_page.visit()
        self.assertEqual(self.browser.current_url.strip('/').rsplit('/')[-1], 'home')

    @skip('Intermittently failing with Page not found error for Assets. TE-418')
    def test_page_existence(self):
        """
        Make sure that all these pages are accessible once you have a course.
        Rather than fire up the browser just to check each url,
        do them all sequentially in this testcase.
        """

        # In the real workflow you will be at the dashboard page
        # after you log in. This test was intermittently failing on the
        # first (asset) page load with a 404.
        # Not exactly sure why, so adding in a visit
        # to the dashboard page here to replicate the usual flow.
        self.dashboard_page = DashboardPage(self.browser)
        self.dashboard_page.visit()

        # Verify that each page is available
        for page in self.pages:
            page.visit()


class DiscussionPreviewTest(StudioCourseTest):
    """
    Tests that Inline Discussions are rendered with a custom preview in Studio
    """

    def setUp(self):
        super(DiscussionPreviewTest, self).setUp()
        cop = CourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )
        cop.visit()
        self.unit = cop.section('Test Section').subsection('Test Subsection').expand_subsection().unit('Test Unit')
        self.unit.go_to()

    def populate_course_fixture(self, course_fixture):
        """
        Return a test course fixture containing a discussion component.
        """
        course_fixture.add_children(
            XBlockFixtureDesc("chapter", "Test Section").add_children(
                XBlockFixtureDesc("sequential", "Test Subsection").add_children(
                    XBlockFixtureDesc("vertical", "Test Unit").add_children(
                        XBlockFixtureDesc(
                            "discussion",
                            "Test Discussion",
                        )
                    )
                )
            )
        )

    def test_is_preview(self):
        """
        Ensure that the preview version of the discussion is rendered.
        """
        self.assertTrue(self.unit.q(css=".discussion-preview").present)
        self.assertFalse(self.unit.q(css=".discussion-show").present)
