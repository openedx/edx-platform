"""
Acceptance tests for Studio.
"""
from unittest import skip

from bok_choy.web_app_test import WebAppTest

from ..pages.studio.asset_index import AssetIndexPage
from ..pages.studio.auto_auth import AutoAuthPage
from ..pages.studio.checklists import ChecklistsPage
from ..pages.studio.course_import import ImportPage
from ..pages.studio.course_info import CourseUpdatesPage
from ..pages.studio.edit_tabs import PagesPage
from ..pages.studio.export import ExportPage
from ..pages.studio.howitworks import HowitworksPage
from ..pages.studio.index import DashboardPage
from ..pages.studio.login import LoginPage
from ..pages.studio.manage_users import CourseTeamPage
from ..pages.studio.overview import CourseOutlinePage
from ..pages.studio.settings import SettingsPage
from ..pages.studio.settings_advanced import AdvancedSettingsPage
from ..pages.studio.settings_graders import GradingPage
from ..pages.studio.signup import SignupPage
from ..pages.studio.textbooks import TextbooksPage
from ..pages.xblock.acid import AcidView
from ..fixtures.course import CourseFixture, XBlockFixtureDesc

from .helpers import UniqueCourseTest, load_data_str


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


class CoursePagesTest(UniqueCourseTest):
    """
    Tests that verify the pages in Studio that you can get to when logged
    in and have a course.
    """

    COURSE_ID_SEPARATOR = "."

    def setUp(self):
        """
        Install a course with no content using a fixture.
        """
        super(UniqueCourseTest, self).setUp()

        CourseFixture(
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run'],
            self.course_info['display_name']
        ).install()

        self.auth_page = AutoAuthPage(self.browser, staff=True)

        self.pages = [
            clz(self.browser, self.course_info['org'], self.course_info['number'], self.course_info['run'])
            for clz in [
                AssetIndexPage, ChecklistsPage, ImportPage, CourseUpdatesPage,
                PagesPage, ExportPage, CourseTeamPage, CourseOutlinePage, SettingsPage,
                AdvancedSettingsPage, GradingPage, TextbooksPage
            ]
        ]

    def test_page_existence(self):
        """
        Make sure that all these pages are accessible once you have a course.
        Rather than fire up the browser just to check each url,
        do them all sequentially in this testcase.
        """
        # Log in
        self.auth_page.visit()

        # Verify that each page is available
        for page in self.pages:
            page.visit()


class XBlockAcidBase(WebAppTest):
    """
    Base class for tests that verify that XBlock integration is working correctly
    """
    __test__ = False

    def setUp(self):
        """
        Create a unique identifier for the course used in this test.
        """
        # Ensure that the superclass sets up
        super(XBlockAcidBase, self).setUp()

        # Define a unique course identifier
        self.course_info = {
            'org': 'test_org',
            'number': 'course_' + self.unique_id[:5],
            'run': 'test_' + self.unique_id,
            'display_name': 'Test Course ' + self.unique_id
        }

        self.auth_page = AutoAuthPage(self.browser, staff=True)
        self.outline = CourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        self.course_id = '{org}.{number}.{run}'.format(**self.course_info)

        self.setup_fixtures()

        self.auth_page.visit()

    def validate_acid_block_preview(self, acid_block):
        """
        Validate the Acid Block's preview
        """
        self.assertTrue(acid_block.init_fn_passed)
        self.assertTrue(acid_block.resource_url_passed)
        self.assertTrue(acid_block.scope_passed('user_state'))
        self.assertTrue(acid_block.scope_passed('user_state_summary'))
        self.assertTrue(acid_block.scope_passed('preferences'))
        self.assertTrue(acid_block.scope_passed('user_info'))

    def test_acid_block_preview(self):
        """
        Verify that all expected acid block tests pass in studio preview
        """

        self.outline.visit()
        subsection = self.outline.section('Test Section').subsection('Test Subsection')
        unit = subsection.toggle_expand().unit('Test Unit').go_to()

        acid_block = AcidView(self.browser, unit.components[0].preview_selector)
        self.validate_acid_block_preview(acid_block)

    @skip('Temporarily diabling because it is failing in Jenkins. TE-369')
    def test_acid_block_editor(self):
        """
        Verify that all expected acid block tests pass in studio editor
        """

        self.outline.visit()
        subsection = self.outline.section('Test Section').subsection('Test Subsection')
        unit = subsection.toggle_expand().unit('Test Unit').go_to()

        unit.edit_draft()

        acid_block = AcidView(self.browser, unit.components[0].edit().editor_selector)
        self.assertTrue(acid_block.init_fn_passed)
        self.assertTrue(acid_block.resource_url_passed)
        self.assertTrue(acid_block.scope_passed('content'))
        self.assertTrue(acid_block.scope_passed('settings'))


