"""
Test the Studio help links.
"""

from flaky import flaky
from bok_choy.web_app_test import WebAppTest
from unittest import skip

from common.test.acceptance.fixtures.course import XBlockFixtureDesc
from common.test.acceptance.tests.studio.base_studio_test import StudioCourseTest, ContainerBase
from common.test.acceptance.pages.studio.index import DashboardPage, DashboardPageWithPrograms
from common.test.acceptance.pages.studio.utils import click_studio_help, studio_help_links
from common.test.acceptance.pages.studio.index import IndexPage, HomePage
from common.test.acceptance.tests.studio.base_studio_test import StudioLibraryTest
from common.test.acceptance.pages.studio.course_info import CourseUpdatesPage
from common.test.acceptance.pages.studio.utils import click_css
from common.test.acceptance.pages.studio.library import LibraryPage
from common.test.acceptance.pages.studio.users import LibraryUsersPage
from common.test.acceptance.pages.studio.overview import CourseOutlinePage
from common.test.acceptance.pages.studio.asset_index import AssetIndexPage
from common.test.acceptance.pages.studio.edit_tabs import PagesPage
from common.test.acceptance.pages.studio.textbook_upload import TextbookUploadPage
from common.test.acceptance.pages.studio.settings import SettingsPage
from common.test.acceptance.pages.studio.settings_graders import GradingPage
from common.test.acceptance.pages.studio.settings_group_configurations import GroupConfigurationsPage
from common.test.acceptance.pages.studio.settings_advanced import AdvancedSettingsPage
from common.test.acceptance.pages.studio.settings_certificates import CertificatesPage
from common.test.acceptance.pages.studio.import_export import ExportCoursePage, ImportCoursePage
from common.test.acceptance.pages.studio.users import CourseTeamPage
from common.test.acceptance.fixtures.programs import ProgramsConfigMixin
from common.test.acceptance.tests.helpers import (
    assert_nav_help_link,
    assert_side_bar_help_link
)
from common.test.acceptance.pages.studio.import_export import ExportLibraryPage, ImportLibraryPage
from common.test.acceptance.pages.studio.auto_auth import AutoAuthPage


class StudioHelpTest(StudioCourseTest):
    """Tests for Studio help."""

    @flaky  # TODO: TNL-4954
    def test_studio_help_links(self):
        """Test that the help links are present and have the correct content."""
        page = DashboardPage(self.browser)
        page.visit()
        click_studio_help(page)
        links = studio_help_links(page)
        expected_links = [{
            'href': u'http://docs.edx.org/',
            'text': u'edX Documentation',
            'sr_text': u'Access documentation on http://docs.edx.org'
        }, {
            'href': u'https://open.edx.org/',
            'text': u'Open edX Portal',
            'sr_text': u'Access the Open edX Portal'
        }, {
            'href': u'https://www.edx.org/course/overview-creating-edx-course-edx-edx101#.VO4eaLPF-n1',
            'text': u'Enroll in edX101',
            'sr_text': u'Enroll in edX101: Overview of Creating an edX Course'
        }, {
            'href': u'https://www.edx.org/course/creating-course-edx-studio-edx-studiox',
            'text': u'Enroll in StudioX',
            'sr_text': u'Enroll in StudioX: Creating a Course with edX Studio'
        }, {
            'href': u'mailto:partner-support@example.com',
            'text': u'Contact Us',
            'sr_text': 'Send an email to partner-support@example.com'
        }]
        for expected, actual in zip(expected_links, links):
            self.assertEqual(expected['href'], actual.get_attribute('href'))
            self.assertEqual(expected['text'], actual.text)
            self.assertEqual(
                expected['sr_text'],
                actual.find_element_by_xpath('following-sibling::span').text
            )


class SignInHelpTest(WebAppTest):
    """
    Tests help links on 'Sign In' page
    """
    def setUp(self):
        super(SignInHelpTest, self).setUp()
        self.index_page = IndexPage(self.browser)
        self.index_page.visit()

    def test_sign_in_nav_help(self):
        """
        Scenario: Help link in navigation bar is working on 'Sign In' page.
        Given that I am on the 'Sign In" page.
        And I want help about the sign in
        And I click the 'Help' in the navigation bar
        Then Help link should open.
        And help url should end with 'getting_started/get_started.html'
        """
        sign_in_page = self.index_page.click_sign_in()
        # The href we want to see in anchor help element.
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff/' \
               'en/latest/getting_started/get_started.html'

        # Assert that help link is correct.
        assert_nav_help_link(
            test=self,
            page=sign_in_page,
            href=href,
            signed_in=False
        )


