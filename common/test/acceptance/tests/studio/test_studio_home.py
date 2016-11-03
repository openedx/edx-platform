"""
Acceptance tests for Home Page (My Courses / My Libraries).
"""
from bok_choy.web_app_test import WebAppTest
from flaky import flaky
from opaque_keys.edx.locator import LibraryLocator
from uuid import uuid4

from common.test.acceptance.fixtures.catalog import CatalogFixture, CatalogConfigMixin
from common.test.acceptance.fixtures.programs import ProgramsFixture, ProgramsConfigMixin
from common.test.acceptance.pages.studio.auto_auth import AutoAuthPage
from common.test.acceptance.pages.studio.library import LibraryEditPage
from common.test.acceptance.pages.studio.index import DashboardPage, DashboardPageWithPrograms
from common.test.acceptance.pages.lms.account_settings import AccountSettingsPage
from common.test.acceptance.tests.helpers import (
    select_option_by_text,
    get_selected_option_text
)
from openedx.core.djangoapps.programs.tests import factories


class CreateLibraryTest(WebAppTest):
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


class DashboardProgramsTabTest(ProgramsConfigMixin, CatalogConfigMixin, WebAppTest):
    """
    Test the programs tab on the studio home page.
    """

    def setUp(self):
        super(DashboardProgramsTabTest, self).setUp()
        self.stub_programs_api()
        self.stub_catalog_api()

        self.auth_page = AutoAuthPage(self.browser, staff=True)
        self.dashboard_page = DashboardPageWithPrograms(self.browser)
        self.auth_page.visit()

    def stub_programs_api(self):
        """Stub out the programs API with fake data."""
        self.set_programs_api_configuration(is_enabled=True)
        ProgramsFixture().install_programs([])

    def stub_catalog_api(self):
        """Stub out the catalog API's program endpoint."""
        self.set_catalog_configuration(is_enabled=True)
        CatalogFixture().install_programs([])

    def test_tab_is_disabled(self):
        """
        The programs tab and "new program" button should not appear at all
        unless enabled via the config model.
        """
        self.set_programs_api_configuration()
        self.dashboard_page.visit()
        self.assertFalse(self.dashboard_page.is_programs_tab_present())
        self.assertFalse(self.dashboard_page.is_new_program_button_present())

    def test_tab_is_enabled_with_empty_list(self):
        """
        The programs tab and "new program" button should appear when enabled
        via config.  When the programs list is empty, a button should appear
        that allows creating a new program.
        """
        self.dashboard_page.visit()
        self.assertTrue(self.dashboard_page.is_programs_tab_present())
        self.assertTrue(self.dashboard_page.is_new_program_button_present())
        results = self.dashboard_page.get_program_list()
        self.assertEqual(results, [])
        self.assertTrue(self.dashboard_page.is_empty_list_create_button_present())

    def test_tab_is_enabled_with_nonempty_list(self):
        """
        The programs tab and "new program" button should appear when enabled
        via config, and the results of the program list should display when
        the list is nonempty.
        """
        test_program_values = [('first program', 'org1'), ('second program', 'org2')]

        programs = [
            factories.Program(
                name=name,
                organizations=[
                    factories.Organization(key=org),
                ],
                course_codes=[
                    factories.CourseCode(run_modes=[
                        factories.RunMode(),
                    ]),
                ]
            )
            for name, org in test_program_values
        ]

        ProgramsFixture().install_programs(programs)

        self.dashboard_page.visit()

        self.assertTrue(self.dashboard_page.is_programs_tab_present())
        self.assertTrue(self.dashboard_page.is_new_program_button_present())
        self.assertFalse(self.dashboard_page.is_empty_list_create_button_present())

        results = self.dashboard_page.get_program_list()
        self.assertEqual(results, test_program_values)

    def test_tab_requires_staff(self):
        """
        The programs tab and "new program" button will not be available, even
        when enabled via config, if the user is not global staff.
        """
        AutoAuthPage(self.browser, staff=False).visit()
        self.dashboard_page.visit()
        self.assertFalse(self.dashboard_page.is_programs_tab_present())
        self.assertFalse(self.dashboard_page.is_new_program_button_present())


class StudioLanguageTest(WebAppTest):
    """ Test suite for the Studio Language """
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
