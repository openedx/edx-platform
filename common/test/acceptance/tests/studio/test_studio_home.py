"""
Acceptance tests for Home Page (My Courses / My Libraries).
"""
import os
import uuid

from bok_choy.web_app_test import WebAppTest
from common.test.acceptance.pages.common.logout import LogoutPage
from common.test.acceptance.pages.lms.courseware import AboutPage, CoursewarePage
from flaky import flaky
from opaque_keys.edx.locator import LibraryLocator, CourseLocator
from uuid import uuid4

from ...fixtures import PROGRAMS_STUB_URL
from ...fixtures.config import ConfigModelFixture
from ...fixtures.programs import FakeProgram, ProgramsFixture, ProgramsConfigMixin
from ...pages.studio.auto_auth import AutoAuthPage
from ...pages.studio.library import LibraryEditPage
from ...pages.studio.index import DashboardPage, DashboardPageWithPrograms
from ...pages.lms.account_settings import AccountSettingsPage
from ..helpers import (
    select_option_by_text,
    get_selected_option_text
)


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

    @flaky  # TODO: SOL-430
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


class DashboardProgramsTabTest(ProgramsConfigMixin, WebAppTest):
    """
    Test the programs tab on the studio home page.
    """

    def setUp(self):
        super(DashboardProgramsTabTest, self).setUp()
        ProgramsFixture().install_programs([])
        self.auth_page = AutoAuthPage(self.browser, staff=True)
        self.dashboard_page = DashboardPageWithPrograms(self.browser)
        self.auth_page.visit()

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
        test_program_values = [
            FakeProgram(name='first program', status='unpublished', org_key='org1', course_id='foo/bar/baz'),
            FakeProgram(name='second program', status='unpublished', org_key='org2', course_id='qux/quux/corge'),
        ]
        ProgramsFixture().install_programs(test_program_values)

        self.set_programs_api_configuration(True)

        self.dashboard_page.visit()

        self.assertTrue(self.dashboard_page.is_programs_tab_present())
        self.assertTrue(self.dashboard_page.is_new_program_button_present())
        self.assertFalse(self.dashboard_page.is_empty_list_create_button_present())

        results = self.dashboard_page.get_program_list()
        expected = [(p.name, p.org_key) for p in test_program_values]
        self.assertEqual(results, expected)

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


class CourseNotEnrollTest(WebAppTest):
    """
    Test that we can create a new content library on the studio home page.
    """

    def setUp(self):
        """
        Load the helper for the home page (dashboard page)
        """
        super(CourseNotEnrollTest, self).setUp()

        self.auth_page = AutoAuthPage(self.browser, staff=True)
        self.dashboard_page = DashboardPage(self.browser)
        self.course_name = "New Course Name"
        self.course_org = "orgX"
        self.course_number = str(uuid.uuid4().get_hex().upper()[0:6])
        self.course_run = "2015_T2"

    def course_id(self):
        """
        Returns the serialized course_key for the test
        """
        # TODO - is there a better way to make this agnostic to the underlying default module store?
        default_store = os.environ.get('DEFAULT_STORE', 'draft')
        course_key = CourseLocator(
            self.course_org,
            self.course_number,
            self.course_run,
            deprecated=(default_store == 'draft')
        )
        return unicode(course_key)

    def test_unenroll_course(self):
        """
        From the home page:
            Click "New Course" ,Fill out the form
            Submit the form
            Return to the home page and logout
            Login with the staff user which is not enrolled in the course
            click the view live button of the course
            Here are two scenario:
             First click the continue button
             Second click the Enroll button and see the response.
        """
        self.auth_page.visit()
        self.dashboard_page.visit()
        self.assertTrue(self.dashboard_page.new_course_button.present)

        self.dashboard_page.click_new_course_button()
        self.assertTrue(self.dashboard_page.is_new_course_form_visible())
        self.dashboard_page.fill_new_course_form(
            self.course_name, self.course_org, self.course_number, self.course_run
        )
        self.assertTrue(self.dashboard_page.is_new_course_form_valid())
        self.dashboard_page.submit_new_course_form()

        self.dashboard_page.visit()
        LogoutPage(self.browser).visit()
        AutoAuthPage(self.browser, course_id=None, staff=True).visit()

        self.dashboard_page.visit()
        self.dashboard_page.view_live('.submit>input:last-child')

        about_page = AboutPage(self.browser, self.course_id)
        about_page.wait_for_page()
        self.assertTrue(about_page.is_browser_on_page())
        self.assertTrue(about_page.is_register_button_present)

        self.dashboard_page.visit()
        self.dashboard_page.view_live('.submit>input:first-child')
        course_ware = CoursewarePage(self.browser, self.course_id)
        course_ware.wait_for_page()
        self.assertTrue(course_ware.is_browser_on_page())