class SignUpHelpTest(WebAppTest):
    """
    Tests help links on 'Sign Up' page.
    """
    def setUp(self):
        super(SignUpHelpTest, self).setUp()
        self.index_page = IndexPage(self.browser)
        self.index_page.visit()

    def test_sign_up_nav_help(self):
        """
        Scenario: Help link in navigation bar is working on 'Sign Up' page.
        Given that I am on the 'Sign Up" page.
        And I want help about the sign up
        And I click the 'Help' in the navigation bar
        Then Help link should open.
        And help url should end with 'getting_started/get_started.html'
        """
        sign_up_page = self.index_page.click_sign_up()
        # The href we want to see in anchor help element.
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff/' \
               'en/latest/getting_started/get_started.html'

        # Assert that help link is correct.
        assert_nav_help_link(
            test=self,
            page=sign_up_page,
            href=href,
            signed_in=False
        )


class HomeHelpTest(StudioCourseTest):
    """
    Tests help links on 'Home'(Courses tab) page.
    """
    def setUp(self):  # pylint: disable=arguments-differ
        super(HomeHelpTest, self).setUp()
        self.home_page = HomePage(self.browser)
        self.home_page.visit()

    def test_course_home_nav_help(self):
        """
        Scenario: Help link in navigation bar is working on 'Home'(Courses tab) page.
        Given that I am on the 'Home'(Courses tab) page.
        And I want help about the courses
        And I click the 'Help' in the navigation bar
        Then Help link should open.
        And help url should end with 'getting_started/get_started.html'
        """
        # The href we want to see in anchor help element.
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff/' \
               'en/latest/getting_started/get_started.html'

        # Assert that help link is correct.
        assert_nav_help_link(
            test=self,
            page=self.home_page,
            href=href
        )

    def test_course_home_side_bar_help(self):
        """
        Scenario: Help link in sidebar links is working on 'Home'(Courses tab) page.
        Given that I am on the 'Home'(Courses tab) page.
        And I want help about the courses
        And I click the 'Getting Started with edX Studio' in the sidebar links
        Then Help link should open.
        And help url should end with 'getting_started/get_started.html'
        """
        # The href we want to see in anchor help element.
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff/' \
               'en/latest/getting_started/get_started.html'

        # Assert that help link is correct.
        assert_side_bar_help_link(
            test=self,
            page=self.home_page,
            href=href,
            help_text='Getting Started with edX Studio',
            as_list_item=True
        )


class NewCourseHelpTest(WebAppTest):
    """
    Test help links while creating a new course.
    """
    def setUp(self):
        super(NewCourseHelpTest, self).setUp()
        self.auth_page = AutoAuthPage(self.browser, staff=True)
        self.dashboard_page = DashboardPage(self.browser)
        self.auth_page.visit()
        self.dashboard_page.visit()
        self.assertTrue(self.dashboard_page.new_course_button.present)
        self.dashboard_page.click_new_course_button()

    def test_course_create_nav_help(self):
        """
        Scenario: Help link in navigation bar is working on 'Create a New Course' page in the dashboard.
        Given that I am on the 'Create a New Course' page in the dashboard.
        And I want help about the process
        And I click the 'Help' in the navigation bar
        Then Help link should open.
        And help url should end with 'getting_started/get_started.html'
        """
        # The href we want to see in anchor help element.
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff' \
               '/en/latest/getting_started/get_started.html'

        # Assert that help link is correct.
        assert_nav_help_link(
            test=self,
            page=self.dashboard_page,
            href=href
        )

    def test_course_create_side_bar_help(self):
        """
        Scenario: Help link in sidebar links is working on 'Create a New Course' page in the dashboard.
        Given that I am on the 'Create a New Course' page in the dashboard.
        And I want help about the process
        And I click the 'Getting Started with edX Studio' in the sidebar links
        Then Help link should open.
        And help url should end with 'getting_started/get_started.html'
        """
        # The href we want to see in anchor help element.
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff/' \
               'en/latest/getting_started/get_started.html'

        # Assert that help link is correct.
        assert_side_bar_help_link(
            test=self,
            page=self.dashboard_page,
            href=href,
            help_text='Getting Started with edX Studio',
            as_list_item=True
        )


