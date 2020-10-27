"""
Acceptance tests for Home Page (My Courses / My Libraries).
"""
import datetime

from base_studio_test import StudioCourseTest
from common.test.acceptance.pages.common.auto_auth import AutoAuthPage
from common.test.acceptance.pages.lms.account_settings import AccountSettingsPage
from common.test.acceptance.pages.studio.index import DashboardPage
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


class StudioLanguageTest(AcceptanceTest):
    """ Test suite for the Studio Language """
    shard = 21

    def setUp(self):
        super(StudioLanguageTest, self).setUp()
        self.dashboard_page = DashboardPage(self.browser)
        self.account_settings = AccountSettingsPage(self.browser)
        AutoAuthPage(self.browser).visit()

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
