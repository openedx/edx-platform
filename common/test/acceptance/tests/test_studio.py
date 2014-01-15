"""
Acceptance tests for Studio.
"""
from bok_choy.web_app_test import WebAppTest

from ..edxapp_pages.studio.asset_index import AssetIndexPage
from ..edxapp_pages.studio.auto_auth import AutoAuthPage
from ..edxapp_pages.studio.checklists import ChecklistsPage
from ..edxapp_pages.studio.course_import import ImportPage
from ..edxapp_pages.studio.course_info import CourseUpdatesPage
from ..edxapp_pages.studio.edit_tabs import StaticPagesPage
from ..edxapp_pages.studio.export import ExportPage
from ..edxapp_pages.studio.howitworks import HowitworksPage
from ..edxapp_pages.studio.index import DashboardPage
from ..edxapp_pages.studio.login import LoginPage
from ..edxapp_pages.studio.manage_users import CourseTeamPage
from ..edxapp_pages.studio.overview import CourseOutlinePage
from ..edxapp_pages.studio.settings import SettingsPage
from ..edxapp_pages.studio.settings_advanced import AdvancedSettingsPage
from ..edxapp_pages.studio.settings_graders import GradingPage
from ..edxapp_pages.studio.signup import SignupPage
from ..edxapp_pages.studio.textbooks import TextbooksPage
from ..fixtures.course import CourseFixture


class LoggedOutTest(WebAppTest):
    """
    Smoke test for pages in Studio that are visible when logged out.
    """

    @property
    def page_object_classes(self):
        return [LoginPage, HowitworksPage, SignupPage]

    def test_page_existence(self):
        """
        Make sure that all the pages are accessible.
        Rather than fire up the browser just to check each url,
        do them all sequentially in this testcase.
        """
        for page in ['login', 'howitworks', 'signup']:
            self.ui.visit('studio.{0}'.format(page))


class LoggedInPagesTest(WebAppTest):
    """
    Tests that verify the pages in Studio that you can get to when logged
    in and do not have a course yet.
    """
    @property
    def page_object_classes(self):
        return [AutoAuthPage, DashboardPage]

    def test_dashboard_no_courses(self):
        """
        Make sure that you can get to the dashboard page without a course.
        """
        self.ui.visit('studio.auto_auth', staff=True)
        self.ui.visit('studio.dashboard')


class CoursePagesTest(WebAppTest):
    """
    Tests that verify the pages in Studio that you can get to when logged
    in and have a course.
    """

    def setUp(self):
        """
        Create a unique identifier for the course used in this test.
        """
        # Define a unique course identifier
        self.course_info = {
            'org': 'test_org',
            'number': '101',
            'run': 'test_' + self.unique_id,
            'display_name': 'Test Course ' + self.unique_id
        }

        # Ensure that the superclass sets up
        super(CoursePagesTest, self).setUp()

    @property
    def page_object_classes(self):
        return [
            AutoAuthPage, AssetIndexPage, ChecklistsPage, ImportPage, CourseUpdatesPage,
            StaticPagesPage, ExportPage, CourseTeamPage, CourseOutlinePage,
            SettingsPage, AdvancedSettingsPage, GradingPage, TextbooksPage
        ]

    @property
    def fixtures(self):
        super_fixtures = super(CoursePagesTest, self).fixtures
        course_fix = CourseFixture(
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run'],
            self.course_info['display_name']
        )
        return set(super_fixtures + [course_fix])

    def test_page_existence(self):
        """
        Make sure that all these pages are accessible once you have a course.
        Rather than fire up the browser just to check each url,
        do them all sequentially in this testcase.
        """
        pages = [
            'uploads', 'checklists', 'import', 'updates', 'tabs', 'export',
            'team', 'outline', 'settings', 'advanced', 'grading', 'textbooks'
        ]

        # Log in
        self.ui.visit('studio.auto_auth', staff=True)

        course_id = '{org}.{number}.{run}'.format(**self.course_info)
        for page in pages:
            self.ui.visit('studio.{0}'.format(page), course_id=course_id)