class NewLibraryHelpTest(WebAppTest):
    """
    Test help links while creating a new library
    """
    def setUp(self):
        super(NewLibraryHelpTest, self).setUp()
        self.auth_page = AutoAuthPage(self.browser, staff=True)
        self.dashboard_page = DashboardPage(self.browser)
        self.auth_page.visit()
        self.dashboard_page.visit()
        self.assertTrue(self.dashboard_page.has_new_library_button)
        self.dashboard_page.click_new_library()

    def test_library_create_nav_help(self):
        """
        Scenario: Help link in navigation bar is working on 'Create a New Library' page in the dashboard.
        Given that I am on the 'Create a New Library' page in the dashboard.
        And I want help about the process
        And I click the 'Help' in the navigation bar
        Then Help link should open.
        And help url should end with 'getting_started/get_started.html'
        """
        # The href we want to see in anchor help element.
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff/' \
               'en/latest/getting_started/get_started.html'

        # Assert that help link is correct.
        assert_nav_help_link(
            test=self,
            page=self.dashboard_page,
            href=href
        )

    def test_library_create_side_bar_help(self):
        """
        Scenario: Help link in sidebar links is working on 'Create a New Library' page in the dashboard.
        Given that I am on the 'Create a New Library' page in the dashboard.
        And I want help about the process
        And I click the 'Getting Started with edX Studio' in the sidebar links
        Then Help link should open.
        And help url should end with 'getting_started/get_started.html'
        """
        # The href we want to see in anchor help element.
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff/' \
               'en/latest/getting_started/get_started.html'

        # Assert that help link is correct.
        assert_side_bar_help_link(
            test=self,
            page=self.dashboard_page,
            href=href,
            help_text='Getting Started with edX Studio',
            as_list_item=True
        )


class LibraryTabHelpTest(WebAppTest):
    """
    Test help links on the library tab present at dashboard.
    """
    def setUp(self):
        super(LibraryTabHelpTest, self).setUp()
        self.auth_page = AutoAuthPage(self.browser, staff=True)
        self.dashboard_page = DashboardPage(self.browser)
        self.auth_page.visit()
        self.dashboard_page.visit()

    def test_library_tab_nav_help(self):
        """
        Scenario: Help link in navigation bar is working on 'Home'(Courses tab) page.
        Given that I am on the 'Home'(Courses tab) page.
        And I want help about the process
        And I click the 'Help' in the navigation bar
        Then Help link should open.
        And help url should end with 'getting_started/get_started.html'
        """
        self.assertTrue(self.dashboard_page.has_new_library_button)
        click_css(self.dashboard_page, '#course-index-tabs .libraries-tab', 0, False)
        # The href we want to see in anchor help element.
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff/' \
               'en/latest/getting_started/get_started.html'

        # Assert that help link is correct.
        assert_nav_help_link(
            test=self,
            page=self.dashboard_page,
            href=href
        )


class LibraryHelpTest(StudioLibraryTest):
    """
    Test help links on a Library page.
    """
    def setUp(self):
        super(LibraryHelpTest, self).setUp()
        self.library_page = LibraryPage(self.browser, self.library_key)
        self.library_user_page = LibraryUsersPage(self.browser, self.library_key)

    def test_library_content_nav_help(self):
        """
        Scenario: Help link in navigation bar is working on content
        library page(click a library on the Library list page).
        Given that I am on the content library page(click a library on the Library list page).
        And I want help about the process
        And I click the 'Help' in the navigation bar
        Then Help link should open.
        And help url should end with 'course/components/libraries.html'
        """
        self.library_page.visit()
        # The href we want to see in anchor help element.
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff/' \
               'en/latest/course_components/libraries.html'

        # Assert that help link is correct.
        assert_nav_help_link(
            test=self,
            page=self.library_page,
            href=href
        )

    def test_library_content_side_bar_help(self):
        """
        Scenario: Help link in sidebar links is working on
        content library page(click a library on the Library list page).
        Given that I am on the content library page(click a library on the Library list page).
        And I want help about the process
        And I click the 'Learn more about content libraries' in the sidebar links
        Then Help link should open.
        And help url should end with 'course/components/libraries.html'
        """
        self.library_page.visit()
        # The href we want to see in anchor help element.
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff/' \
               'en/latest/course_components/libraries.html'

        # Assert that help link is correct.
        assert_side_bar_help_link(
            test=self,
            page=self.library_page,
            href=href,
            help_text='Learn more about content libraries'
        )

    def test_library_user_access_setting_nav_help(self):
        """
        Scenario: Help link in navigation bar is working on 'User Access'
         settings page of library.
        Given that I am on the 'User Access' settings page of library.
        And I want help about the process
        And I click the 'Help' in the navigation bar
        Then Help link should open.
        And help url should end with
        'creating_content/libraries.html#give-other-users-access-to-your-library'
        """
        self.library_user_page.visit()
        # The href we want to see in anchor help element.
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff/en/' \
               'latest/course_components/libraries.html#give-other-users-access-to-your-library'

        # Assert that help link is correct.
        assert_nav_help_link(
            test=self,
            page=self.library_user_page,
            href=href
        )


