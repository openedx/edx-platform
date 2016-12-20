"""
Acceptance tests for Home Page (My Courses / My Libraries).
"""
from bok_choy.web_app_test import WebAppTest
from opaque_keys.edx.locator import LibraryLocator

from ...fixtures import PROGRAMS_STUB_URL
from ...fixtures.config import ConfigModelFixture
from ...fixtures.programs import ProgramsFixture
from ...pages.studio.auto_auth import AutoAuthPage
from ...pages.studio.library import LibraryEditPage
from ...pages.studio.index import DashboardPage, DashboardPageWithPrograms


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
        name = "New Library Name"
        org = "TestOrgX"
        number = "TESTLIB"

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


class DashboardProgramsTabTest(WebAppTest):
    """
    Test the programs tab on the studio home page.
    """

    def setUp(self):
        super(DashboardProgramsTabTest, self).setUp()
        ProgramsFixture().install_programs([])
        self.auth_page = AutoAuthPage(self.browser, staff=True)
        self.dashboard_page = DashboardPageWithPrograms(self.browser)
        self.auth_page.visit()

    def set_programs_api_configuration(self, is_enabled=False, api_version=1, api_url=PROGRAMS_STUB_URL,
                                       js_path='/js', css_path='/css'):
        """
        Dynamically adjusts the programs API config model during tests.
        """
        ConfigModelFixture('/config/programs', {
            'enabled': is_enabled,
            'enable_studio_tab': is_enabled,
            'enable_student_dashboard': is_enabled,
            'api_version_number': api_version,
            'internal_service_url': api_url,
            'public_service_url': api_url,
            'authoring_app_js_path': js_path,
            'authoring_app_css_path': css_path,
            'cache_ttl': 0
        }).install()

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
        self.set_programs_api_configuration(True)
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
        ProgramsFixture().install_programs(test_program_values)
        self.set_programs_api_configuration(True)
        self.dashboard_page.visit()
        self.assertTrue(self.dashboard_page.is_programs_tab_present())
        self.assertTrue(self.dashboard_page.is_new_program_button_present())
        results = self.dashboard_page.get_program_list()
        self.assertEqual(results, test_program_values)
        self.assertFalse(self.dashboard_page.is_empty_list_create_button_present())

    def test_tab_requires_staff(self):
        """
        The programs tab and "new program" button will not be available, even
        when enabled via config, if the user is not global staff.
        """
        self.set_programs_api_configuration(True)
        AutoAuthPage(self.browser, staff=False).visit()
        self.dashboard_page.visit()
        self.assertFalse(self.dashboard_page.is_programs_tab_present())
        self.assertFalse(self.dashboard_page.is_new_program_button_present())
