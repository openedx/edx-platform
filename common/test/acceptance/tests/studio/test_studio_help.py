"""
Test the Studio help links.
"""

from flaky import flaky
from bok_choy.web_app_test import WebAppTest

from common.test.acceptance.tests.studio.base_studio_test import StudioCourseTest
from common.test.acceptance.pages.studio.index import DashboardPage
from common.test.acceptance.pages.studio.utils import click_studio_help, studio_help_links
from common.test.acceptance.pages.studio.index import IndexPage, HomePage
from common.test.acceptance.tests.studio.base_studio_test import StudioLibraryTest
from common.test.acceptance.pages.studio.utils import click_css
from common.test.acceptance.pages.studio.library import LibraryPage
from common.test.acceptance.pages.studio.users import LibraryUsersPage
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