class LibraryImportHelpTest(StudioLibraryTest):
    """
    Test help links on a Library import and export pages.
    """
    def setUp(self):
        super(LibraryImportHelpTest, self).setUp()
        self.library_import_page = ImportLibraryPage(self.browser, self.library_key)
        self.library_import_page.visit()

    def test_library_import_nav_help(self):
        """
        Scenario: Help link in navigation bar is working on Library import page.
        Given that I am on the Library import page.
        And I want help about the process
        And I click the 'Help' in the navigation bar
        Then Help link should open.
        And help url should end with 'creating_content/libraries.html#import-a-library'
        """
        # The href we want to see in anchor help element.
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff/en/' \
               'latest/course_components/libraries.html#import-a-library'

        # Assert that help link is correct.
        assert_nav_help_link(
            test=self,
            page=self.library_import_page,
            href=href
        )

    def test_library_import_side_bar_help(self):
        """
        Scenario: Help link in sidebar links is working on Library import page.
        Given that I am on the Library import page.
        And I want help about the process
        And I click the 'Learn more about importing a library' in the sidebar links
        Then Help link should open.
        And help url should end with 'creating_content/libraries.html#import-a-library'
        """
        # The href we want to see in anchor help element.
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff/en/' \
               'latest/course_components/libraries.html#import-a-library'

        # Assert that help link is correct.
        assert_side_bar_help_link(
            test=self,
            page=self.library_import_page,
            href=href,
            help_text='Learn more about importing a library'
        )


class LibraryExportHelpTest(StudioLibraryTest):
    """
    Test help links on a Library export pages.
    """
    def setUp(self):
        super(LibraryExportHelpTest, self).setUp()
        self.library_export_page = ExportLibraryPage(self.browser, self.library_key)
        self.library_export_page.visit()

    def test_library_export_nav_help(self):
        """
        Scenario: Help link in navigation bar is working on Library export page.
        Given that I am on the Library export page.
        And I want help about the process
        And I click the 'Help' in the navigation bar
        Then Help link should open.
        And help url should end with 'creating_content/libraries.html#export-a-library'
        """
        # The href we want to see in anchor help element.
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff/en/' \
               'latest/course_components/libraries.html#export-a-library'

        # Assert that help link is correct.
        assert_nav_help_link(
            test=self,
            page=self.library_export_page,
            href=href
        )

    def test_library_export_side_bar_help(self):
        """
        Scenario: Help link in sidebar links is working on Library export page.
        Given that I am on the Library export page.
        And I want help about the process
        And I click the 'Learn more about exporting a library' in the sidebar links
        Then Help link should open.
        And help url should end with 'creating_content/libraries.html#export-a-library'
        """
        # The href we want to see in anchor help element.
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff/en/' \
               'latest/course_components/libraries.html#export-a-library'

        # Assert that help link is correct.
        assert_side_bar_help_link(
            test=self,
            page=self.library_export_page,
            href=href,
            help_text='Learn more about exporting a library'
        )


class NewProgramHelpTest(ProgramsConfigMixin, WebAppTest):
    """
    Test help links on a 'New Program' page
    """
    def setUp(self):
        super(NewProgramHelpTest, self).setUp()
        self.auth_page = AutoAuthPage(self.browser, staff=True)
        self.program_page = DashboardPageWithPrograms(self.browser)
        self.auth_page.visit()
        self.set_programs_api_configuration(True)
        self.program_page.visit()

    def test_program_create_nav_help(self):
        """
        Scenario: Help link in navigation bar is working on 'New Program' page
        Given that I am on the 'New Program' page
        And I want help about the process
        And I click the 'Help' in the navigation bar
        Then Help link should open.
        And help url should end with 'index.html'
        """
        self.program_page.click_new_program_button()
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff' \
               '/en/latest/index.html'

        # Assert that help link is correct.
        assert_nav_help_link(
            test=self,
            page=self.program_page,
            href=href,
        )


