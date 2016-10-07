# -*- coding: utf-8 -*-
"""
Test for matlab problems
"""
from textwrap import dedent
import time

from flaky import flaky

from openedx.tests.acceptance.pages.lms.matlab_problem import MatlabProblemPage
from openedx.tests.acceptance.fixtures.course import XBlockFixtureDesc
from openedx.tests.acceptance.fixtures.xqueue import XQueueResponseFixture
from openedx.tests.acceptance.tests.lms.test_lms_problems import ProblemsTest


class MatlabProblemTest(ProblemsTest):
    """
    Tests that verify matlab problem "Run Code".
    """
    def get_problem(self):
        """
        Create a matlab problem for the test.
        """
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
        return XBlockFixtureDesc('problem', 'Test Matlab Problem', data=problem_data)

    def _goto_matlab_problem_page(self):
        """
        Open matlab problem page with assertion.
        """
        self.courseware_page.visit()
        matlab_problem_page = MatlabProblemPage(self.browser)
        self.assertEqual(matlab_problem_page.problem_name, 'Test Matlab Problem')
        return matlab_problem_page

    @flaky  # TNL-4132
    def test_run_code(self):
        """
        Test "Run Code" button functionality.
        """

        # Enter a submission, which will trigger a pre-defined response from the XQueue stub.
        self.submission = "a=1" + self.unique_id[0:5]  # pylint: disable=attribute-defined-outside-init

        self.xqueue_grade_response = {'msg': self.submission}

        matlab_problem_page = self._goto_matlab_problem_page()

        # Configure the XQueue stub's response for the text we will submit
        if self.xqueue_grade_response is not None:
            XQueueResponseFixture(self.submission, self.xqueue_grade_response).install()

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
            self.xqueue_grade_response.get("msg"),
            matlab_problem_page.get_grader_msg(".ungraded-matlab-result")[0]
        )
