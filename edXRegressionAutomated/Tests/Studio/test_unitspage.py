from bok_choy.web_app_test import WebAppTest
from pages.login import LoginPage
from pages.courseoutlinepage import CourseOutlinePage
from pages.mycoursespage import MyCoursesPage
from ..LMS.pages.lms_login import LMSLoginPage
from pages.unitpage import UnitsPage
from ..Settings.config import GlobalVariables

class TestUnitPage(WebAppTest):
    def setUp(self):
        super(TestUnitPage, self).setUp()
        self.browser.maximize_window()
        self.login_page = LoginPage(self.browser)
        self.mycourses_page = MyCoursesPage(self.browser)
        self.course_outline_page = CourseOutlinePage(self.browser)
        self.lms_login_page = LMSLoginPage(self.browser)
        self.unit_page = UnitsPage(self.browser)

        LoginPage(self.browser).visit()
        self.login_page.login(GlobalVariables.user_name, GlobalVariables.password)
        self.login_page.login_success_validation()

        # Click the Auto Course
        self.mycourses_page.click_manual_smoke_test_course_1_auto()

        # Delete all Sections in the course
        self.course_outline_page.delete_sections()

        # Navigate to Units/ Add New Component Page
        self.course_outline_page.add_new_section_main_button('Section Main Button') # Pre Req
        self.course_outline_page.add_new_subsection('New SubSection') # Pre Req
        self.course_outline_page.add_new_unit()

    def test_add_components(self):
        # Verify that all HTML components can be added and are displayed in pages

        list_html_component = {'Announcement':'"announcement.yaml"', 'Anonymous User ID':'"anon_user_id.yaml"',
                               'Full Screen Image Tool':'"image_modal.yaml"', 'IFrame Tool':'"iframe.yaml"',
                               'Raw HTML':'"raw.yaml"', 'Zooming Image Tool':'"zooming_image.yaml"'}

        for verify, add in list_html_component.iteritems():
            self.unit_page.click_unit_html_button()
            self.unit_page.add_component_html(add)
            self.assertTrue(self.unit_page.verify_component(verify))
            print verify + ' in HTML added successfully on pages'
            """
            Notes: Text in HTML is missing
            """

        # Verify that user can click Discussion button and the component is added

        self.unit_page.click_unit_discussion_button()
        print 'Adding Inline Discussion test successful'

        # Verify that all Common Problem Types are added and displayed in pages

        list_common_problem_components = {'Blank Common Problem':'"blank_common.yaml"',
                                          'Checkboxes':'"checkboxes_response.yaml"',
                                          'Dropdown':'"optionresponse.yaml"',
                                          'Multiple Choice':'"multiplechoice.yaml"',
                                          'Numerical Input':'"numericalresponse.yaml"',
                                          'Text Input':'"string_response.yaml"'}

        for verify, add in list_common_problem_components.iteritems():
            self.unit_page.click_unit_common_problem_button()
            self.unit_page.add_component_common_problem(add)
            self.assertTrue(self.unit_page.verify_component(verify))
            print verify + ' in Common Problem added successfully on pages'

        # Verify that all Advanced Problem Types are added and displayed in pages

        list_advanced_problem_components = {'Circuit Schematic Builder':'"circuitschematic.yaml"',
                                            'Custom Javascript Display and Grading':'"jsinput_response.yaml"',
                                            'Custom Python-Evaluated Input':'"customgrader.yaml"',
                                            'Drag and Drop':'"drag_and_drop.yaml"',
                                            'Image Mapped Input':'"imageresponse.yaml"',
                                            'Math Expression Input':'"formularesponse.yaml"',
                                            'Molecular Structure':'"jsme.yaml"',
                                            'Problem with Adaptive Hint':'"problem_with_hint.yaml"' }

        for verify, add in list_advanced_problem_components.iteritems():
            self.unit_page.click_unit_advanced_problem_button()
            self.unit_page.add_component_common_problem(add)
            self.assertTrue(self.unit_page.verify_component(verify))
            print verify + ' in Advanced Problem added successfully on pages'
            """
            Blank Advanced Problem and Peer Assessment missing
            """

        # Verify that Video is added and displayed in pages
        self.unit_page.click_unit_video_button()
        print 'Adding Video test successful'