class CourseOutlineHelpTest(StudioCourseTest):
    """
    Tests help links on course outline page.
    """
    def setUp(self):  # pylint: disable=arguments-differ
        super(CourseOutlineHelpTest, self).setUp()
        self.course_outline_page = CourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )
        self.course_outline_page.visit()

    @skip("This scenario depends upon TNL-5460")
    def test_course_outline_nav_help(self):
        """
        Scenario: Help link in navigation bar is working on Course Outline page
        Given that I am on the Course Outline page
        And I want help about the process
        And I click the 'Help' in the navigation bar
        Then Help link should open.
        And help url should end with 'developing_course/course_outline.html'
        """
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff' \
               '/en/latest/developing_course/course_outline.html'

        # Assert that help link is correct.
        assert_nav_help_link(
            test=self,
            page=self.course_outline_page,
            href=href
        )

    def test_course_outline_side_bar_help(self):
        """
        Scenario: Help link in sidebar links is working on Course Outline page
        Given that I am on the Course Outline page.
        And I want help about the process
        And I click the 'Learn more about the course outline' in the sidebar links
        Then Help link should open.
        And help url should end with 'developing_course/course_outline.html'
        """
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff' \
               '/en/latest/developing_course/course_outline.html'

        # Assert that help link is correct.
        assert_side_bar_help_link(
            test=self,
            page=self.course_outline_page,
            href=href,
            help_text='Learn more about the course outline',
            index=0
        )


class CourseUpdateHelpTest(StudioCourseTest):
    """
    Test help links on Course Update page
    """
    def setUp(self):  # pylint: disable=arguments-differ
        super(CourseUpdateHelpTest, self).setUp()
        self.course_update_page = CourseUpdatesPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )
        self.course_update_page.visit()

    def test_course_update_nav_help(self):
        """
        Scenario: Help link in navigation bar is working on 'Course Update' page
        Given that I am on the 'Course Update' page
        And I want help about the process
        And I click the 'Help' in the navigation bar
        Then Help link should open.
        And help url should end with 'course_assets/handouts_updates.html'
        """
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff/' \
               'en/latest/course_assets/handouts_updates.html'

        # Assert that help link is correct.
        assert_nav_help_link(
            test=self,
            page=self.course_update_page,
            href=href
        )


class AssetIndexHelpTest(StudioCourseTest):
    """
    Test help links on Course 'Files & Uploads' page
    """
    def setUp(self):  # pylint: disable=arguments-differ
        super(AssetIndexHelpTest, self).setUp()
        self.course_asset_index_page = AssetIndexPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )
        self.course_asset_index_page.visit()

    def test_asset_index_nav_help(self):
        """
        Scenario: Help link in navigation bar is working on 'Files & Uploads' page
        Given that I am on the 'Files & Uploads' page
        And I want help about the process
        And I click the 'Help' in the navigation bar
        Then Help link should open.
        And help url should end with 'course_assets/course_files.html'
        """
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff/' \
               'en/latest/course_assets/course_files.html'

        # Assert that help link is correct.
        assert_nav_help_link(
            test=self,
            page=self.course_asset_index_page,
            href=href
        )

    def test_asset_index_side_bar_help(self):
        """
        Scenario: Help link in sidebar links is working on 'Files & Uploads' page
        Given that I am on the 'Files & Uploads' page.
        And I want help about the process
        And I click the 'Learn more about managing files' in the sidebar links
        Then Help link should open.
        And help url should end with 'course_assets/course_files.html'
        """
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff/' \
               'en/latest/course_assets/course_files.html'

        # Assert that help link is correct.
        assert_side_bar_help_link(
            test=self,
            page=self.course_asset_index_page,
            href=href,
            help_text='Learn more about managing files'
        )


class CoursePagesHelpTest(StudioCourseTest):
    """
    Test help links on Course 'Pages' page
    """
    def setUp(self):  # pylint: disable=arguments-differ
        super(CoursePagesHelpTest, self).setUp()
        self.course_pages_page = PagesPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )
        self.course_pages_page.visit()

    def test_course_page_nav_help(self):
        """
        Scenario: Help link in navigation bar is working on 'Pages' page
        Given that I am on the 'Pages' page
        And I want help about the process
        And I click the 'Help' in the navigation bar
        Then Help link should open.
        And help url should end with 'course_assets/pages.html'
        """
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff/' \
               'en/latest/course_assets/pages.html'

        # Assert that help link is correct.
        assert_nav_help_link(
            test=self,
            page=self.course_pages_page,
            href=href
        )


