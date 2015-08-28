from bok_choy.web_app_test import WebAppTest
from pages.mycoursespage import MyCoursesPage
from pages.studiohelp import StudioHelpPage
from pages.login import LoginPage
from pages.edxlivepage import EdxLivePage
from pages.readthedocspdf import ReadTheDocsPDF
from .pages.courseoutlinepage import CourseOutlinePage
from ..Settings.config import GlobalVariables

class TestMyCoursesPage(WebAppTest):
    def setUp(self):
        super(TestMyCoursesPage, self).setUp()
        self.browser.maximize_window()
        self.mycourses_page = MyCoursesPage(self.browser)
        self.studio_help_page = StudioHelpPage(self.browser)
        self.login_page = LoginPage(self.browser)
        self.edx_live_page = EdxLivePage(self.browser)
        self.read_the_docs_pdf = ReadTheDocsPDF(self.browser)
        self.course_outline_page = CourseOutlinePage(self.browser)

        LoginPage(self.browser).visit()
        self.login_page.login(GlobalVariables.user_name, GlobalVariables.password)
        self.login_page.login_success_validation()

    def test_click_edx_image(self):
        # Verify that user can click edX Image and is navigated to My Courses (same) page
        self.mycourses_page.click_edx_image()

    def test_studio_help_link(self):
        # Verify that user can click pages Help link and is navigated to pages Help page

        self.mycourses_page.click_help_link()

    def test_mycourses_link_under_account_username(self):
        # Verify that user can click My Courses link under Account Username drop down and is navigated to My Courses
        # (same) page

        self.mycourses_page.click_mycourses_link()

    def test_email_to_create_course_link(self):
        # Verify that user can click the Email staff to create course link and is navigated to outlook email with
        # correct email in To

        self.mycourses_page.click_email_staff_to_create()
        self.assertEquals(self.mycourses_page.click_email_staff_to_create(), "mailto:studio-request@edx.org")

    def test_getting_started_with_studio_link(self):
        # Verify that user can click Getting Started with edX pages link and is navigated to read the docs Getting
        # Started with pages page

        self.mycourses_page.click_getting_started_with_studio_link()

    def test_request_help_with_studio_link(self):
        # Verify that user can click Request help with edX pages link and Help and Support popup displays

        self.mycourses_page.click_request_help_with_studio_link()

    def test_contact_edx_staff_help_create_course_link(self):
        # Verify that user can click contact edX staff to help you create a course link and is navigated to outlook
        # email with correct email in To

        self.mycourses_page.click_staff_to_help_create_course()
        self.assertEquals(self.mycourses_page.click_staff_to_help_create_course(), "mailto:studio-request@edx.org")

    def test_contact_us_link(self):
        # Verify that user can click Contact Us link in the footer and Help and Support pop up displays

        self.mycourses_page.click_contact_us_link()

    def test_building_and_running_an_edx_link(self):
        # Verify that user can click Building and Running an edX course PDF and is navigated to read the docs page

        self.mycourses_page.click_looking_help_with_studio()

    def test_clicking_auto_course(self):
        # Verify that user can click Manual Smoke Test Course 1 - Auto and is navigated to its Course Outline page

        self.mycourses_page.click_manual_smoke_test_course_1_auto()
