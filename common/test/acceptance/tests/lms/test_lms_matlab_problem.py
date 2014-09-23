# -*- coding: utf-8 -*-
"""
End-to-end tests for the LMS.
"""
import time

from ..helpers import UniqueCourseTest
from ...pages.studio.auto_auth import AutoAuthPage
from ...pages.lms.courseware import CoursewarePage
from ...pages.lms.matlab_problem import MatlabProblemPage
from ...fixtures.course import CourseFixture, XBlockFixtureDesc
from ...fixtures.xqueue import XQueueResponseFixture
from textwrap import dedent


class MatlabProblemTest(UniqueCourseTest):
    """
    Tests that verify matlab problem "Run Code".
    """
    USERNAME = "STAFF_TESTER"
    EMAIL = "johndoe@example.com"

    def setUp(self):
        super(MatlabProblemTest, self).setUp()

        self.XQUEUE_GRADE_RESPONSE = None

        self.courseware_page = CoursewarePage(self.browser, self.course_id)

        # Install a course with sections/problems, tabs, updates, and handouts
        course_fix = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )

        problem_data = dedent("""
            <problem markdown="null">
                  <text>
                    <p>
                        Write MATLAB code to create the following row vector and store it in a variable named <code>V</code>.
                    </p>
                    <table id="a0000000466" class="equation" width="100%" cellspacing="0" cellpadding="7" style="table-layout:auto">
                      <tr>
                        <td class="equation">[1 1 2 3 5 8 13]</td>
                      </tr>
                    </table>
                    <p>
                      <coderesponse queuename="matlab">
                        <matlabinput rows="10" cols="40" mode="" tabsize="4">
                            <plot_payload>
                            </plot_payload>
                        </matlabinput>
                        <codeparam>
                          <initial_display/>
                            <answer_display>
                            </answer_display>
                            <grader_payload>
                            </grader_payload>
                        </codeparam>
                      </coderesponse>
                    </p>
                  </text>
            </problem>
        """)

        course_fix.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('problem', 'Test Matlab Problem', data=problem_data)
                )
            )
        ).install()

        # Auto-auth register for the course.
        AutoAuthPage(self.browser, username=self.USERNAME, email=self.EMAIL,
                     course_id=self.course_id, staff=False).visit()

    def _goto_matlab_problem_page(self):
        """
        Open matlab problem page with assertion.
        """
        self.courseware_page.visit()
        matlab_problem_page = MatlabProblemPage(self.browser)
        self.assertEqual(matlab_problem_page.problem_name, 'TEST MATLAB PROBLEM')
        return matlab_problem_page

    def test_run_code(self):
        """
        Test "Run Code" button functionality.
        """

        # Enter a submission, which will trigger a pre-defined response from the XQueue stub.
        self.submission = "a=1" + self.unique_id[0:5]

        self.XQUEUE_GRADE_RESPONSE = {'msg': self.submission}

        matlab_problem_page = self._goto_matlab_problem_page()

        # Configure the XQueue stub's response for the text we will submit
        if self.XQUEUE_GRADE_RESPONSE is not None:
            XQueueResponseFixture(self.submission, self.XQUEUE_GRADE_RESPONSE).install()

        matlab_problem_page.set_response(self.submission)
        matlab_problem_page.click_run_code()

        self.assertEqual(
            u'Submitted. As soon as a response is returned, this message will be replaced by that feedback.',
            matlab_problem_page.get_grader_msg(".external-grader-message")[0]
        )

        # Wait 5 seconds for xqueue stub server grader response sent back to lms.
        time.sleep(5)

        self.assertEqual(u'', matlab_problem_page.get_grader_msg(".external-grader-message")[0])
        self.assertEqual(
            self.XQUEUE_GRADE_RESPONSE.get("msg"),
            matlab_problem_page.get_grader_msg(".ungraded-matlab-result")[0]
        )