class UploadTextbookHelpTest(StudioCourseTest):
    """
    Test help links on Course 'Textbooks' page
    """
    def setUp(self):  # pylint: disable=arguments-differ
        super(UploadTextbookHelpTest, self).setUp()
        self.course_textbook_upload_page = TextbookUploadPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )
        self.course_textbook_upload_page.visit()

    def test_course_textbook_upload_nav_help(self):
        """
        Scenario: Help link in navigation bar is working on 'Textbooks' page
        Given that I am on the 'Textbooks' page
        And I want help about the process
        And I click the 'Help' in the navigation bar
        Then Help link should open.
        And help url should end with 'course_assets/textbooks.html'
        """
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff' \
               '/en/latest/course_assets/textbooks.html'

        # Assert that help link is correct.
        assert_nav_help_link(
            test=self,
            page=self.course_textbook_upload_page,
            href=href
        )

    def test_course_textbook_side_bar_help(self):
        """
        Scenario: Help link in sidebar links is working on 'Textbooks' page
        Given that I am on the 'Textbooks' page
        And I want help about the process
        And I click the 'Learn more about textbooks' in the sidebar links
        Then Help link should open.
        And help url should end with 'course_assets/textbooks.html'
        """
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff' \
               '/en/latest/course_assets/textbooks.html'

        # Assert that help link is correct.
        assert_side_bar_help_link(
            test=self,
            page=self.course_textbook_upload_page,
            href=href,
            help_text='Learn more about textbooks'
        )


class StudioUnitHelpTest(ContainerBase):
    """
    Tests help links on Unit page.
    """
    def setUp(self, is_staff=True):
        super(StudioUnitHelpTest, self).setUp(is_staff=is_staff)

    def populate_course_fixture(self, course_fixture):
        """
        Populates the course fixture.

        We are modifying 'advanced_modules' setting of the
        course.

        Also add a section with a subsection and a unit.
        """
        course_fixture.add_advanced_settings(
            {u"advanced_modules": {"value": ["split_test"]}}
        )

        course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit')
                )
            )
        )

    def test_unit_page_nav_help(self):
        """
        Scenario: Help link in navigation bar is working on Unit page.
        Given that I am on the Unit page.
        And I want help about the process
        And I click the 'Help' in the navigation bar
        Then Help link should open.
        And help url should end with 'developing_course/course_units.html'
        """
        unit_page = self.go_to_unit_page()
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff' \
               '/en/latest/developing_course/course_units.html'

        # Assert that help link is correct.
        assert_nav_help_link(
            test=self,
            page=unit_page,
            href=href
        )


class SettingsHelpTest(StudioCourseTest):
    """
    Tests help links on Schedule and Details Settings page
    """
    def setUp(self, is_staff=False, test_xss=True):
        super(SettingsHelpTest, self).setUp()

        self.settings_page = SettingsPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        self.settings_page.visit()

    def test_settings_page_nav_help(self):
        """
        Scenario: Help link in navigation bar is working on Settings page.
        Given that I am on the Settings page.
        And I want help about the process
        And I click the 'Help' in the navigation bar
        Then Help link should open.
        And help url should end with 'set_up_course/setting_up_student_view.html'
        """
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff' \
               '/en/latest/set_up_course/setting_up_student_view.html'

        # Assert that help link is correct.
        assert_nav_help_link(
            test=self,
            page=self.settings_page,
            href=href
        )


class GradingPageHelpTest(StudioCourseTest):
    """
    Tests help links on Grading page
    """
    def setUp(self, is_staff=False, test_xss=True):
        super(GradingPageHelpTest, self).setUp()

        self.grading_page = GradingPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        self.grading_page.visit()

    def test_grading_page_nav_help(self):
        """
        Scenario: Help link in navigation bar is working on Grading page.
        Given that I am on the Grading page
        And I want help about the process
        And I click the 'Help' in the navigation bar
        Then Help link should open.
        And help url should end with 'grading/index.html'
        """
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff/' \
               'en/latest/grading/index.html'

        # Assert that help link is correct.
        assert_nav_help_link(
            test=self,
            page=self.grading_page,
            href=href
        )


class CourseTeamSettingsHelpTest(StudioCourseTest):
    """
    Tests help links on Course Team settings page
    """
    def setUp(self, is_staff=False, test_xss=True):
        super(CourseTeamSettingsHelpTest, self).setUp()

        self.course_team_settings_page = CourseTeamPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        self.course_team_settings_page.visit()

    def test_course_course_team_nav_help(self):
        """
        Scenario: Help link in navigation bar is working on Course Team settings page
        Given that I am on the Course Team settings page
        And I want help about the process
        And I click the 'Help' in the navigation bar
        Then Help link should open.
        And help url should end with 'set_up_course/course_staffing.html#add-course-team-members'
        """
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff/' \
               'en/latest/set_up_course/course_staffing.html#add-course-team-members'

        # Assert that help link is correct.
        assert_nav_help_link(
            test=self,
            page=self.course_team_settings_page,
            href=href
        )


