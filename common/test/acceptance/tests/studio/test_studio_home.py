"""
Acceptance tests for Home Page (My Courses / My Libraries).
"""
import datetime
from uuid import uuid4

from flaky import flaky
from opaque_keys.edx.locator import LibraryLocator

from base_studio_test import StudioCourseTest
from common.test.acceptance.pages.common.auto_auth import AutoAuthPage
from common.test.acceptance.pages.lms.account_settings import AccountSettingsPage
from common.test.acceptance.pages.studio.index import DashboardPage
from common.test.acceptance.pages.studio.library import LibraryEditPage
from common.test.acceptance.pages.studio.overview import CourseOutlinePage
from common.test.acceptance.tests.helpers import AcceptanceTest, get_selected_option_text, select_option_by_text


class CreateLibraryTest(AcceptanceTest):
    """
    Test that we can create a new content library on the studio home page.
    """

    def setUp(self):
        """
        Load the helper for the home page (dashboard page)
        """
        super(CreateLibraryTest, self).setUp()

        self.auth_page = AutoAuthPage(self.browser, staff=True)
        self.dashboard_page = DashboardPage(self.browser)

    def test_create_library(self):
        """
        From the home page:
            Click "New Library"
            Fill out the form
            Submit the form
            We should be redirected to the edit view for the library
            Return to the home page
            The newly created library should now appear in the list of libraries
        """
        unique_suffix = uuid4().hex[:4]
        name = "New Library Name " + unique_suffix
        org = "TestOrgX" + unique_suffix
        number = "TESTLIB_" + unique_suffix

        self.auth_page.visit()
        self.dashboard_page.visit()
        self.assertFalse(self.dashboard_page.has_library(name=name, org=org, number=number))
        self.assertTrue(self.dashboard_page.has_new_library_button())

        self.dashboard_page.click_new_library()
        self.assertTrue(self.dashboard_page.is_new_library_form_visible())
        self.dashboard_page.fill_new_library_form(name, org, number)
        self.assertTrue(self.dashboard_page.is_new_library_form_valid())
        self.dashboard_page.submit_new_library_form()

        # The next page is the library edit view; make sure it loads:
        lib_page = LibraryEditPage(self.browser, LibraryLocator(org, number))
        lib_page.wait_for_page()

        # Then go back to the home page and make sure the new library is listed there:
        self.dashboard_page.visit()
        self.assertTrue(self.dashboard_page.has_library(name=name, org=org, number=number))
        # Click on the library listing and verify that the library edit view loads.
        self.dashboard_page.click_library(name)
        lib_page.wait_for_page()


class StudioLanguageTest(AcceptanceTest):
    """ Test suite for the Studio Language """
    def setUp(self):
        super(StudioLanguageTest, self).setUp()
        self.dashboard_page = DashboardPage(self.browser)
        self.account_settings = AccountSettingsPage(self.browser)
        AutoAuthPage(self.browser).visit()

    @flaky  # TODO fix this, see WL-963
    def test_studio_language_change(self):
        """
        Scenario: Ensure that language selection is working fine.
        First I go to the user dashboard page in studio. I can see 'English' is selected by default.
        Then I choose 'Dummy Language' from drop down (at top of the page).
        Then I visit the student account settings page and I can see the language has been updated to 'Dummy Language'
        in both drop downs.
        """
        dummy_language = u'Dummy Language (Esperanto)'
        self.dashboard_page.visit()
        language_selector = self.dashboard_page.language_selector
        self.assertEqual(
            get_selected_option_text(language_selector),
            u'English'
        )

        select_option_by_text(language_selector, dummy_language)
        self.dashboard_page.wait_for_ajax()
        self.account_settings.visit()
        self.assertEqual(self.account_settings.value_for_dropdown_field('pref-lang'), dummy_language)
        self.assertEqual(
            get_selected_option_text(language_selector),
            u'Dummy Language (Esperanto)'
        )


class ArchivedCourseTest(StudioCourseTest):
    """ Tests that archived courses appear in their own list. """

    def setUp(self, is_staff=True, test_xss=False):
        """
        Load the helper for the home page (dashboard page)
        """
        super(ArchivedCourseTest, self).setUp(is_staff=is_staff, test_xss=test_xss)
        self.dashboard_page = DashboardPage(self.browser)

    def populate_course_fixture(self, course_fixture):
        current_time = datetime.datetime.now()
        course_start_date = current_time - datetime.timedelta(days=60)
        course_end_date = current_time - datetime.timedelta(days=90)

        course_fixture.add_course_details({
            'start_date': course_start_date,
            'end_date': course_end_date
        })

    def test_archived_course(self):
        """
        Scenario: Ensure that an archived course displays in its own list and can be clicked on.
        """
        self.dashboard_page.visit()
        self.assertTrue(self.dashboard_page.has_course(
            org=self.course_info['org'], number=self.course_info['number'], run=self.course_info['run'],
            archived=True
        ))

        # Click on the archived course and make sure that the Studio course outline appears.
        self.dashboard_page.click_course_run(self.course_info['run'])
        course_outline_page = CourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )
        course_outline_page.wait_for_page()