class XBlockAcidNoChildTest(XBlockAcidBase):
    """
    Tests of an AcidBlock with no children
    """
    __test__ = True

    def setup_fixtures(self):

        course_fix = CourseFixture(
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run'],
            self.course_info['display_name']
        )

        course_fix.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit').add_children(
                        XBlockFixtureDesc('acid', 'Acid Block')
                    )
                )
            )
        ).install()


class XBlockAcidParentBase(XBlockAcidBase):
    """
    Base class for tests that verify that parent XBlock integration is working correctly
    """
    __test__ = False

    def validate_acid_block_preview(self, acid_block):
        super(XBlockAcidParentBase, self).validate_acid_block_preview(acid_block)
        self.assertTrue(acid_block.child_tests_passed)

    @skip('Intermittently failing, needs a better page definition that waits until the unit is fully rendered')
    def test_acid_block_preview(self):
        """
        Verify that all expected acid block tests pass in studio preview
        """

        self.outline.visit()
        subsection = self.outline.section('Test Section').subsection('Test Subsection')
        unit = subsection.toggle_expand().unit('Test Unit').go_to()
        container = unit.components[0].go_to_container()

        acid_block = AcidView(self.browser, container.xblocks[0].preview_selector)
        self.validate_acid_block_preview(acid_block)

    @skip('This will fail until the container page supports editing')
    def test_acid_block_editor(self):
        super(XBlockAcidParentBase, self).test_acid_block_editor()


class XBlockAcidEmptyParentTest(XBlockAcidParentBase):
    """
    Tests of an AcidBlock with children
    """
    __test__ = True

    def setup_fixtures(self):

        course_fix = CourseFixture(
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run'],
            self.course_info['display_name']
        )

        course_fix.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit').add_children(
                        XBlockFixtureDesc('acid_parent', 'Acid Parent Block').add_children(
                        )
                    )
                )
            )
        ).install()


class XBlockAcidChildTest(XBlockAcidParentBase):
    """
    Tests of an AcidBlock with children
    """
    __test__ = True

    def setup_fixtures(self):

        course_fix = CourseFixture(
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run'],
            self.course_info['display_name']
        )

        course_fix.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit').add_children(
                        XBlockFixtureDesc('acid_parent', 'Acid Parent Block').add_children(
                            XBlockFixtureDesc('acid', 'First Acid Child', metadata={'name': 'first'}),
                            XBlockFixtureDesc('acid', 'Second Acid Child', metadata={'name': 'second'}),
                            XBlockFixtureDesc('html', 'Html Child', data="<html>Contents</html>"),
                        )
                    )
                )
            )
        ).install()

    @skip('This will fail until we fix support of children in pure XBlocks')
    def test_acid_block_preview(self):
        super(XBlockAcidChildTest, self).test_acid_block_preview()

    @skip('This will fail until we fix support of children in pure XBlocks')
    def test_acid_block_editor(self):
        super(XBlockAcidChildTest, self).test_acid_block_editor()
