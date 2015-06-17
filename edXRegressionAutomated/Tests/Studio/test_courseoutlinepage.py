from bok_choy.web_app_test import WebAppTest

from pages.login import LoginPage
from pages.mycoursespage import MyCoursesPage
from pages.courseoutlinepage import CourseOutlinePage
from Tests.LMS.pages.courseware import CoursewarePage
from pages.unitpage import UnitsPage
from Tests.LMS.pages.lms_login import LMSLoginPage
from Tests.Settings.config import GlobalVariables


class TestCourseOutline(WebAppTest):
    def setUp(self):
        super(TestCourseOutline, self).setUp()
        self.browser.maximize_window()
        self.login_page = LoginPage(self.browser)
        self.mycourses_page = MyCoursesPage(self.browser)
        self.course_outline_page = CourseOutlinePage(self.browser)
        self.courseware_page = CoursewarePage(self.browser)
        self.units_page = UnitsPage(self.browser)
        self.lms_login_page = LMSLoginPage(self.browser)

        LoginPage(self.browser).visit()
        self.login_page.login(GlobalVariables.user_name, GlobalVariables.password)
        self.login_page.login_success_validation()

        # Click the Auto Course
        self.mycourses_page.click_manual_smoke_test_course_1_auto()

        # Delete all Sections in the course
        self.course_outline_page.delete_sections()

    def test_click_course_link(self):
        # Verify that user can click course link and is navigated to Course Outline (same) page

        self.course_outline_page.click_course_link()

    def test_new_section_main_button(self):
        # Verify that user can click new section button (next to View Live Collapse/Expand buttons) and new section is added

        self.course_outline_page.add_new_section_main_button("Section Main Button")
        self.course_outline_page.delete_sections()

    def test_new_sub_section_button(self):
        # Verify that user can click new subsection button and new subsection is added

        self.course_outline_page.add_new_section_main_button('Section Main Button') # Pre Req
        self.course_outline_page.add_new_subsection('New SubSection')
        self.course_outline_page.delete_sections()

    def test_new_unit_button(self):
        # Verify that user can click New Unit button and is navigated to Units (add new component) page

        self.course_outline_page.add_new_section_main_button('Section Main Button') # Pre Req
        self.course_outline_page.add_new_subsection('New SubSection') # Pre Req
        self.course_outline_page.add_new_unit()


class TestCourseOutlineWithViewLive(WebAppTest):
    def setUp(self):
        super(TestCourseOutlineWithViewLive, self).setUp()
        self.browser.maximize_window()
        self.login_page = LoginPage(self.browser)
        self.mycourses_page = MyCoursesPage(self.browser)
        self.course_outline_page = CourseOutlinePage(self.browser)
        self.courseware_page = CoursewarePage(self.browser)
        self.units_page = UnitsPage(self.browser)
        self.lms_login_page = LMSLoginPage(self.browser)

        # To tackle pages Authentication box when clicking View Live
        LMSLoginPage(self.browser).visit()
        self.lms_login_page.login(GlobalVariables.user_name, GlobalVariables.password)
        self.lms_login_page.login_success_validation()

        LoginPage(self.browser).visit()
        self.login_page.login(GlobalVariables.user_name, GlobalVariables.password)
        self.login_page.login_success_validation()

        # Click the Auto Course
        self.mycourses_page.click_manual_smoke_test_course_1_auto()

        # Delete all Sections in the course
        #self.course_outline_page.delete_sections()

    def test_view_live_button(self):
        # Verify that user can click View Live button and is navigated to pages on a new tab

        self.course_outline_page.click_view_live_button()