class CourseGroupConfigurationHelpTest(StudioCourseTest):
    """
    Tests help links on course Group Configurations settings page
    """
    def setUp(self, is_staff=False, test_xss=True):
        super(CourseGroupConfigurationHelpTest, self).setUp()

        self.course_group_configuration_page = GroupConfigurationsPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        self.course_group_configuration_page.visit()

    def test_course_group_conf_nav_help(self):
        """
        Scenario: Help link in navigation bar is working on
                  Group Configurations settings page
        Given that I am on the Group Configurations settings page
        And I want help about the process
        And I click the 'Help' in the navigation bar
        Then Help link should open.
        And help url should end with 'index.html'
        """
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff/' \
               'en/latest/index.html'

        # Assert that help link is correct.
        assert_nav_help_link(
            test=self,
            page=self.course_group_configuration_page,
            href=href
        )

    def test_course_group_conf_content_group_side_bar_help(self):
        """
        Scenario: Help link in side bar under the 'content group' is working
                  on Group Configurations settings page
        Given that I am on the Group Configurations settings page
        And I want help about the process
        And I click the 'Learn More' in the sidebar links
        Then Help link should open.
        And help url should end with 'course_features/cohorts/cohorted_courseware.html'
        """
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff/' \
               'en/latest/course_features/cohorts/cohorted_courseware.html'

        # Assert that help link is correct.
        assert_side_bar_help_link(
            test=self,
            page=self.course_group_configuration_page,
            href=href,
            help_text='Learn More'
        )


class AdvancedSettingHelpTest(StudioCourseTest):
    """
    Tests help links on course Advanced Settings page.
    """
    def setUp(self, is_staff=False, test_xss=True):
        super(AdvancedSettingHelpTest, self).setUp()

        self.advanced_settings = AdvancedSettingsPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        self.advanced_settings.visit()

    def test_advanced_settings_nav_help(self):
        """
        Scenario: Help link in navigation bar is working on Advanced Settings page.
        Given that I am on the Advanced Settings page.
        And I want help about the process
        And I click the 'Help' in the navigation bar
        Then Help link should open.
        And help url should end with 'index.html'
        """
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff' \
               '/en/latest/index.html'

        # Assert that help link is correct.
        assert_nav_help_link(
            test=self,
            page=self.advanced_settings,
            href=href
        )


class CertificatePageHelpTest(StudioCourseTest):
    """
    Tests help links on course Certificate settings page.
    """
    def setUp(self, is_staff=False, test_xss=True):
        super(CertificatePageHelpTest, self).setUp()

        self.certificates_page = CertificatesPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        self.certificates_page.visit()

    def test_certificate_page_nav_help(self):
        """
        Scenario: Help link in navigation bar is working on Certificate settings page
        Given that I am on the Certificate settings page
        And I want help about the process
        And I click the 'Help' in the navigation bar
        Then Help link should open.
        And help url should end with 'set_up_course/creating_course_certificates.html'
        """
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff' \
               '/en/latest/set_up_course/creating_course_certificates.html'

        # Assert that help link is correct.
        assert_nav_help_link(
            test=self,
            page=self.certificates_page,
            href=href
        )

    def test_certificate_page_side_bar_help(self):
        """
        Scenario: Help link in side bar is working Certificate settings page
        Given that I am on the Certificate settings page
        And I want help about the process
        And I click the 'Learn more about certificates' in the sidebar links
        Then Help link should open.
        And help url should end with 'set_up_course/creating_course_certificates.html'
        """
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff' \
               '/en/latest/set_up_course/creating_course_certificates.html'

        # Assert that help link is correct.
        assert_side_bar_help_link(
            test=self,
            page=self.certificates_page,
            href=href,
            help_text='Learn more about certificates',
        )


