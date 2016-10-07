"""
Javascript tests for the crowdsourcehinter xblock
"""
from textwrap import dedent
from openedx.tests.acceptance.fixtures.course import CourseFixture, XBlockFixtureDesc
from openedx.tests.acceptance.pages.lms.courseware import CoursewarePage
from openedx.tests.acceptance.pages.xblock.crowdsourcehinter_problem import CrowdsourcehinterProblemPage
from openedx.tests.acceptance.pages.studio.auto_auth import AutoAuthPage
from openedx.tests.acceptance.tests.helpers import UniqueCourseTest


class CrowdsourcehinterProblemTest(UniqueCourseTest):
    """
    Test scenario for the hinter.
    """
    USERNAME = "STAFF_TESTER"
    EMAIL = "johndoe@example.com"

    def setUp(self):
        super(CrowdsourcehinterProblemTest, self).setUp()

        self.courseware_page = CoursewarePage(self.browser, self.course_id)

        # Install a course with sections/problems, tabs, updates, and handouts
        course_fix = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )
        problem_data = dedent('''
            <problem>
                <p>A text input problem accepts a line of text from the student, and evaluates the input for correctness based on an expected answer.</p>
                <p>The answer is correct if it matches every character of the expected answer. This can be a problem with international spelling, dates, or anything where the format of the answer is not clear.</p>
                <p>Which US state has Lansing as its capital?</p>
                <stringresponse answer="Michigan" type="ci" >
                      <textline label="Which US state has Lansing as its capital?" size="20"/>
                </stringresponse>
                <solution>
                <div class="detailed-solution">
                <p>Explanation</p>
                <p>Lansing is the capital of Michigan, although it is not Michigan's largest city, or even the seat of the county in which it resides.</p>
                </div>
                </solution>
            </problem>
        ''')

        children = XBlockFixtureDesc('chapter', 'Test Section').add_children(
            XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                XBlockFixtureDesc('vertical', 'Test Unit').add_children(
                    XBlockFixtureDesc('problem', 'text input problem', data=problem_data),
                    XBlockFixtureDesc('crowdsourcehinter', 'test crowdsourcehinter')
                )
            )
        )

        course_fix.add_children(children).install()

        # Auto-auth register for the course.
        AutoAuthPage(self.browser, username=self.USERNAME, email=self.EMAIL,
                     course_id=self.course_id, staff=False).visit()

    def _goto_csh_problem_page(self):
        """
        Visit the page courseware page containing the hinter
        """
        self.courseware_page.visit()
        csh_problem_page = CrowdsourcehinterProblemPage(self.browser)
        self.assertGreater(len(self.browser.find_elements_by_class_name('crowdsourcehinter_block')), 0)
        return csh_problem_page

    def test_student_hint_workflow(self):
        """
        Test the basic workflow of a student recieving hints. The student should submit an incorrect answer and
        receive a hint (in this case no hint since none are set), be able to rate that hint, see a different UX
        after submitting a correct answer, and be capable of contributing a new hint to the system.
        """
        csh_problem_page = self._goto_csh_problem_page()

        csh_problem_page.submit_text_answer("michigann")
        csh_problem_page.wait_for_ajax()
        self.assertEqual(csh_problem_page.get_hint_text()[0], u"Hint: Sorry, there are no hints for this answer.")

        self.assertGreater(len(self.browser.find_elements_by_class_name('csh_rate_hint')), 0)
        csh_problem_page.rate_hint()
        csh_problem_page.wait_for_ajax()

        csh_problem_page.submit_text_answer("michigan")
        csh_problem_page.wait_for_ajax()
        self.assertGreater(len(self.browser.find_elements_by_id('show_hint_rating_ux')), 0)

        csh_problem_page.submit_new_hint("new hint text")
