from ..helpers import UniqueCourseTest
from ...fixtures.course import CourseFixture, XBlockFixtureDesc, CourseUpdateDesc
from ...pages.lms.auto_auth import AutoAuthPage
from ...pages.lms.tab_nav import TabNavPage
from ...pages.lms.course_nav import CourseNavPage
from ...pages.lms.courseware import CoursewarePage
from selenium.webdriver.common.action_chains import ActionChains


class HTMLAnnotationTest(UniqueCourseTest):
    """
    Tests for annotation inside HTML components in LMS.
    """

    def setUp(self):
        """
        Initialize pages and install a course fixture.
        """
        super(HTMLAnnotationTest, self).setUp()
        self.tab_nav = TabNavPage(self.browser)
        self.courseware_page = CoursewarePage(self.browser, self.course_id)
        self.course_nav = CourseNavPage(self.browser)


        course_fix = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )

        self.selector = "annotate_id"
        course_fix.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc(
                        'html',
                        'Test HTML',
                        data="""<html><div><p id="{}">Annotate it!</p></div></html>""".format(self.selector)),
                )
            )).install()

        # Auto-auth register for the course
        AutoAuthPage(self.browser, course_id=self.course_id).visit()



    def test_html_visit(self):
        """
        Navigate to the html page.
        """
        self.courseware_page.visit()
        
        element = self.browser.find_element_by_id(self.selector)
        ac = ActionChains(self.browser)

        # this code manually shows annotator icon, but not in bok_choy.
        ac.move_to_element(element).click_and_hold(element).move_by_offset(-100, 0).release().perform()
        # may be it appears and hides too fast in bok_choy.
        
        