class GroupExperimentConfigurationHelpTest(ContainerBase):
    """
    Tests help links on course Group Configurations settings page

    It is related to Experiment Group Configurations on the page.
    """
    def setUp(self):  # pylint: disable=arguments-differ
        super(GroupExperimentConfigurationHelpTest, self).setUp()
        self.group_configuration_page = GroupConfigurationsPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )
        # self.create_poorly_configured_split_instance()
        self.group_configuration_page.visit()

    def populate_course_fixture(self, course_fixture):
        """
        Populates the course fixture.

        We are modifying 'advanced_modules' setting of the
        course.
        """
        course_fixture.add_advanced_settings(
            {u"advanced_modules": {"value": ["split_test"]}}
        )

    def test_course_group_configuration_experiment_side_bar_help(self):
        """
        Scenario: Help link in side bar under the 'Experiment Group Configurations'
                  is working on Group Configurations settings page
        Given that I am on the Group Configurations settings page
        And I want help about the process
        And I click the 'Learn More' in the sidebar links
        Then Help link should open.
        And help url should end with
        'content_experiments_configure.html#set-up-group-configurations-in-edx-studio'
        """
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff/en/latest/course_features' \
               '/content_experiments/content_experiments_configure.html#set-up-group-configurations-in-edx-studio'
        # Assert that help link is correct.
        assert_side_bar_help_link(
            test=self,
            page=self.group_configuration_page,
            href=href,
            help_text='Learn More',
        )


class ToolsImportHelpTest(StudioCourseTest):
    """
    Tests help links on tools import pages.
    """
    def setUp(self, is_staff=False, test_xss=True):

        super(ToolsImportHelpTest, self).setUp()

        self.import_page = ImportCoursePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )
        self.import_page.visit()

    def test_tools_import_nav_help(self):
        """
        Scenario: Help link in navigation bar is working on tools Library import page
        Given that I am on the Library import tools page
        And I want help about the process
        And I click the 'Help' in the navigation bar
        Then Help link should open.
        And help url should end with 'releasing_course/export_import_course.html#import-a-course'
        """
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff/en/' \
               'latest/releasing_course/export_import_course.html#import-a-course'

        # Assert that help link is correct.
        assert_nav_help_link(
            test=self,
            page=self.import_page,
            href=href
        )

    def test_tools_import_side_bar_help(self):
        """
        Scenario: Help link in side bar is working on tools Library import page
        Given that I am on the tools Library import page
        And I want help about the process
        And I click the 'Learn more about importing a course' in the sidebar links
        Then Help link should open.
        And help url should end with 'releasing_course/export_import_course.html#import-a-course'
        """
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff/en/' \
               'latest/releasing_course/export_import_course.html#import-a-course'

        # Assert that help link is correct.
        assert_side_bar_help_link(
            test=self,
            page=self.import_page,
            href=href,
            help_text='Learn more about importing a course',
        )


class ToolsExportHelpTest(StudioCourseTest):
    """
    Tests help links on tools export pages.
    """
    def setUp(self, is_staff=False, test_xss=True):

        super(ToolsExportHelpTest, self).setUp()

        self.export_page = ExportCoursePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )
        self.export_page.visit()

    def test_tools_import_nav_help(self):
        """
        Scenario: Help link in navigation bar is working on tools Library export page
        Given that I am on the Library export tools page
        And I want help about the process
        And I click the 'Help' in the navigation bar
        Then Help link should open.
        And help url should end with 'releasing_course/export_import_course.html#export-a-course'
        """
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff/en/' \
               'latest/releasing_course/export_import_course.html#export-a-course'

        # Assert that help link is correct.
        assert_nav_help_link(
            test=self,
            page=self.export_page,
            href=href
        )

    def test_tools_import_side_bar_help(self):
        """
        Scenario: Help link in side bar is working on tools Library export page
        Given that I am on the tools Library import page
        And I want help about the process
        And I click the 'Learn more about exporting a course' in the sidebar links
        Then Help link should open.
        And help url should end with 'releasing_course/export_import_course.html#export-a-course'
        """
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff/en/' \
               'latest/releasing_course/export_import_course.html#export-a-course'

        # Assert that help link is correct.
        assert_side_bar_help_link(
            test=self,
            page=self.export_page,
            href=href,
            help_text='Learn more about exporting a course',
        )


class StudioWelcomeHelpTest(WebAppTest):
    """
    Tests help link on 'Welcome' page ( User not logged in)
    """
    def setUp(self):
        super(StudioWelcomeHelpTest, self).setUp()
        self.index_page = IndexPage(self.browser)
        self.index_page.visit()

    def test_welcome_nav_help(self):
        """
        Scenario: Help link in navigation bar is working on 'Welcome' page (User not logged in).
        Given that I am on the 'Welcome' page.
        And I want help about the edx
        And I click the 'Help' in the navigation bar
        Then Help link should open.
        And help url should contain 'getting_started/get_started.html'
        """
        # The url we want to see in anchor help element.
        href = 'http://edx.readthedocs.org/projects/edx-partner-course-staff/' \
               'en/latest/getting_started/get_started.html'

        # Assert that help link is correct.
        assert_nav_help_link(
            test=self,
            page=self.index_page,
            href=href,
            signed_in=False
        )
